#!/usr/bin/env python3
"""
Script para baixar todos os informativos de 2023 usando o feed Atom
"""

import requests
import re
import time
from pathlib import Path

DOWNLOADS_DIR = Path("downloads")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def extrair_links_feed_atom(tribunal, ano):
    """Extrai links de posts do feed Atom"""
    
    url_feed = f"https://www.dizerodireito.com.br/feeds/posts/default/-/informativo%20comentado%20{tribunal}-{ano}?max-results=100"
    
    try:
        resp = requests.get(url_feed, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        
        posts = {}
        
        # Procurar por padrões no XML
        # <entry>...<title>...</title>...<link href="..."/>...</entry>
        
        # Extrair cada <entry>...</entry>
        entries = re.findall(r'<entry.*?</entry>', resp.text, re.DOTALL)
        
        for entry_xml in entries:
            # Extrair título
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', entry_xml)
            title = title_match.group(1) if title_match else ""
            
            # Extrair número do informativo do título
            num_match = re.search(rf'(\d+).*{tribunal}', title, re.IGNORECASE)
            if not num_match:
                num_match = re.search(rf'info-(\d+)-{tribunal}', title, re.IGNORECASE)
            
            if num_match:
                numero = int(num_match.group(1))
                
                # Extrair link href (rel="alternate")
                link_match = re.search(r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']alternate["\']', entry_xml)
                if not link_match:
                    link_match = re.search(r'<link[^>]*rel=["\']alternate["\'][^>]*href=["\']([^"\']+)["\']', entry_xml)
                if not link_match:
                    link_match = re.search(r'<link[^>]*href=["\']([^"\']+\.html[^"\']*)["\']', entry_xml)
                
                if link_match:
                    link = link_match.group(1)
                    posts[numero] = {
                        'titulo': title,
                        'url_post': link,
                        'numero': numero
                    }
        
        return posts
    
    except Exception as e:
        print(f"  ✗ Erro ao acessar feed: {e}")
        return {}

def baixar_pdfs_do_post(tribunal, numero, url_post):
    """Acessa o post e baixa os PDFs"""
    
    try:
        resp = requests.get(url_post, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        
        # Procurar por links de PDF
        pdfs = re.findall(
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            resp.text,
            re.IGNORECASE
        )
        
        if pdfs:
            # Filtrar PDFs únicos
            pdfs = list(set(pdfs))
            
            folder = DOWNLOADS_DIR / f"Informativos_{tribunal.upper()}"
            folder.mkdir(parents=True, exist_ok=True)
            
            baixados = 0
            for pdf_url in pdfs:
                # Limpar URL
                pdf_url = pdf_url.split('?')[0].strip('"\'')
                if not pdf_url.startswith('http'):
                    pdf_url = f"https://www.dizerodireito.com.br{pdf_url}"
                
                # Determinar nome do arquivo
                if 'resumido' in pdf_url.lower() or 'resumo' in pdf_url.lower():
                    nome_arquivo = f"info-{numero}-{tribunal}-resumido.pdf"
                else:
                    nome_arquivo = f"info-{numero}-{tribunal}.pdf"
                
                caminho = folder / nome_arquivo
                
                # Verificar se já existe
                if caminho.exists():
                    continue
                
                # Baixar PDF
                try:
                    resp_pdf = requests.get(pdf_url, headers=HEADERS, timeout=30)
                    resp_pdf.raise_for_status()
                    
                    if b'%PDF' in resp_pdf.content:
                        with open(caminho, 'wb') as f:
                            f.write(resp_pdf.content)
                        
                        baixados += 1
                except:
                    pass
                
                time.sleep(0.2)
            
            return baixados
        
        return 0
    
    except Exception as e:
        return 0

def main():
    print("\n" + "="*80)
    print("📥 DOWNLOAD DE INFORMATIVOS 2023 VIA FEED ATOM")
    print("="*80)
    
    total_baixados = 0
    
    for tribunal in ['stf', 'stj']:
        print(f"\n🔎 {tribunal.upper()} 2023")
        print("-" * 40)
        
        # Extrair posts do feed
        posts = extrair_links_feed_atom(tribunal, '2023')
        
        if posts:
            print(f"✓ Encontrados {len(posts)} posts\n")
            
            contador_tribunal = 0
            for numero in sorted(posts.keys()):
                post_info = posts[numero]
                
                print(f"  info-{numero}-{tribunal}...", end=" ", flush=True)
                
                baixados = baixar_pdfs_do_post(tribunal, numero, post_info['url_post'])
                
                if baixados > 0:
                    print(f"✓ ({baixados} arquivo(s))")
                    contador_tribunal += baixados
                    total_baixados += baixados
                else:
                    print("(já existe)")
                
                time.sleep(0.1)
            
            print(f"\n   {contador_tribunal} arquivo(s) novo(s) baixado(s)")
        else:
            print("✗ Nenhum post encontrado")
    
    print("\n" + "="*80)
    print("✅ RESUMO")
    print("="*80)
    print(f"Total de arquivos baixados: {total_baixados}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
