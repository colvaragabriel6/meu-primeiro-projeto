import hashlib
import json
import re
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

# =========================================================
# CONFIG (AJUSTE SE QUISER)
# =========================================================

POSTS_FILE_PRIMARY = Path("data/posts_limpos.txt")
POSTS_FILE_FALLBACK = Path("data/posts.txt")

PDF_URLS_OUT = Path("data/pdf_urls.txt")        # gerado/atualizado automaticamente
INDEX_PATH = Path("data/pdf_index.jsonl")       # índice final (JSONL)
DOWNLOAD_ROOT = Path("downloads")               # pastas finais

HEADERS = {"User-Agent": "vibe-coding-learning-bot/0.9 (educational)"}

# crawler
CRAWL_MAX_DEPTH = 4
CRAWL_MAX_PAGES_PER_SEED = 40
CRAWL_SLEEP_S = 0.4

# download
DOWNLOAD_TIMEOUT = 60
DOWNLOAD_SLEEP_S = 0.4
MAX_BYTES = 80 * 1024 * 1024  # 80MB

# limite total de posts por execução (para teste; aumente depois)
MAX_POSTS_THIS_RUN = 30

# =========================================================
# REGEX
# =========================================================

PDF_RE = re.compile(r"\.pdf(\?|#|$)", re.IGNORECASE)
URL_PDF_RE = re.compile(
    r"https?://[^\s\"'<>]+\.pdf(?:\?[^\s\"'<>]*)?(?:#[^\s\"'<>]*)?",
    re.IGNORECASE,
)

# =========================================================
# UTILITÁRIOS
# =========================================================

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_filename(name: str) -> str:
    name = (name or "").strip()
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w\.\-]+", "_", name, flags=re.UNICODE)
    name = re.sub(r"_+", "_", name)
    return name

def year_from_url(pdf_url: str) -> str | None:
    path = urlparse(pdf_url).path
    parts = [p for p in path.split("/") if p]
    for p in parts:
        if re.fullmatch(r"\d{4}", p):
            return p
    return None

def basename_from_url(pdf_url: str) -> str:
    path = urlparse(pdf_url).path
    base = Path(path).name
    base = unquote(base)
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return safe_filename(base)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                out.append(s)
    return out

