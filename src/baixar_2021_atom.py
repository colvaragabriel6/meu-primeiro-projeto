#!/usr/bin/env python3
"""
Download informativos de 2021 extraindo links direto do feed Atom
"""
import os
import re
import requests
from pathlib import Path
from urllib.parse import urljoin

BASE_DIR = Path(__file__).parent.parent
DOWNLOADS = BASE_DIR / "downloads"
STF_DIR = DOWNLOADS / "Informativos_STF"
STJ_DIR = DOWNLOADS / "Informativos_STJ"

# Criar diretórios se não existirem
STF_DIR.mkdir(parents=True, exist_ok=True)
STJ_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def baixar_infos_2021(tribunal, ano):
    """Baixa informativos de 2021 extraindo links do feed"""
    
    dir_saida = STF_DIR if tribunal == "stf" else STJ_DIR
    total_baixados = 0
    total_pulados = 0
    
    url_feed = f"https://www.dizerodireito.com.br/feeds/posts/default/-/informativo%20comentado%20{tribunal}-{ano}?max-results=100"
    
    print(f"\n📥 Buscando informativos {tribunal.upper()} {ano}...")
    resp_feed = requests.get(url_feed, headers=HEADERS, timeout=10)
    
    # Extrair todos os links alternados que apontam para posts
    post_links = re.findall(
        rf'<link rel=["\']alternate["\'][^>]*href=["\']([^\'"]*informativo-comentado-\d+-{tribunal}[^\'"]*)["\']',
        resp_feed.text,
        re.IGNORECASE
    )
    
    print(f"Encontrados {len(post_links)} posts")
    
    # Extrair números e remover duplicatas
    nums_dict = {}
    for link in post_links:
        match = re.search(rf'informativo-comentado-(\d+)-{tribunal}', link, re.IGNORECASE)
        if match:
            num = int(match.group(1))
            if num not in nums_dict:
                nums_dict[num] = link
    
    nums_sorted = sorted(nums_dict.keys())
    print(f"Informativos únicos: {len(nums_sorted)} (info-{min(nums_sorted)}-{tribunal} até info-{max(nums_sorted)}-{tribunal})\n")
    
    for num in nums_sorted:
        post_url = nums_dict[num]
        
        try:
            resp_post = requests.get(post_url, headers=HEADERS, timeout=10)
            
            # Procurar PDFs no conteúdo do post
            pdf_links = re.findall(r'href=["\'](https?://[^\'"]+\.pdf[^\'"]*)["\']', resp_post.text, re.IGNORECASE)
            
            if not pdf_links:
                print(f"  ✗ info-{num}-{tribunal}: sem PDFs")
                continue
            
            # Baixar cada PDF
            sucesso = False
            for pdf_url in pdf_links:
                try:
                    resp_pdf = requests.get(pdf_url, headers=HEADERS, timeout=15)
                    resp_pdf.raise_for_status()
                    
                    # Determinar nome do arquivo
                    if 'resumido' in pdf_url.lower():
                        filename = f"info-{num}-{tribunal}-resumido.pdf"
                    else:
                        filename = f"info-{num}-{tribunal}.pdf"
                    
                    filepath = dir_saida / filename
                    
                    if filepath.exists():
                        total_pulados += 1
                    else:
                        filepath.write_bytes(resp_pdf.content)
                        total_baixados += 1
                        sucesso = True
                    
                except Exception as e:
                    pass
            
            if sucesso:
                print(f"  ✓ info-{num}-{tribunal}")
        
        except Exception as e:
            print(f"  ✗ info-{num}-{tribunal}: {str(e)[:30]}")
    
    return total_baixados, total_pulados

if __name__ == "__main__":
    print("=" * 60)
    print("📥 BAIXADOR DE INFORMATIVOS DE 2021")
    print("=" * 60)
    
    stf_baixados, stf_pulados = baixar_infos_2021("stf", 2021)
    stj_baixados, stj_pulados = baixar_infos_2021("stj", 2021)
    
    print("\n" + "=" * 60)
    print("✅ RESUMO")
    print("=" * 60)
    print(f"STF 2021: {stf_baixados} novo(s), {stf_pulados} existente(s)")
    print(f"STJ 2021: {stj_baixados} novo(s), {stj_pulados} existente(s)")
    total_novo = stf_baixados + stj_baixados
    total_exist = stf_pulados + stj_pulados
    print(f"TOTAL: {total_novo} novo(s), {total_exist} existente(s)")
