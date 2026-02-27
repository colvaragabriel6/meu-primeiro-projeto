#!/usr/bin/env python3
"""
Script melhorado para baixar informativos de 2023 - tentando diferentes estratégias
"""

import requests
import re
import time
from pathlib import Path

DOWNLOADS_DIR = Path("downloads")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Informativos que faltam
FALTANTES = {
    'stf': [1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112],
    'stj': [11, 13, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793]
}

def tentar_url_direto(tribunal, numero):
    """Tenta acessar URLs diretas aos PDFs"""
    
    # Tentar diferentes padrões de URL
    padroes = [
        f"https://www.dizerodireito.com.br/2023/informativo-comentado-{numero}-{tribunal}.html",
        f"https://www.dizerodireito.com.br/2023/{numero}/{tribunal}/download.html",
        f"https://drive.google.com/search?q=info-{numero}-{tribunal} filetype:pdf",
    ]
    
    for url in padroes:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                # Procurar por PDFs
                pdfs = re.findall(
                    r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                    resp.text,
                    re.IGNORECASE
                )
                
                if pdfs:
                    return pdfs
        except:
            pass
    
    return []

def buscar_em_edicoes(tribunal, numero):
    """Tenta buscar em páginas de edições/editions"""
    
    try:
        # Tentar buscar na pasta de edições
        ano = 2023
        url = f"https://www.dizerodireito.com.br/search?q=+updated:2023+info-{numero}-{tribunal}+filetype:pdf"
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        # Procurar por links
        pdfs = re.findall(
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            resp.text,
            re.IGNORECASE
        )
        
        if pdfs:
            return pdfs
    except:
        pass
    
    return []

def obter_url_post_melhorado(tribunal, numero):
    """Tenta obter URL do post de forma mais robusta"""
    
    try:
        # Estratégia 1: Procurar na página de tags ano/tribunal
        ano = 2023
        url_tags = f"https://www.dizerodireito.com.br/search/label/informativo%20comentado%20{tribunal}-{ano}"
        resp = requests.get(url_tags, headers=HEADERS, timeout=10)
        
        # Procurar especificamente por este número
        # Padrões diferentes que podem aparecer
        patterns = [
            rf'<h1[^>]*><a[^>]*href=["\']([^"\']*{numero}[^"\']*\.html)["\'][^>]*>',  # h1 pattern
            rf'<a[^>]*href=["\']([^"\']*{numero}[^"\']*\.html)["\'][^>]*>.*?{numero}',  # link direto
            rf'{numero}[^<]*<a[^>]*href=["\']([^"\']*\.html)["\']',  # número seguido de link
            rf'{numero:04d}[^<]*<a[^>]*href=["\']([^"\']*\.html)["\']',  # número com zeros
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resp.text, re.IGNORECASE)
            if match:
                url_post = match.group(1)
                if not url_post.startswith('http'):
                    url_post = f"https://www.dizerodireito.com.br{url_post}"
                
                return url_post
        
        return None
    except:
        return None

def baixar_pdf(url, caminho_destino):
    """Baixa um PDF"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        
        if b'%PDF' in resp.content or resp.headers.get('content-type', '').startswith('application/pdf'):
            with open(caminho_destino, 'wb') as f:
                f.write(resp.content)
            
            print(f"   ✓ {caminho_destino.name} ({len(resp.content)/1024:.1f} KB)")
            return True
    except:
        pass
    
    return False

def processar_informativo(tribunal, numero):
    """Tenta baixar um informativo por diferentes métodos"""
    
    folder = DOWNLOADS_DIR / f"Informativos_{tribunal.upper()}"
    folder.mkdir(parents=True, exist_ok=True)
    
    # Verificar se já existe
    nome_base = f"info-{numero}-{tribunal}"
    existentes = list(folder.glob(f"{nome_base}*.pdf"))
    
    if existentes:
        print(f"✓ info-{numero}-{tribunal} já existe ({len(existentes)} arquivo(s))")
        return True
    
    print(f"🔍 Buscando info-{numero}-{tribunal}...", end=" ", flush=True)
    
    # Estratégia 1: Tentar URL do post
    url_post = obter_url_post_melhorado(tribunal, numero)
    
    if url_post:
        print(f"encontrado")
        try:
            resp = requests.get(url_post, headers=HEADERS, timeout=10)
            pdfs = re.findall(
                r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                resp.text,
                re.IGNORECASE
            )
            
            if pdfs:
                baixados = 0
                for pdf_url in pdfs:
                    # Limpar URL
                    pdf_url = pdf_url.split('?')[0].strip('"\'')
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://www.dizerodireito.com.br{pdf_url}"
                    
                    # Determinar nome do arquivo
                    if 'resumido' in pdf_url.lower():
                        nome_arquivo =  f"{nome_base}-resumido.pdf"
                    else:
                        nome_arquivo = f"{nome_base}.pdf"
                    
                    caminho = folder / nome_arquivo
                    if baixar_pdf(pdf_url, caminho):
                        baixados += 1
                    
                    time.sleep(0.2)
                
                return baixados > 0
        except:
            pass
    
    print(f"não encontrado")
    return False

def main():
    print("\n" + "="*80)
    print("📥 DOWNLOAD DE INFORMATIVOS 2023 - FALTANTES")
    print("="*80)
    
    total_baixados = 0
    
    for tribunal in ['stf', 'stj']:
        print(f"\n🔎 {tribunal.upper()} 2023 ({len(FALTANTES[tribunal])} informativos)")
        print("-" * 40)
        
        for numero in FALTANTES[tribunal]:
            if processar_informativo(tribunal, numero):
                total_baixados += 1
            
            time.sleep(0.3)
        
        print()
    
    print("="*80)
    print(f"✅ RESUMO: {total_baixados} informativos baixados")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