def append_unique_lines(path: Path, lines: list[str]) -> int:
    """
    Acrescenta linhas novas (sem duplicar).
    Retorna quantas foram adicionadas.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set(load_lines(path))
    new = [l for l in lines if l not in existing]
    if not new:
        return 0
    with path.open("a", encoding="utf-8") as f:
        for l in new:
            f.write(l + "\n")
    return len(new)

# =========================================================
# CLASSIFICAÇÃO (taxonomia final do Gabriel)
# =========================================================

@dataclass
class Classification:
    categoria: str
    ano: str | None

def classify_pdf(pdf_url: str) -> Classification:
    """
    Pastas finais:
      - Informativos_STF/<ano>/
      - Informativos_STJ/<ano>/
      - Revisoes/
      - Alteracoes_Legislativas/<ano>/   (inclui alterações + comentários/explicações de leis)
      - Materiais_Diversos/<ano>/
    """
    filename = basename_from_url(pdf_url).lower()
    url_lower = pdf_url.lower()
    ano = year_from_url(pdf_url)

    # 1) Informativos STF / STJ
    if "stf" in filename:
        return Classification("Informativos_STF", ano)
    if "stj" in filename:
        return Classification("Informativos_STJ", ano)

    # 2) Revisões
    if "revisao" in filename or "revisão" in filename or "promotor" in filename:
        return Classification("Revisoes", None)

    # 3) Alterações legislativas (inclui comentários/explicações)
    palavras_al = [
        "legisl", "novidades", "alteracao", "alteração",
        "lei", "leis", "comentad", "comentario", "comentário",
        "explic", "analise", "análise", "artigo"
    ]
    if any(p in filename for p in palavras_al) or "novidades%20legislativas" in url_lower:
        return Classification("Alteracoes_Legislativas", ano)

    # 4) Diversos
    return Classification("Materiais_Diversos", ano)

def build_destination_path(pdf_url: str) -> Path:
    cls = classify_pdf(pdf_url)
    filename = basename_from_url(pdf_url)

    if cls.categoria in ("Informativos_STF", "Informativos_STJ"):
        ano = cls.ano or "Sem_Ano"
        return DOWNLOAD_ROOT / cls.categoria / ano / filename

    if cls.categoria == "Alteracoes_Legislativas":
        ano = cls.ano or "Sem_Ano"
        return DOWNLOAD_ROOT / "Alteracoes_Legislativas" / ano / filename

    if cls.categoria == "Materiais_Diversos":
        ano = cls.ano or "Sem_Ano"
        return DOWNLOAD_ROOT / "Materiais_Diversos" / ano / filename

    # Revisoes (flat)
    return DOWNLOAD_ROOT / "Revisoes" / filename

# =========================================================
# CRAWLER (multi-camadas)
# =========================================================

def extrair_pdfs_e_links(pagina_url: str) -> tuple[list[str], list[str]]:
    """
    Retorna (pdfs, links_candidatos) para continuar o crawl.
    PDFs são extraídos por:
      (i) URLs de PDF no HTML bruto (regex)
      (ii) <a href="...">
    """
    resp = requests.get(pagina_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    pdfs: list[str] = []
    links: list[str] = []

    # PDFs por HTML bruto
    for u in URL_PDF_RE.findall(html):
        pdfs.append(u.strip())

    # PDFs e links por <a>
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        href = href.strip()
        if not href or href.startswith("javascript:") or href == "#":
            continue

        abs_href = urljoin(pagina_url, href).strip()

        if PDF_RE.search(abs_href):
            pdfs.append(abs_href)
            continue

        # candidatos: seguir páginas internas
        parsed = urlparse(abs_href)
        if parsed.scheme not in ("http", "https"):
            continue

        # seguir apenas dizerodireito.com.br (onde estão as páginas)
        if not parsed.netloc.endswith("dizerodireito.com.br"):
            continue

        # evitar expansão exagerada
        if "/search/" in parsed.path:
            continue

        links.append(abs_href)

    # dedup preservando ordem
    pdfs = list(dict.fromkeys([p for p in pdfs if p]))
    links = list(dict.fromkeys([l for l in links if l]))
    return pdfs, links

def crawl_pdfs(seed_url: str, max_depth: int, max_pages: int, sleep_s: float) -> list[str]:
    """
    BFS com profundidade controlada.
    Retorna PDFs encontrados a partir da seed.
    """
    visitados: set[str] = set()
    fila = deque([(seed_url, 0)])

    encontrados: list[str] = []

    while fila and len(visitados) < max_pages:
        url, depth = fila.popleft()
        if url in visitados:
            continue
        visitados.add(url)

        try:
            pdfs, links = extrair_pdfs_e_links(url)
        except Exception:
            # falha de rede/página: ignora
            continue

        for p in pdfs:
            if p not in encontrados:
                encontrados.append(p)

        if depth < max_depth:
            for lk in links:
                if lk not in visitados:
                    fila.append((lk, depth + 1))

        time.sleep(sleep_s)

    return encontrados

# =========================================================
# DOWNLOAD + ÍNDICE
# =========================================================

def load_existing_hashes(index_path: Path) -> set[str]:
    hashes = set()
    if not index_path.exists():
        return hashes
    with index_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                h = obj.get("sha256")
                if h:
                    hashes.add(h)
            except json.JSONDecodeError:
                continue
    return hashes

def download_pdf(pdf_url: str, dest: Path) -> tuple[int, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    with requests.get(pdf_url, headers=HEADERS, timeout=DOWNLOAD_TIMEOUT, stream=True) as r:
        r.raise_for_status()
        total = 0
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)
                total += len(chunk)
                if total > MAX_BYTES:
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError(f"Arquivo excedeu limite de {MAX_BYTES} bytes: {pdf_url}")

    h = sha256_file(tmp)
    tmp.replace(dest)
    return total, h

def download_and_index(pdf_urls: list[str]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)

    existing_hashes = load_existing_hashes(INDEX_PATH)

    for i, url in enumerate(pdf_urls, start=1):
        dest = build_destination_path(url)
        cls = classify_pdf(url)

        print(f"\n[PDF {i}/{len(pdf_urls)}] {url}")
        print(f"Categoria: {cls.categoria} | Ano: {cls.ano or 'Sem_Ano'}")
        print(f"Destino: {dest}")

        # se já existe fisicamente, hashear e registrar se precisar
        if dest.exists() and dest.stat().st_size > 0:
            h = sha256_file(dest)
            if h in existing_hashes:
                print("Já existe (hash conhecido). Pulando.")
                continue

            existing_hashes.add(h)
            registro = {
                "pdf_url": url,
                "categoria": cls.categoria,
                "ano": cls.ano,
                "local_path": str(dest),
                "size_bytes": dest.stat().st_size,
                "sha256": h,
                "status": "ja_existia",
                "timestamp_utc": iso_now(),
            }
            with INDEX_PATH.open("a", encoding="utf-8") as out:
                out.write(json.dumps(registro, ensure_ascii=False) + "\n")
            print("Indexado (arquivo já existia).")
            continue

        # baixar
        try:
            size, h = download_pdf(url, dest)
        except Exception as e:
            print("FALHA ao baixar:", e)
            registro = {
                "pdf_url": url,
                "categoria": cls.categoria,
                "ano": cls.ano,
                "local_path": str(dest),
                "status": "erro",
                "erro": str(e),
                "timestamp_utc": iso_now(),
            }
            with INDEX_PATH.open("a", encoding="utf-8") as out:
                out.write(json.dumps(registro, ensure_ascii=False) + "\n")
            time.sleep(DOWNLOAD_SLEEP_S)
            continue

        # dedup por hash
        if h in existing_hashes:
            dest.unlink(missing_ok=True)
            print("Duplicado por hash. Removido e ignorado.")
            continue

        existing_hashes.add(h)

        registro = {
            "pdf_url": url,
            "categoria": cls.categoria,
            "ano": cls.ano,
            "local_path": str(dest),
            "size_bytes": size,
            "sha256": h,
            "status": "baixado",
            "timestamp_utc": iso_now(),
        }
        with INDEX_PATH.open("a", encoding="utf-8") as out:
            out.write(json.dumps(registro, ensure_ascii=False) + "\n")

        print(f"OK. ({size} bytes) SHA-256: {h}")
        time.sleep(DOWNLOAD_SLEEP_S)

# =========================================================
# MAIN
# =========================================================

def main():
    posts_file = POSTS_FILE_PRIMARY if POSTS_FILE_PRIMARY.exists() else POSTS_FILE_FALLBACK
    if not posts_file.exists():
        print("ERRO: não encontrei nem data/posts_limpos.txt nem data/posts.txt.")
        print("Você precisa ter uma lista de posts (1 URL por linha).")
        return

    posts = load_lines(posts_file)
    if not posts:
        print(f"ERRO: {posts_file} está vazio.")
        return

    # para não explodir no início
    posts = posts[:MAX_POSTS_THIS_RUN]

    print("Arquivo de posts:", posts_file)
    print("Posts nesta execução:", len(posts))
    print(f"Crawl: depth={CRAWL_MAX_DEPTH}, pages/seed={CRAWL_MAX_PAGES_PER_SEED}")

    # coletar PDFs
    all_pdfs: list[str] = []
    for idx, seed in enumerate(posts, start=1):
        print(f"\n[POST {idx}/{len(posts)}] Seed:", seed)
        pdfs = crawl_pdfs(seed, CRAWL_MAX_DEPTH, CRAWL_MAX_PAGES_PER_SEED, CRAWL_SLEEP_S)

        # filtra só URLs .pdf de verdade
        pdfs = [p for p in pdfs if PDF_RE.search(p)]
        if pdfs:
            print(f"  PDFs encontrados: {len(pdfs)}")
        else:
            print("  PDFs encontrados: 0")

        for p in pdfs:
            if p not in all_pdfs:
                all_pdfs.append(p)

    print("\nTotal de PDFs únicos coletados:", len(all_pdfs))

    # gravar/atualizar pdf_urls.txt
    added = append_unique_lines(PDF_URLS_OUT, all_pdfs)
    print("PDF URLs adicionadas em data/pdf_urls.txt:", added)

    # baixar e indexar
    if all_pdfs:
        download_and_index(all_pdfs)

    print("\nConcluído.")
    print("Lista de PDFs:", PDF_URLS_OUT)
    print("Índice:", INDEX_PATH)
    print("Downloads em:", DOWNLOAD_ROOT)

if __name__ == "__main__":
    main()
