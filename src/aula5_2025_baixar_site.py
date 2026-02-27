import os
import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


# ==========================
# CONFIG
# ==========================
SEEDS = [
    "https://www.dizerodireito.com.br/2025/",      # arquivo do ano (ponto de partida)
]

TARGET_YEAR = "2025"

ALLOWED_HOSTS = {
    "www.dizerodireito.com.br",
    "dizerodireito.com.br",
    "dizerodireito.net",  # onde frequentemente ficam os PDFs (wp-content/uploads)
}

# Limites para não “explodir” o crawl
MAX_PAGES = 1200          # quantas páginas HTML no máximo vamos visitar
MAX_DEPTH = 5             # “camadas” máximas a partir dos seeds
SLEEP_SECONDS = 0.8       # atraso entre requisições (raspagem responsável)

DOWNLOADS_DIR = Path("downloads")
DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / f"crawl_state_{TARGET_YEAR}.json"

USER_AGENT = "Mozilla/5.0 (compatible; JurisRAGBot/1.0; +educational)"

PDF_RE = re.compile(r"\.pdf(\?.*)?$", re.IGNORECASE)
YEAR_PATH_RE = re.compile(rf"/{TARGET_YEAR}/")  # garante que pegamos conteúdo de 2025 no blog

# Heurísticas de classificação
STJ_RE = re.compile(r"\bstj\b", re.IGNORECASE)
STF_RE = re.compile(r"\bstf\b", re.IGNORECASE)
INFORMATIVO_RE = re.compile(r"\binformativo\b", re.IGNORECASE)
REVISAO_RE = re.compile(r"\brevis[aã]o\b", re.IGNORECASE)
ALTER_RE = re.compile(r"\b(lei|altera|alteraç|legisla)\b", re.IGNORECASE)


# ==========================
# UTILS
# ==========================
def ensure_dirs():
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def norm_url(u: str) -> str:
    # remove fragment
    u = u.strip()
    if not u:
        return u
    parsed = urlparse(u)
    return parsed._replace(fragment="").geturl()


def is_allowed(u: str) -> bool:
    try:
        host = urlparse(u).netloc.lower()
        return host in ALLOWED_HOSTS
    except Exception:
        return False


def is_html_candidate(u: str) -> bool:
    # Só vamos “entrar” em páginas de 2025 do blog (para não varrer o site inteiro)
    if not is_allowed(u):
        return False
    if PDF_RE.search(u):
        return False
    # aceita /2025/ (arquivo do ano, posts e meses)
    return bool(YEAR_PATH_RE.search(urlparse(u).path))


def guess_category(filename: str, context_text: str) -> str:
    """
    Retorna uma das chaves:
    Informativos_STJ, Informativos_STF, Revisoes, Alteracoes_Legislativas, Materiais_Diversos
    """
    text = (filename + " " + context_text).lower()

    if INFORMATIVO_RE.search(text) and STJ_RE.search(text):
        return "Informativos_STJ"
    if INFORMATIVO_RE.search(text) and STF_RE.search(text):
        return "Informativos_STF"
    if REVISAO_RE.search(text):
        return "Revisoes"
    if ALTER_RE.search(text) and ("lei" in text or "legis" in text or "altera" in text):
        return "Alteracoes_Legislativas"

    # fallback
    return "Materiais_Diversos"


def extract_year_from_anywhere(u: str, filename: str, context_text: str) -> str:
    # tenta 4 dígitos no caminho/nome/texto
    for s in (u, filename, context_text):
        m = re.search(r"(19|20)\d{2}", s)
        if m:
            return m.group(0)
    return TARGET_YEAR


def make_dest_path(category: str, year: str, filename: str) -> Path:
    if category in ("Informativos_STJ", "Informativos_STF"):
        return DOWNLOADS_DIR / category / year / filename
    else:
        return DOWNLOADS_DIR / category / filename


def safe_filename_from_url(u: str) -> str:
    path = urlparse(u).path
    name = os.path.basename(path) or f"arquivo_{sha1(u)[:10]}.pdf"
    # sanitiza
    name = re.sub(r"[^\w\-.]+", "-", name, flags=re.UNICODE).strip("-")
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def http_get(session: requests.Session, url: str) -> requests.Response:
    time.sleep(SLEEP_SECONDS)
    resp = session.get(url, timeout=30, allow_redirects=True)
    resp.raise_for_status()
    return resp


def download_pdf(session: requests.Session, pdf_url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)

    # se já existe e parece ok, pula
    if dest.exists() and dest.stat().st_size > 10_000:
        return False

    time.sleep(SLEEP_SECONDS)
    with session.get(pdf_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
        tmp.replace(dest)
    return True


def parse_links(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    # Links normais
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        abs_url = norm_url(urljoin(base_url, href))
        text = (a.get_text(" ", strip=True) or "")[:500]
        links.append((abs_url, text))

    # Também tenta imagens clicáveis que às vezes escondem o link no <a>
    # (No blog do Dizer o Direito, os botões de download às vezes são imagem dentro de <a>)
    return links


# ==========================
# MAIN CRAWLER
# ==========================
def main():
    ensure_dirs()

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    visited = set()
    queue = [(u, 0) for u in SEEDS]

    pdf_found = 0
    pdf_downloaded = 0
    pages_visited = 0

    while queue and pages_visited < MAX_PAGES:
        url, depth = queue.pop(0)
        url = norm_url(url)

        if not url or url in visited:
            continue
        visited.add(url)

        if not is_html_candidate(url):
            continue

        try:
            resp = http_get(session, url)
        except Exception as e:
            print(f"[ERRO] GET {url} -> {e}")
            continue

        pages_visited += 1
        ct = resp.headers.get("Content-Type", "")
        if "text/html" not in ct:
            continue

        html = resp.text
        links = parse_links(html, url)

        # Contexto textual da página (para ajudar classificação)
        page_text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        page_text = re.sub(r"\s+", " ", page_text)[:2000]

        for link_url, link_text in links:
            if not link_url:
                continue

            # PDFs (podem estar no dizerodireito.net ou até outros domínios; aqui vamos baixar apenas domínios permitidos)
            if PDF_RE.search(link_url) and is_allowed(link_url):
                pdf_found += 1
                filename = safe_filename_from_url(link_url)
                category = guess_category(filename, page_text + " " + link_text)
                year = extract_year_from_anywhere(link_url, filename, page_text + " " + link_text)
                dest = make_dest_path(category, year, filename)

                try:
                    did = download_pdf(session, link_url, dest)
                    if did:
                        pdf_downloaded += 1
                        print(f"[PDF] baixado: {dest}")
                    else:
                        print(f"[PDF] já existe: {dest}")
                except Exception as e:
                    print(f"[ERRO] baixar PDF {link_url} -> {e}")
                continue

            # HTML: só segue se ainda tem “profundidade”
            if depth < MAX_DEPTH and is_html_candidate(link_url):
                queue.append((link_url, depth + 1))

        if pages_visited % 25 == 0:
            print(f"\n[STATUS] páginas={pages_visited} | pdf_encontrados={pdf_found} | pdf_baixados={pdf_downloaded} | fila={len(queue)}\n")

    print("\n===== RESUMO =====")
    print("Páginas visitadas:", pages_visited)
    print("PDFs encontrados:", pdf_found)
    print("PDFs baixados:", pdf_downloaded)
    print("Pasta de saída:", DOWNLOADS_DIR)


if __name__ == "__main__":
    main()
