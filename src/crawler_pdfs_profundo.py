import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

# Detecta PDFs (mesmo com ?param ou #fragment)
PDF_RE = re.compile(r"\.pdf(\?|#|$)", re.IGNORECASE)

# Detecta URLs completas de PDF em qualquer lugar do HTML (texto/script/etc.)
URL_PDF_RE = re.compile(
    r"https?://[^\s\"'<>]+\.pdf(?:\?[^\s\"'<>]*)?(?:#[^\s\"'<>]*)?",
    re.IGNORECASE,
)

HEADERS = {"User-Agent": "vibe-coding-learning-bot/0.3 (educational)"}


def _normalizar(url: str) -> str:
    """Normaliza URL minimamente (remove espaços)."""
    return (url or "").strip()


def extrair_pdfs_e_links_candidatos(pagina_url: str) -> tuple[list[str], list[str]]:
    """
    Baixa uma página e retorna:
      - pdfs: PDFs encontrados (por href e por varredura do HTML)
      - links: links internos candidatos para continuar a busca
    """
    resp = requests.get(pagina_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    pdfs: list[str] = []
    links: list[str] = []

    # (A) PDFs por varredura do HTML bruto (pega até se não estiver em <a href>)
    for pdf_url in URL_PDF_RE.findall(html):
        pdfs.append(_normalizar(pdf_url))

    # (B) PDFs e links por <a href="...">
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue

        href = _normalizar(href)
        if not href or href.startswith("javascript:") or href == "#":
            continue

        abs_href = urljoin(pagina_url, href)
        abs_href = _normalizar(abs_href)

        # PDF?
        if PDF_RE.search(abs_href):
            pdfs.append(abs_href)
            continue

        # Candidato: mesma origem do dizerodireito.com.br (HTML)
        parsed = urlparse(abs_href)
        if parsed.scheme not in ("http", "https"):
            continue

        # Só seguir o domínio principal (não seguir dizerodireito.net aqui; lá é onde ficam os PDFs)
        if not parsed.netloc.endswith("dizerodireito.com.br"):
            continue

        # Evitar páginas de busca/label que explodem o grafo
        if "/search/" in parsed.path:
            continue

        # Heurística simples: priorizar URLs do ano e páginas com cara de conteúdo
        # (isso reduz exploração sem travar)
        url_lower = abs_href.lower()
        if "/2026/" in url_lower or "/2025/" in url_lower or "/2024/" in url_lower:
            links.append(abs_href)
        else:
            # ainda aceitamos algumas páginas internas úteis
            palavras = ["informativo", "edicao", "edição", "pdf", "baixar", "download", "resumido", "completo"]
            if any(p in url_lower for p in palavras):
                links.append(abs_href)

    # dedup preservando ordem
    pdfs = list(dict.fromkeys([p for p in pdfs if p]))
    links = list(dict.fromkeys([l for l in links if l]))

    return pdfs, links


def buscar_pdfs_profundo(
    seed_url: str,
    max_depth: int = 4,
    max_pages: int = 60,
    sleep_s: float = 1.0,
) -> list[str]:
    """
    Busca PDFs a partir de uma URL inicial, seguindo links internos até max_depth camadas,
    limitando o total de páginas visitadas (max_pages).
    Retorna todos os PDFs encontrados dentro desses limites.
    """
    seed_url = _normalizar(seed_url)

    visitados: set[str] = set()
    fila = deque([(seed_url, 0)])  # (url, depth)

    pdfs_encontrados: list[str] = []

    while fila and len(visitados) < max_pages:
        url, depth = fila.popleft()

        if url in visitados:
            continue
        visitados.add(url)

        print(f"Visitando (prof={depth}): {url}")

        try:
            pdfs, candidatos = extrair_pdfs_e_links_candidatos(url)
        except Exception as e:
            print(f"  ERRO ao acessar: {e}")
            continue

        # acumula PDFs encontrados
        if pdfs:
            novos = 0
            for p in pdfs:
                if p not in pdfs_encontrados:
                    pdfs_encontrados.append(p)
                    novos += 1
            if novos:
                print(f"  +{novos} PDF(s) encontrado(s) nesta página.")

        # enfileira candidatos (se ainda pode descer)
        if depth < max_depth:
            for link in candidatos:
                if link not in visitados:
                    fila.append((link, depth + 1))

        time.sleep(sleep_s)

    return pdfs_encontrados


if __name__ == "__main__":
    # Seed: use a página intermediária que você identificou
    seed = "https://www.dizerodireito.com.br/2026/02/informativo-comentado-28-edicao.html"

    pdfs = buscar_pdfs_profundo(seed, max_depth=4, max_pages=60, sleep_s=1.0)

    print("\nPDFs encontrados no total:")
    for p in pdfs:
        print("-", p)
