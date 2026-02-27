#!/usr/bin/env python3
"""
Script para verificar cobertura comparando com o site usando busca mais agressiva
"""

import requests
import re
from bs4 import BeautifulSoup
from pathlib import Path
import time

DOWNLOADS_DIR = Path("downloads")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def buscar_informativos_no_site(year: str) -> dict:
    """Busca informativos no arquivo do ano usando múltiplas estratégias"""
    
    print(f"\n🔍 Buscando informativos de {year} no site...")
    
    base_url = f"https://www.dizerodireito.com.br/{year}/"
    informativos = {}
    
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        time.sleep(1)
        
        # Primeira estratégia: acessar a página do ano
        print(f"   → Acessando {base_url}")
        resp = session.get(base_url, timeout=30)
        resp.raise_for_status()
        
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Procura padrões no HTML bruto
        pattern_info = re.compile(r"info-(\d+)-(stj|stf)", re.IGNORECASE)
        
        for match in pattern_info.finditer(html):
            num, tribunal = match.groups()
            key = f"{tribunal.upper()}-{num}"
            informativos[key] = f"info-{num}-{tribunal.lower()}.pdf"
        
        print(f"   ✓ Encontrado via regex: {len(informativos)} informativos")
        
        # Segunda estratégia: buscar todos os links
        links_html = soup.find_all("a", href=True)
        for link in links_html:
            href = link.get("href", "")
            match = pattern_info.search(href)
            if match:
                num, tribunal = match.groups()
                key = f"{tribunal.upper()}-{num}"
                if key not in informativos:
                    informativos[key] = href
        
        print(f"   ✓ Total única encontrado: {len(informativos)} informativos")
        
        return informativos
    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return {}


def obter_informativos_locais() -> dict:
    """Obtém informativos já baixados"""
    
    informativos = {}
    
    # STJ
    stj_folder = DOWNLOADS_DIR / "Informativos_STJ"
    if stj_folder.exists():
        for file in stj_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+)-(stj|stf)", file.name, re.IGNORECASE)
            if match:
                num, tribunal = match.groups()
                key = f"{tribunal.upper()}-{num}"
                informativos[key] = file.name
    
    # STF
    stf_folder = DOWNLOADS_DIR / "Informativos_STF"
    if stf_folder.exists():
        for file in stf_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+)-(stj|stf)", file.name, re.IGNORECASE)
            if match:
                num, tribunal = match.groups()
                key = f"{tribunal.upper()}-{num}"
                informativos[key] = file.name
    
    return informativos


def comparar_cobertura(year: str):
    """Compara cobertura entre site e local"""
    
    print(f"\n{'='*70}")
    print(f"VERIFICAÇÃO DE COBERTURA - ANO {year}")
    print(f"{'='*70}\n")
    
    # Busca no site
    site_inf = buscar_informativos_no_site(year)
    
    # Busca local
    local_inf = obter_informativos_locais()
    
    # Filtra informativos de 2024 e 2025 (pelo nome do arquivo que às vezes tem ano)
    local_year = local_inf  # Temos de 2024 e 2025 misturados
    
    # Separa por tribunal
    site_stj = {k: v for k, v in site_inf.items() if k.startswith("STJ")}
    site_stf = {k: v for k, v in site_inf.items() if k.startswith("STF")}
    
    local_stj = {k: v for k, v in local_inf.items() if k.startswith("STJ")}
    local_stf = {k: v for k, v in local_inf.items() if k.startswith("STF")}
    
    print(f"📊 Resumo {year}:")
    print(f"   Site STJ:  {len(site_stj):<4} | Local STJ:  {len(local_stj):<4}", end="")
    print(f" | {'✅ OK' if len(site_stj) == len(local_stj) else '⚠️  DIFERENÇA'}")
    
    print(f"   Site STF:  {len(site_stf):<4} | Local STF:  {len(local_stf):<4}", end="")
    print(f" | {'✅ OK' if len(site_stf) == len(local_stf) else '⚠️  DIFERENÇA'}")
    
    # Análise de cobertura
    stj_faltando = set(site_stj.keys()) - set(local_stj.keys())
    stf_faltando = set(site_stf.keys()) - set(local_stf.keys())
    
    print(f"\n📍 Análise detalhada:\n")
    
    if stj_faltando:
        print(f"   ❌ STJ faltando ({len(stj_faltando)}):")
        for key in sorted(stj_faltando)[:10]:
            print(f"      • {key}")
        if len(stj_faltando) > 10:
            print(f"      ... e mais {len(stj_faltando) - 10}")
    else:
        print(f"   ✅ STJ: 100% de cobertura")
    
    if stf_faltando:
        print(f"\n   ❌ STF faltando ({len(stf_faltando)}):")
        for key in sorted(stf_faltando)[:10]:
            print(f"      • {key}")
        if len(stf_faltando) > 10:
            print(f"      ... e mais {len(stf_faltando) - 10}")
    else:
        print(f"\n   ✅ STF: 100% de cobertura")
    
    # Taxa geral
    total_site = len(site_stj) + len(site_stf)
    total_local = len(local_stj) + len(local_stf)
    taxa = (total_local / total_site * 100) if total_site > 0 else 0
    
    print(f"\n📈 Taxa geral de cobertura:")
    print(f"   Site: {total_site} | Local: {total_local} | Cobertura: {taxa:.1f}%")
    
    if taxa < 100:
        print(f"\n   ⚠️  Faltam {int(total_site - total_local)} informativos")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔎 VERIFICAÇÃO DE COBERTURA DE INFORMATIVOS")
    print("="*70)
    
    comparar_cobertura("2024")
    comparar_cobertura("2025")
