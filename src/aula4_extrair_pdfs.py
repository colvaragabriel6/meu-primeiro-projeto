import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PDF_RE = re.compile(r"\.pdf(\?|#|$)", re.IGNORECASE)

HEADERS = {
    "User-Agent": "vibe-coding-learning-bot/0.1 (educational)"
}

def extrair_pdfs_de_url(pagina_url: str) -> list[str]:
    """Baixa uma página HTML e retorna todos os links que parecem PDF."""
    resp = requests.get(pagina_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()  # levanta erro se status HTTP for ruim
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    pdfs = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue

        href = href.strip()
        if href.startswith("javascript:") or href == "#":
            continue

        # transforma links relativos em absolutos
        abs_href = urljoin(pagina_url, href)

        if PDF_RE.search(abs_href):
            pdfs.append(abs_href)

    # remove duplicados preservando ordem
    pdfs = list(dict.fromkeys(pdfs))
    return pdfs

def extrair_links_internos(pagina_url: str) -> list[str]:
    """Baixa uma página e retorna links internos (candidatos para 'camadas' seguintes)."""
    resp = requests.get(pagina_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        href = href.strip()
        if href.startswith("javascript:") or href == "#":
            continue

        abs_href = urljoin(pagina_url, href)

        # heurísticas: só links do próprio site e que pareçam páginas de conteúdo
        if abs_href.startswith("https://www.dizerodireito.com.br/") and "/2026/" in abs_href:
            links.append(abs_href)

    links = list(dict.fromkeys(links))
    return links

if __name__ == "__main__":
    # Use exatamente as páginas que você citou para testar com certeza
    pagina_principal = "https://www.dizerodireito.com.br/2026/02/informativo-comentado-28-edicao.html"

    print("Camada 1 — tentando achar PDFs direto na página principal:")
    pdfs = extrair_pdfs_de_url(pagina_principal)
    for p in pdfs:
        print("-", p)

    if not pdfs:
        print("\nNenhum PDF na camada 1. Camada 2 — seguindo links internos candidatos...")
        candidatos = extrair_links_internos(pagina_principal)

        # limite de candidatos para não varrer demais
        candidatos = candidatos[:20]

        for i, link in enumerate(candidatos, start=1):
            print(f"[{i}/{len(candidatos)}] Entrando em:", link)
            time.sleep(1)  # educado com o site
            pdfs2 = extrair_pdfs_de_url(link)

            if pdfs2:
                print("PDFs encontrados nessa camada:")
                for p in pdfs2:
                    print("-", p)
                break
        else:
            print("Não encontrei PDFs nem na camada 2.")
