#!/usr/bin/env python3
"""
Upload de informativos para Google Drive
Versão com autenticação manual via URL
"""
import os
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import time

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_FILE = Path('secrets/drive_token.json')
CLIENT_FILE = Path('secrets/oauth_client.json')

BASE_DIR = Path(__file__).parent.parent
DOWNLOADS = BASE_DIR / "downloads"
STF_DIR = DOWNLOADS / "Informativos_STF"
STJ_DIR = DOWNLOADS / "Informativos_STJ"

# Variável global para armazenar a autenticação
auth_code = None
server_running = True

class OAuthHandler(BaseHTTPRequestHandler):
    """Handler para capturar o código de autenticação"""
    def do_GET(self):
        global auth_code
        query_components = parse_qs(urlparse(self.path).query)
        if 'code' in query_components:
            auth_code = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <html>
            <head><meta charset="utf-8"><title>Autenticação bem-sucedida</title></head>
            <body>
            <h1>✓ Autenticação bem-sucedida!</h1>
            <p>Você pode fechar esta janela agora.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suprimir logs

def autenticar():
    """Autentica com Google Drive API"""
    creds = None
    
    # Tentar carregar credenciais salvas
    if CREDS_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(CREDS_FILE), SCOPES)
            if creds.expired and creds.refresh_token:
                print("🔄 Atualizando credenciais...")
                creds.refresh(Request())
                with open(CREDS_FILE, 'w') as token:
                    token.write(creds.to_json())
            print("✓ Usando credenciais existentes")
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"⚠️  Credenciais inválidas")
            CREDS_FILE.unlink()
    
    if not CLIENT_FILE.exists():
        print(f"❌ Arquivo {CLIENT_FILE} não encontrado!")
        return None
    
    print("\n🔐 Fazendo autenticação...")
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_FILE),
            scopes=SCOPES,
            redirect_uri='http://localhost:8080/'
        )
        
        # Obter URL de autorização
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline'
        )
        
        print("\n📌 Abra este link no navegador:")
        print(auth_url)
        print("\nAguardando callback...")
        
        # Iniciar servidor local
        global auth_code
        httpd = HTTPServer(('localhost', 8080), OAuthHandler)
        
        # Tentar abrir navegador automaticamente
        try:
            webbrowser.open(auth_url)
            print("(Navegador aberto automaticamente)")
        except:
            pass
        
        # Aguardar até 60 segundos
        start = time.time()
        while auth_code is None and (time.time() - start) < 60:
            httpd.handle_request()
            if auth_code:
                break
        
        httpd.server_close()
        
        if not auth_code:
            print("❌ Timeout na autenticação")
            return None
        
        # Usar código para obter credenciais
        creds = flow.fetch_token(code=auth_code)
        
        # Salvar
        with open(CREDS_FILE, 'w') as token:
            token.write(flow.credentials.to_json())
        
        print("✓ Autenticação bem-sucedida!")
        return build('drive', 'v3', credentials=flow.credentials)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def create_folder(service, name, parent_id=None):
    """Cria pasta"""
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder['id']

def find_folder(service, name):
    """Encontra pasta"""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id)', pageSize=1).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def upload_file(service, file_path, folder_id):
    """Faz upload"""
    file_metadata = {
        'name': file_path.name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(str(file_path))
    service.files().create(body=file_metadata, media_body=media).execute()

if __name__ == "__main__":
    print("=" * 70)
    print("📤 UPLOAD DE INFORMATIVOS PARA GOOGLE DRIVE")
    print("=" * 70)
    
    service = autenticar()
    if not service:
        exit(1)
    
    print("\n📁 Verificando estrutura...")
    main_id = find_folder(service, 'DOD - Informativos')
    if not main_id:
        print("   Criando pasta principal...")
        main_id = create_folder(service, 'DOD - Informativos')
    print(f"✓ Pasta principal criada/encontrada")
    
    stf_id = find_folder(service, 'Informativos_STF')
    if not stf_id:
        stf_id = create_folder(service, 'Informativos_STF', main_id)
        print(f"✓ Criada pasta STF")
    else:
        print(f"✓ Pasta STF encontrada")
    
    stj_id = find_folder(service, 'Informativos_STJ')
    if not stj_id:
        stj_id = create_folder(service, 'Informativos_STJ', main_id)
        print(f"✓ Criada pasta STJ")
    else:
        print(f"✓ Pasta STJ encontrada")
    
    print(f"\n📤 Upload STF ({len(list(STF_DIR.glob('*.pdf')))} arquivos)...")
    stf_files = sorted(STF_DIR.glob("*.pdf"))
    for i, f in enumerate(stf_files, 1):
        try:
            upload_file(service, f, stf_id)
            if i % 50 == 0 or i == len(stf_files):
                print(f"   [{i}/{len(stf_files)}] ✓")
        except:
            pass
    
    print(f"\n📤 Upload STJ ({len(list(STJ_DIR.glob('*.pdf')))} arquivos)...")
    stj_files = sorted(STJ_DIR.glob("*.pdf"))
    for i, f in enumerate(stj_files, 1):
        try:
            upload_file(service, f, stj_id)
            if i % 50 == 0 or i == len(stj_files):
                print(f"   [{i}/{len(stj_files)}] ✓")
        except:
            pass
    
    print("\n" + "=" * 70)
    print("✅ UPLOAD CONCLUÍDO")
    print("=" * 70)
