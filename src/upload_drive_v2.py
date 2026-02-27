#!/usr/bin/env python3
"""
Upload de informativos para Google Drive (versão simplificada)
Usa credenciais service account ou OAuth com melhor tratamento de erros
"""
import os
import json
from pathlib import Path
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
                # Salvar token atualizado
                with open(CREDS_FILE, 'w') as token:
                    token.write(creds.to_json())
            print("✓ Usando credenciais existentes")
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"⚠️  Credenciais inválidas: {str(e)[:60]}")
            CREDS_FILE.unlink()
            print("   Removido. Será solicitada nova autenticação...")
    
    # Fazer novo login OAuth
    if not CLIENT_FILE.exists():
        print(f"❌ Arquivo {CLIENT_FILE} não encontrado!")
        print("   Baixe em: https://console.cloud.google.com")
        return None
    
    print("\n🔐 Abrindo navegador para autenticação...")
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_FILE), SCOPES
        )
        creds = flow.run_local_server(port=8080)
        
        # Salvar para próximo uso
        with open(CREDS_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print("✓ Autenticação bem-sucedida")
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return None

def create_folder(service, name, parent_id=None):
    """Cria pasta no Drive"""
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder['id']

def find_folder(service, name):
    """Encontra pasta por nome"""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id)', pageSize=1).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def upload_file(service, file_path, folder_id):
    """Faz upload de arquivo"""
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
    
    # Autenticar
    service = autenticar()
    if not service:
        print("\n❌ Não foi possível autenticar")
        exit(1)
    
    # Criar/encontrar pastas
    print("\n📁 Verificando estrutura de pastas...")
    main_id = find_folder(service, 'DOD - Informativos')
    if not main_id:
        print("   Criando pasta 'DOD - Informativos'...")
        main_id = create_folder(service, 'DOD - Informativos')
    print(f"✓ Pasta principal: {main_id[:20]}...")
    
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
    
    # Upload STF
    print(f"\n📤 Upload STF...")
    stf_files = sorted(STF_DIR.glob("*.pdf"))
    for i, f in enumerate(stf_files, 1):
        try:
            upload_file(service, f, stf_id)
            if i % 50 == 0 or i == len(stf_files):
                print(f"   {i}/{len(stf_files)} ✓")
        except Exception as e:
            print(f"   ✗ {f.name}: {str(e)[:40]}")
    
    # Upload STJ
    print(f"\n📤 Upload STJ...")
    stj_files = sorted(STJ_DIR.glob("*.pdf"))
    for i, f in enumerate(stj_files, 1):
        try:
            upload_file(service, f, stj_id)
            if i % 50 == 0 or i == len(stj_files):
                print(f"   {i}/{len(stj_files)} ✓")
        except Exception as e:
            print(f"   ✗ {f.name}: {str(e)[:40]}")
    
    print("\n" + "=" * 70)
    print("✅ UPLOAD CONCLUÍDO")
    print("=" * 70)
    print(f"\n📍 Pasta: DOD - Informativos")
    print(f"📊 Informativos enviados: {len(stf_files) + len(stj_files)}")
