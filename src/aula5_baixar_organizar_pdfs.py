import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

# =========================
# CONFIGURAÇÕES
# =========================

INPUT_LIST = Path("data/pdf_urls.txt")          # lista de URLs (uma por linha)
INDEX_PATH = Path("data/pdf_index.jsonl")       # índice (JSONL)
DOWNLOAD_ROOT = Path("downloads")               # raiz das pastas organizadas

HEADERS = {
    "User-Agent": "vibe-coding-learning-bot/0.7 (educational)"
}

TIMEOUT = 60
SLEEP_S = 0.6  # respeitar o servidor
MAX_BYTES = 80 * 1024 * 1024  # 80 MB por PDF (limite de segurança)

# =========================
# UTILITÁRIOS
# =========================

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_filename(name: str) -> str:
    """
    Normaliza nome de arquivo para evitar caracteres problemáticos.
    Mantém letras, números, ponto, hífen e underscore.
    """
    name = name.strip()
    name = name.replace(" ", "_")
    name = re.sub(r"[^\w\.\-]+", "_", name, flags=re.UNICODE)
    name = re.sub(r"_+", "_", name)
    return name

def year_from_url(pdf_url: str) -> str | None:
    """
    Tenta extrair ano do caminho do URL.
    Ex.: .../uploads/2026/01/arquivo.pdf -> 2026
    """
    path = urlparse(pdf_url).path
    parts = [p for p in path.split("/") if p]
    for p in parts:
        if re.fullmatch(r"\d{4}", p):
            return p
    return None

def basename_from_url(pdf_url: str) -> str:
    path = urlparse(pdf_url).path
    base = Path(path).name
    base = unquote(base)  # decodifica %20 etc.
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return safe_filename(base)

@dataclass
class Classification:
    categoria: str
    ano: str | None

def classify_pdf(pdf_url: str) -> Classification:
    """
    Classificação objetiva por palavras-chave no nome do arquivo e/ou URL.

    Pastas finais:
      - Informativos_STF/<ano>/
      - Informativos_STJ/<ano>/
      - Revisoes/
      - Alteracoes_Legislativas/<ano>/
      - Materiais_Diversos/<ano>/
    """
    filename = basename_from_url(pdf_url).lower()
    url_lower = pdf_url.lower()
    ano = year_from_url(pdf_url)

    # 1) Informativos STF / STJ (por ano)
    # Critério principal: nome do arquivo (mais confiável)
    if "stf" in filename:
        return Classification(categoria="Informativos_STF", ano=ano)

    if "stj" in filename:
        return Classification(categoria="Informativos_STJ", ano=ano)

    # 2) Revisões (tudo junto)
    if "revisao" in filename or "revisão" in filename or "promotor" in filename:
        return Classification(categoria="Revisoes", ano=None)

    # 3) Alterações legislativas (inclui comentários/explicações de leis)
    # Entram aqui: novidades legislativas, alterações, comentários, explicações, leis comentadas, etc.
    palavras_al = [
        "legisl", "novidades", "alteracao", "alteração",
        "lei", "leis", "comentad", "comentário", "comentario",
        "explic", "analis", "análise", "artigo"
    ]
    if any(p in filename for p in palavras_al) or any(p in url_lower for palavras in ["novidades%20legislativas", "legisl"] for p in [palavras]):
        return Classification(categoria="Alteracoes_Legislativas", ano=ano)

    # 4) Materiais diversos (resto)
    return Classification(categoria="Materiais_Diversos", ano=ano)

def build_destination_path(pdf_url: str) -> Path:
    """
    Monta o caminho final do arquivo dentro de downloads/ conforme classificação.
    """
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

    # Revisoes é "flat"
    return DOWNLOAD_ROOT / "Revisoes" / filename

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
    """
    Baixa o PDF em streaming.
    Retorna (bytes_baixados, sha256).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp = dest.with_suffix(dest.suffix + ".part")

    with requests.get(pdf_url, headers=HEADERS, timeout=TIMEOUT, stream=True) as r:
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

def main():
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not INPUT_LIST.exists():
        print(f"ERRO: não encontrei {INPUT_LIST}.")
        print("Crie o arquivo data/pdf_urls.txt com 1 URL de PDF por linha.")
        return

    # Ler URLs
    pdf_urls = []
    with INPUT_LIST.open("r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            if url.lower().startswith("http"):
                pdf_urls.append(url)

    # dedup preservando ordem
    pdf_urls = list(dict.fromkeys(pdf_urls))

    print("Total de URLs de PDF para processar:", len(pdf_urls))

    # hashes já existentes
    existing_hashes = load_existing_hashes(INDEX_PATH)

    for i, pdf_url in enumerate(pdf_urls, start=1):
        dest = build_destination_path(pdf_url)
        cls = classify_pdf(pdf_url)

        print(f"\n[{i}/{len(pdf_urls)}] Baixando: {pdf_url}")
        print(f"Categoria: {cls.categoria} | Ano: {cls.ano or 'Sem_Ano'}")
        print(f"Destino: {dest}")

        # Se já existe, tenta hash e registra/evita duplicidade
        if dest.exists() and dest.stat().st_size > 0:
            h = sha256_file(dest)
            if h in existing_hashes:
                print("Já existe (mesmo hash). Pulando.")
                continue

            existing_hashes.add(h)
            registro = {
                "pdf_url": pdf_url,
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

        # Baixar
        try:
            size, h = download_pdf(pdf_url, dest)
        except Exception as e:
            print("FALHA ao baixar:", e)
            registro = {
                "pdf_url": pdf_url,
                "categoria": cls.categoria,
                "ano": cls.ano,
                "local_path": str(dest),
                "status": "erro",
                "erro": str(e),
                "timestamp_utc": iso_now(),
            }
            with INDEX_PATH.open("a", encoding="utf-8") as out:
                out.write(json.dumps(registro, ensure_ascii=False) + "\n")
            time.sleep(SLEEP_S)
            continue

        # Dedup por hash
        if h in existing_hashes:
            try:
                dest.unlink(missing_ok=True)
            except Exception:
                pass
            print("Duplicado por hash. Removido e ignorado.")
            continue

        existing_hashes.add(h)

        registro = {
            "pdf_url": pdf_url,
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
        time.sleep(SLEEP_S)

    print("\nConcluído.")
    print("Índice:", INDEX_PATH)
    print("Downloads em:", DOWNLOAD_ROOT)

if __name__ == "__main__":
    main()
