#!/usr/bin/env python3
"""
Upload de informativos para Google Drive
Cria pasta "DOD - Informativos" com subpastas STF e STJ
"""
import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configurações
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDS_FILE = 'secrets/drive_token.json'
CLIENT_FILE = 'secrets/oauth_client.json'

BASE_DIR = Path(__file__).parent.parent
DOWNLOADS = BASE_DIR / "downloads"
STF_DIR = DOWNLOADS / "Informativos_STF"
STJ_DIR = DOWNLOADS / "Informativos_STJ"

def autenticar():
    """Autentica com Google Drive API"""
    creds = None
    
    # Carregar token existente se houver
    if os.path.exists(CREDS_FILE):
        try:
            creds = Credentials.from_authorized_user_file(CREDS_FILE, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"⚠️  Token expirou ou inválido: {str(e)[:50]}")
            print("   Vou remover e fazer nova autenticação...")
            os.remove(CREDS_FILE)
    
    # Se não, usar OAuth
    if not os.path.exists(CLIENT_FILE):
        print("❌ Arquivo oauth_client.json não encontrado!")
        print("   Baixe o arquivo de credenciais do Google Cloud Console")
        return None
    
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Salvar token para próximo uso
    with open(CREDS_FILE, 'w') as token:
        token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def criar_pasta(service, nome_pasta, pasta_pai=None):
    """Cria pasta no Google Drive"""
    file_metadata = {
        'name': nome_pasta,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if pasta_pai:
        file_metadata['parents'] = [pasta_pai]
    
    result = service.files().create(body=file_metadata, fields='id').execute()
    return result['id']

def buscar_pasta(service, nome_pasta):
    """Procura pastas existentes por nome"""
    query = f"name='{nome_pasta}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)', pageSize=10).execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    return None

def fazer_upload(service, filepath, nome_arquivo, pasta_id):
    """Faz upload de arquivo para pasta específica"""
    file_metadata = {
        'name': nome_arquivo,
        'parents': [pasta_id]
    }
    
    media = MediaFileUpload(str(filepath), resumable=True)
    result = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    return result['id']

if __name__ == "__main__":
    print("=" * 60)
    print("📤 UPLOAD DE INFORMATIVOS PARA GOOGLE DRIVE")
    print("=" * 60)
    
    # Autenticar
    print("\n🔐 Autenticando com Google Drive...")
    try:
        service = autenticar()
        if not service:
            exit(1)
        print("✓ Autenticado com sucesso")
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("   Execute: pip install google-auth-oauthlib google-api-python-client")
        exit(1)
    except Exception as e:
        print(f"❌ Erro de autenticação: {e}")
        exit(1)
    
    # Buscar ou criar pasta principal
    print("\n📁 Procurando/criando pasta 'DOD - Informativos'...")
    pasta_principal_id = buscar_pasta(service, 'DOD - Informativos')
    
    if pasta_principal_id:
        print(f"✓ Pasta encontrada (ID: {pasta_principal_id[:10]}...)")
    else:
        print("✓ Criando pasta...")
        pasta_principal_id = criar_pasta(service, 'DOD - Informativos')
        print(f"✓ Pasta criada (ID: {pasta_principal_id[:10]}...)")
    
    # Criar subpastas
    print("\n📂 Criando subpastas...")
    stf_pasta_id = buscar_pasta(service, 'Informativos_STF')
    if not stf_pasta_id:
        stf_pasta_id = criar_pasta(service, 'Informativos_STF', pasta_principal_id)
        print(f"✓ Pasta STF criada")
    else:
        print(f"✓ Pasta STF encontrada")
    
    stj_pasta_id = buscar_pasta(service, 'Informativos_STJ')
    if not stj_pasta_id:
        stj_pasta_id = criar_pasta(service, 'Informativos_STJ', pasta_principal_id)
        print(f"✓ Pasta STJ criada")
    else:
        print(f"✓ Pasta STJ encontrada")
    
    # Upload de arquivos STF
    print(f"\n📤 Upload de informativos STF...")
    stf_files = sorted(STF_DIR.glob("*.pdf"))
    stf_enviados = 0
    stf_erros = 0
    
    for i, arquivo in enumerate(stf_files, 1):
        try:
            fazer_upload(service, arquivo, arquivo.name, stf_pasta_id)
            stf_enviados += 1
            if i % 50 == 0 or i == len(stf_files):
                print(f"  {i}/{len(stf_files)} arquivos STF enviados")
        except Exception as e:
            stf_erros += 1
            if stf_erros <= 5:
                print(f"  ✗ Erro em {arquivo.name}: {str(e)[:50]}")
    
    # Upload de arquivos STJ
    print(f"\n📤 Upload de informativos STJ...")
    stj_files = sorted(STJ_DIR.glob("*.pdf"))
    stj_enviados = 0
    stj_erros = 0
    
    for i, arquivo in enumerate(stj_files, 1):
        try:
            fazer_upload(service, arquivo, arquivo.name, stj_pasta_id)
            stj_enviados += 1
            if i % 50 == 0 or i == len(stj_files):
                print(f"  {i}/{len(stj_files)} arquivos STJ enviados")
        except Exception as e:
            stj_erros += 1
            if stj_erros <= 5:
                print(f"  ✗ Erro em {arquivo.name}: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("✅ RESUMO DO UPLOAD")
    print("=" * 60)
    print(f"STF: {stf_enviados}/{len(stf_files)} arquivos enviados")
    if stf_erros > 0:
        print(f"     {stf_erros} erros")
    print(f"STJ: {stj_enviados}/{len(stj_files)} arquivos enviados")
    if stj_erros > 0:
        print(f"     {stj_erros} erros")
    print(f"TOTAL: {stf_enviados + stj_enviados}/{len(stf_files) + len(stj_files)}")
    print(f"\n📍 Pasta: DOD - Informativos")
