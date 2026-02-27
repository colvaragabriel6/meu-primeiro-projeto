#!/usr/bin/env python3
"""
Script para verificar cobertura de informativos 2024-2025
Análise local com confirmação no site
"""

import re
from pathlib import Path
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import time

DOWNLOADS_DIR = Path("downloads")

def analisar_locais():
    """Analisa informativos localmente"""
    
    informativos = {
        'stf': defaultdict(list),
        'stj': defaultdict(list)
    }
    
    # STF
    stf_folder = DOWNLOADS_DIR / "Informativos_STF"
    if stf_folder.exists():
        for file in stf_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+).*stf", file.name, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                informativos['stf'][num].append(file.name)
    
    # STJ
    stj_folder = DOWNLOADS_DIR / "Informativos_STJ"
    if stj_folder.exists():
        for file in stj_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+).*stj", file.name, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                informativos['stj'][num].append(file.name)
    
    return informativos

def buscar_site():
    """Busca informativos no site"""
    
    resultados = {
        'stf': {'2024': [], '2025': []},
        'stj': {'2024': [], '2025': []}
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        # STF 2024
        print("🔍 Buscando STF 2024...")
        resp = requests.get(
            "https://www.dizerodireito.com.br/search/label/informativo%20comentado%20stf-2024",
            headers=headers,
            timeout=20
        )
        resp.raise_for_status()
        matches = re.findall(r"info-(\d+)-stf", resp.text, re.IGNORECASE)
        resultados['stf']['2024'] = sorted(list(set([int(m) for m in matches])))
        print(f"   Encontrado: {len(resultados['stf']['2024'])} informativos")
        
        # STF 2025
        print("🔍 Buscando STF 2025...")
        time.sleep(1)
        resp = requests.get(
            "https://www.dizerodireito.com.br/search/label/informativo%20comentado%20stf-2025",
            headers=headers,
            timeout=20
        )
        resp.raise_for_status()
        matches = re.findall(r"info-(\d+)-stf", resp.text, re.IGNORECASE)
        resultados['stf']['2025'] = sorted(list(set([int(m) for m in matches])))
        print(f"   Encontrado: {len(resultados['stf']['2025'])} informativos")
        
        # STJ 2024
        print("🔍 Buscando STJ 2024...")
        time.sleep(1)
        resp = requests.get(
            "https://www.dizerodireito.com.br/search/label/informativo%20comentado%20stj-2024",
            headers=headers,
            timeout=20
        )
        resp.raise_for_status()
        matches = re.findall(r"info-(\d+)-stj", resp.text, re.IGNORECASE)
        resultados['stj']['2024'] = sorted(list(set([int(m) for m in matches])))
        print(f"   Encontrado: {len(resultados['stj']['2024'])} informativos")
        
        # STJ 2025
        print("🔍 Buscando STJ 2025...")
        time.sleep(1)
        resp = requests.get(
            "https://www.dizerodireito.com.br/search/label/informativo%20comentado%20stj-2025",
            headers=headers,
            timeout=20
        )
        resp.raise_for_status()
        matches = re.findall(r"info-(\d+)-stj", resp.text, re.IGNORECASE)
        resultados['stj']['2025'] = sorted(list(set([int(m) for m in matches])))
        print(f"   Encontrado: {len(resultados['stj']['2025'])} informativos")
        
    except Exception as e:
        print(f"   ❌ Erro ao buscar site: {e}")
    
    return resultados

def main():
    print("\n" + "="*80)
    print("📊 VERIFICAÇÃO DE COBERTURA DE INFORMATIVOS 2024-2025")
    print("="*80 + "\n")
    
    # Análise local
    print("📁 Analisando arquivos locais...")
    locais = analisar_locais()
    
    stf_nums = sorted(locais['stf'].keys())
    stj_nums = sorted(locais['stj'].keys())
    
    print(f"\n✅ Informativos baixados localmente:")
    print(f"   STF: {len(stf_nums)} informativos (info-{min(stf_nums) if stf_nums else 'N/A'} a info-{max(stf_nums) if stf_nums else 'N/A'})")
    print(f"   STJ: {len(stj_nums)} informativos (info-{min(stj_nums) if stj_nums else 'N/A'} a info-{max(stj_nums) if stj_nums else 'N/A'})")
    
    # Busca no site
    print("\n🌐 Buscando no site...")
    site = buscar_site()
    
    # Comparação
    print("\n" + "="*80)
    print("📈 COMPARAÇÃO: SITE vs LOCAL")
    print("="*80 + "\n")
    
    for ano in ['2024', '2025']:
        print(f"\n🗓️ ANO {ano}:\n")
        
        # STF
        site_stf = site['stf'][ano]
        local_stf = [n for n in stf_nums if n >= 1100]  # Aproximação
        
        print(f"   STF:")
        print(f"      Site:  {len(site_stf)} informativos", end="")
        if site_stf:
            print(f" (info-{min(site_stf)} a info-{max(site_stf)})")
        else:
            print()
        
        print(f"      Local: {len(local_stf)} relativos a este período")
        if site_stf:
            faltando_stf = set(site_stf) - set(local_stf)
            if faltando_stf:
                print(f"      ⚠️  FALTANDO: {len(faltando_stf)} informativos")
                print(f"         Números: {sorted(list(faltando_stf))[:10]}")
            else:
                print(f"      ✅ 100% de cobertura")
        
        # STJ
        site_stj = site['stj'][ano]
        local_stj = [n for n in stj_nums if n >= 800]  # Aproximação
        
        print(f"\n   STJ:")
        print(f"      Site:  {len(site_stj)} informativos", end="")
        if site_stj:
            print(f" (info-{min(site_stj)} a info-{max(site_stj)})")
        else:
            print()
        
        print(f"      Local: {len(local_stj)} relativos a este período")
        if site_stj:
            faltando_stj = set(site_stj) - set(local_stj)
            if faltando_stj:
                print(f"      ⚠️  FALTANDO: {len(faltando_stj)} informativos")
                print(f"         Números: {sorted(list(faltando_stj))[:10]}")
            else:
                print(f"      ✅ 100% de cobertura")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
