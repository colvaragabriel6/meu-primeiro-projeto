#!/usr/bin/env python3
"""
Script para baixar informativos de 2023 e materiais da pasta OUTROS
"""

import requests
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup

DOWNLOADS_DIR = Path("downloads")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def obter_urls_informativos(tribunal, numero):
    """Obtém URLs de download para um informativo específico"""
    
    try:
        # Acessar a página de tags do ano
        url_tags = f"https://www.dizerodireito.com.br/search/label/informativo%20comentado%20{tribunal}-2023"
        resp = requests.get(url_tags, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        
        # Procurar pelo link do post HTML
        pattern = rf"href='([^']*informativo[^']*{numero}[^']*\.html[^']*)'|href='([^']*{numero}[^']*informativo[^']*\.html[^']*)'|informativo.*{numero}.*href='([^']*\.html)'|{numero}.*informativo.*href='([^']*\.html)'"
        matches = re.finditer(pattern, resp.text, re.IGNORECASE)
        
        url_post = None
        for match in matches:
            url_post = next((g for g in match.groups() if g), None)
            if url_post:
                break
        
        if not url_post:
            # Tentar padrão mais simples
            if f'{numero}' in resp.text:
                pattern_simples = rf"href='([^']*{numero}[^']*\.html[^']*)'|href='([^']*\.html[^']*{numero}[^']*)'|href='([^']*{numero.zfill(4)}[^']*\.html[^']*)'|href='([^']*\.html[^']*{numero.zfill(4)}[^']*)'|href='([^']*0*{numero}[^']*\.html[^']*)'|href='([^']*\.html[^']*0*{numero}[^']*\.html)'"
                matches = re.finditer(pattern_simples, resp.text, re.IGNORECASE)
                for match in matches:
                    url_post = next((g for g in match.groups() if g), None)
                    if url_post:
                        break
        
        if url_post:
            if not url_post.startswith('http'):
                url_post = f"https://www.dizerodireito.com.br{url_post}"
            
            # Acessar o post HTML e procurar pelos PDFs
            resp_post = requests.get(url_post, headers=HEADERS, timeout=10)
            resp_post.raise_for_status()
            
            # Procurar por links de PDF no post
            pdf_matches = re.findall(
                r'href=["\'](https://[^\s"\']*\.pdf)["\']',
                resp_post.text,
                re.IGNORECASE
            )
            
            if pdf_matches:
                urls = {}
                for pdf_url in pdf_matches:
                    if 'resumido' in pdf_url.lower() or 'resumo' in pdf_url.lower():
                        urls['resumido'] = pdf_url
                    else:
                        urls['completo'] = pdf_url
                
                return urls
        
        return {}
    
    except Exception as e:
        return {}

def baixar_pdf(url, caminho_destino, silent=False):
    """Baixa um PDF e salva no caminho especificado"""
    try:
        if not silent:
            print(f"   Baixando: {caminho_destino.name}...", end=" ", flush=True)
        
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        
        # Verificar se é realmente um PDF
        if resp.headers.get('content-type', '').startswith('application/pdf') or b'%PDF' in resp.content:
            with open(caminho_destino, 'wb') as f:
                f.write(resp.content)
            
            if not silent:
                tamanho = len(resp.content) / 1024
                print(f"✓ ({tamanho:.1f} KB)")
            return True
        else:
            if not silent:
                print(f"✗ Arquivo não é PDF")
            return False
    
    except Exception as e:
        if not silent:
            print(f"✗ Erro: {e}")
        return False

def baixar_informativos_2023():
    """Baixa todos os informativos de 2023"""
    
    print("\n" + "="*80)
    print("📥 DOWNLOAD DE INFORMATIVOS 2023")
    print("="*80)
    
    total_baixados = 0
    
    for tribunal in ['stf', 'stj']:
        folder = DOWNLOADS_DIR / f"Informativos_{tribunal.upper()}"
        folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🔎 {tribunal.upper()} 2023")
        print("-" * 40)
        
        # Determinar números para 2023 (baseado em feed Atom)
        ranges_2023 = {
            'stf': list(range(1096, 1121)),  # 1096-1120
            'stj': [11, 12, 13] + list(range(778, 800))  # [11,12,13,778-799]
        }
        
        contador = 0
        for numero in ranges_2023[tribunal]:
            urls = obter_urls_informativos(tribunal, numero)
            
            if urls:
                print(f"\n✓ info-{numero}-{tribunal}")
                
                for tipo, url in urls.items():
                    if tipo == 'completo':
                        nome_arquivo = f"info-{numero}-{tribunal}.pdf"
                    else:
                        nome_arquivo = f"info-{numero}-{tribunal}-{tipo}.pdf"
                    
                    caminho = folder / nome_arquivo
                    
                    if caminho.exists():
                        print(f"   ✓ {nome_arquivo} (já existe)")
                    else:
                        if baixar_pdf(url, caminho):
                            contador += 1
                            total_baixados += 1
                        
                        time.sleep(0.3)  # Delay entre requisições
            else:
                print(f"✗ info-{numero}-{tribunal}")
            
            time.sleep(0.2)
        
        print(f"\n   {contador} novo(s) arquivo(s) baixado(s) para {tribunal.upper()}")
    
    return total_baixados

def processar_materiais_outros():
    """Catalogar materiais em OUTROS para referência"""
    
    print("\n" + "="*80)
    print("📂 MATERIAIS EM OUTROS")
    print("="*80)
    
    outros_dir = DOWNLOADS_DIR / "OUTROS"
    
    for year in [2019, 2020, 2021, 2022, 2023, 2024]:
        year_dir = outros_dir / str(year)
        if year_dir.exists():
            pdf_files = list(year_dir.glob("*.pdf"))
            if pdf_files:
                print(f"\n📁 {year}: {len(pdf_files)} arquivos")
                if year == 2023 or len(pdf_files) < 10:
                    for f in sorted(pdf_files)[:5]:
                        print(f"   • {f.name}")
                    if len(pdf_files) > 5:
                        print(f"   ... e {len(pdf_files) - 5} mais")

def main():
    total = baixar_informativos_2023()
    processar_materiais_outros()
    
    print("\n" + "="*80)
    print("✅ RESUMO")
    print("="*80)
    print(f"Total de arquivos baixados: {total}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
