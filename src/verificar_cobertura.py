#!/usr/bin/env python3
"""
Script para verificar se todos os informativos de 2024 e 2025 foram raspados
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
from urllib.parse import urljoin
import time

USER_AGENT = "Mozilla/5.0 (compatible; JurisRAGBot/1.0; +educational)"
DOWNLOADS_DIR = Path("downloads")

# Padrões para identificar informativos
INFORMATIVO_PATTERN = re.compile(r"info-(\d+)-(stj|stf)", re.IGNORECASE)


def get_informativos_from_site(year: str) -> dict:
    """Busca lista de informativos no site para um ano específico"""
    
    url = f"https://www.dizerodireito.com.br/{year}/"
    
    print(f"🌐 Acessando {url}...")
    
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        time.sleep(1)
        
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        informativos = {}
        
        # Procura todos os links com padrão de informativo
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()
            text = link.get_text(" ", strip=True).lower()
            
            # Procura por padrões de informativo
            if "informativo" in text.lower() or "info-" in href.lower():
                match = INFORMATIVO_PATTERN.search(href)
                if match:
                    num, tribunal = match.groups()
                    key = f"{tribunal.upper()}-{num}"
                    if key not in informativos:
                        informativos[key] = {
                            "url": href,
                            "title": text[:100]
                        }
        
        return informativos
    
    except Exception as e:
        print(f"❌ Erro ao acessar {url}: {e}")
        return {}


def get_informativos_locais() -> dict:
    """Coleta informativos locais"""
    
    informativos = {}
    
    # STJ
    stj_folder = DOWNLOADS_DIR / "Informativos_STJ"
    if stj_folder.exists():
        for file in stj_folder.glob("*.pdf"):
            match = INFORMATIVO_PATTERN.search(file.name)
            if match:
                num, tribunal = match.groups()
                key = f"{tribunal.upper()}-{num}"
                informativos[key] = file.name
    
    # STF
    stf_folder = DOWNLOADS_DIR / "Informativos_STF"
    if stf_folder.exists():
        for file in stf_folder.glob("*.pdf"):
            match = INFORMATIVO_PATTERN.search(file.name)
            if match:
                num, tribunal = match.groups()
                key = f"{tribunal.upper()}-{num}"
                informativos[key] = file.name
    
    return informativos


def verificar_cobertura():
    """Verifica cobertura de informativos para 2024 e 2025"""
    
    print("\n" + "="*70)
    print("📊 VERIFICAÇÃO DE COBERTURA DE INFORMATIVOS")
    print("="*70)
    
    for year in ["2024", "2025"]:
        print(f"\n{'─'*70}")
        print(f"\n📅 ANO {year}")
        print(f"{'─'*70}\n")
        
        # Busca no site
        site_informativos = get_informativos_from_site(year)
        print(f"✓ Site tem {len(site_informativos)} informativos úicos encontrados")
        
        # Busca localmente
        local_informativos = get_informativos_locais()
        local_year = {k: v for k, v in local_informativos.items() if year in v}
        
        print(f"✓ Temos {len(local_year)} informativos locais\n")
        
        # Análise por tribunal
        stj_site = {k: v for k, v in site_informativos.items() if k.startswith("STJ")}
        stf_site = {k: v for k, v in site_informativos.items() if k.startswith("STF")}
        
        stj_local = {k: v for k, v in local_year.items() if k.startswith("STJ")}
        stf_local = {k: v for k, v in local_year.items() if k.startswith("STF")}
        
        print(f"STJ (Site):  {len(stj_site):<4} | STJ (Local):  {len(stj_local):<4} | {'✅' if len(stj_site) == len(stj_local) else '⚠️  DIFERENÇA'}")
        print(f"STF (Site):  {len(stf_site):<4} | STF (Local):  {len(stf_local):<4} | {'✅' if len(stf_site) == len(stf_local) else '⚠️  DIFERENÇA'}")
        
        # Faltando
        print("\n📍 Análise detalhada:")
        
        # STJ faltando
        stj_faltando = set(stj_site.keys()) - set(stj_local.keys())
        if stj_faltando:
            print(f"\n  ❌ STJ faltando ({len(stj_faltando)}):")
            for key in sorted(stj_faltando):
                print(f"     • {key}")
        else:
            print(f"\n  ✅ Todos os informativos STJ foram coletados")
        
        # STF faltando
        stf_faltando = set(stf_site.keys()) - set(stf_local.keys())
        if stf_faltando:
            print(f"\n  ❌ STF faltando ({len(stf_faltando)}):")
            for key in sorted(stf_faltando):
                print(f"     • {key}")
        else:
            print(f"\n  ✅ Todos os informativos STF foram coletados")
        
        # Resumo
        total_faltando = len(stj_faltando) + len(stf_faltando)
        total_site = len(stj_site) + len(stf_site)
        total_local = len(stj_local) + len(stf_local)
        
        print(f"\n  📊 Resumo {year}:")
        print(f"     Total no site: {total_site}")
        print(f"     Total local:   {total_local}")
        print(f"     Taxa cobertura: {(total_local/total_site*100 if total_site > 0 else 0):.1f}%")
        
        if total_faltando > 0:
            print(f"     ⚠️  {total_faltando} arquivo(s) faltando")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    verificar_cobertura()
