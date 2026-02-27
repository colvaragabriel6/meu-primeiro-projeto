#!/usr/bin/env python3
"""
Script para baixar atualizações de livros e materiais da categoria "Atualizações dos Livros"
"""

import requests
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

DOWNLOADS_DIR = Path("downloads")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def obter_arquivos_existentes(ano):
    """Obtém lista de arquivos já baixados para um ano"""
    outros_dir = DOWNLOADS_DIR / "OUTROS" / str(ano)
    if not outros_dir.exists():
        return set()
    
    arquivos = set()
    for f in outro_dir.glob("*.pdf"):
        arquivos.add(f.name.lower())
    
    return arquivos

def extrair_links_pdfs(html):
    """Extrai todos os links de PDF de um HTML"""
    matches = re.findall(
        r'href=["\']([^"\']*\.pdf(?:["\']|\?[^"\']*)["\'])',
        html,
        re.IGNORECASE
    )
    
    pdfs = []
    for match in matches:
        # Limpar parâmetros de URL se houver
        url = match.split('?')[0].strip('"\'')
        if url.endswith('.pdf'):
            pdfs.append(url)
    
    return list(set(pdfs))

def buscar_posts_atualizacoes():
    """Busca posts da categoria de atualizações"""
    print("\n🔍 Buscando 'Atualizações dos Livros'...\n")
    
    try:
        # Buscar a página de atualizações
        url = "https://www.dizerodireito.com.br/search/label/Atualizações%20dos%20Livro"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        
        # Procurar por links de posts
        pattern = r"<h1[^>]*class='vbs_post_title'>[^<]*<a[^>]*href='([^']*)'[^>]*title='([^']*)'[^>]*>"
        matches = re.finditer(pattern, resp.text, re.IGNORECASE)
        
        posts = []
        for match in matches:
            url_post = match.group(1)
            titulo = match.group(2)
            
            # Tentar extrair ano do título
            ano_match = re.search(r'(20\d{2})', titulo)
            ano = int(ano_match.group(1)) if ano_match else None
            
            posts.append({
                'url': url_post,
                'titulo': titulo,
                'ano': ano
            })
        
        print(f"✓ Encontrados {len(posts)} posts com atualizações\n")
        return posts
    
    except Exception as e:
        print(f"✗ Erro ao buscar atualizações: {e}\n")
        return []

def baixar_atualizacoes(posts):
    """Baixa os PDFs dos posts de atualizações"""
    
    total_baixados = 0
    
    for post in posts:
        ano = post['ano']
        titulo = post['titulo']
        url_post = post['url']
        
        if not ano:
            continue
        
        print(f"📄 {titulo} ({ano})")
        
        try:
            # Acessar o post
            resp = requests.get(url_post, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            
            # Extrair PDFs
            pdfs = extrair_links_pdfs(resp.text)
            
            if pdfs:
                # Criar pasta do ano
                outros_dir = DOWNLOADS_DIR / "OUTROS" / str(ano)
                outros_dir.mkdir(parents=True, exist_ok=True)
                
                # Obter arquivos existentes
                existentes = obter_arquivos_existentes(ano)
                
                for pdf_url in pdfs:
                    # Extrair nome do arquivo
                    nome_arquivo = pdf_url.split('/')[-1].split('?')[0]
                    
                    if not nome_arquivo.lower() in existentes:
                        print(f"   Baixando: {nome_arquivo}...", end=" ", flush=True)
                        
                        try:
                            resp_pdf = requests.get(pdf_url, headers=HEADERS, timeout=30)
                            resp_pdf.raise_for_status()
                            
                            if b'%PDF' in resp_pdf.content or resp_pdf.headers.get('content-type', '').startswith('application/pdf'):
                                caminho = outros_dir / nome_arquivo
                                with open(caminho, 'wb') as f:
                                    f.write(resp_pdf.content)
                                
                                tamanho = len(resp_pdf.content) / 1024
                                print(f"✓ ({tamanho:.1f} KB)")
                                total_baixados += 1
                            else:
                                print("✗ Não é PDF")
                        except Exception as e:
                            print(f"✗ Erro: {e}")
                    else:
                        print(f"   ✓ {nome_arquivo} (já existe)")
                    
                    time.sleep(0.5)
            else:
                print(f"   ℹ️  Nenhum PDF encontrado")
        
        except Exception as e:
            print(f"   ✗ Erro: {e}")
        
        time.sleep(0.5)
    
    return total_baixados

def main():
    print("\n" + "="*80)
    print("📥 DOWNLOAD DE MATERIAIS - ATUALIZAÇÕES DOS LIVROS")
    print("="*80)
    
    # Buscar posts
    posts = buscar_posts_atualizacoes()
    
    if posts:
        # Baixar atualizações
        total = baixar_atualizacoes(posts)
        
        print("\n" + "="*80)
        print("✅ RESUMO")
        print("="*80)
        print(f"Total de arquivos baixados: {total}")
        print(f"{'='*80}\n")
    else:
        print("⚠️  Nenhum post encontrado")

if __name__ == "__main__":
    main()
