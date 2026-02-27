#!/usr/bin/env python3
"""
Script para baixar os informativos faltantes de 2024
"""

import requests
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup

DOWNLOADS_DIR = Path("downloads")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Informativos faltando
FALTANTES = {
    'stf': [1162],
    'stj': [835, 836, 837]
}

def obter_urls_download(tribunal, numero):
    """Obtém URLs de download para um informativo específico"""
    print(f"\n🔍 Buscando info-{numero}-{tribunal}...", end=" ", flush=True)
    
    urls = {}
    
    try:
        # Primeiro, procurar pelo post na página de tags
        ano = '2024' if numero < 1170 or tribunal == 'stj' else '2025'  # Heurística
        
        url_tags = f"https://www.dizerodireito.com.br/search/label/informativo%20comentado%20{tribunal}-{ano}"
        resp = requests.get(url_tags, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        
        # Procurar pelo link do post HTML
        match_post = re.search(
            rf"href='([^']*informativo[^']*{numero}[^']*\.html[^']*)'",
            resp.text,
            re.IGNORECASE
        )
        
        if match_post:
            url_post = match_post.group(1)
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
                for pdf_url in pdf_matches:
                    if 'resumido' in pdf_url.lower() or 'resumo' in pdf_url.lower():
                        urls['resumido'] = pdf_url
                    else:
                        urls['completo'] = pdf_url
                
                print(f"✓ Encontrado")
                return urls
        
        print(f"✗ Não encontrado", flush=True)
        return {}
    
    except Exception as e:
        print(f"✗ Erro: {e}")
        return {}

def baixar_pdf(url, caminho_destino):
    """Baixa um PDF e salva no caminho especificado"""
    try:
        print(f"   Baixando: {caminho_destino.name}...", end=" ", flush=True)
        
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        
        # Verificar se é realmente um PDF
        if resp.headers.get('content-type', '').startswith('application/pdf') or b'%PDF' in resp.content:
            with open(caminho_destino, 'wb') as f:
                f.write(resp.content)
            
            tamanho = len(resp.content) / 1024  # KB
            print(f"✓ ({tamanho:.1f} KB)")
            return True
        else:
            print(f"✗ Arquivo não é PDF")
            return False
    
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("📥 DOWNLOAD DE INFORMATIVOS FALTANTES")
    print("="*80)
    
    baixados = {'stf': 0, 'stj': 0}
    
    for tribunal in ['stf', 'stj']:
        folder = DOWNLOADS_DIR / f"Informativos_{tribunal.upper()}"
        folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"🔎 {tribunal.upper()}")
        print(f"{'='*80}")
        
        for numero in FALTANTES[tribunal]:
            # Obter URLs
            urls = obter_urls_download(tribunal, numero)
            
            # Baixar arquivos encontrados
            if urls:
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
                            baixados[tribunal] += 1
                        
                time.sleep(0.5)  # Pequeno delay entre requisições
            else:
                print(f"   ⚠️  Não conseguiu encontrar download para info-{numero}-{tribunal}")
    
    # Resumo
    print(f"\n{'='*80}")
    print("✅ RESUMO")
    print(f"{'='*80}")
    print(f"STF: {baixados['stf']} arquivo(s) baixado(s)")
    print(f"STJ: {baixados['stj']} arquivo(s) baixado(s)")
    print(f"Total: {sum(baixados.values())} arquivo(s)")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
