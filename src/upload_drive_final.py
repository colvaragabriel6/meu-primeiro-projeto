#!/usr/bin/env python3
"""
Upload de informativos para Google Drive
Com autenticação manual por código
"""
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
    """Autentica manualmente com Google Drive API"""
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
            print("✓ Credenciais carregadas com sucesso")
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"⚠️  Credenciais expiradas/inválidas")
            if CREDS_FILE.exists():
                CREDS_FILE.unlink()
    
    if not CLIENT_FILE.exists():
        print(f"❌ Arquivo {CLIENT_FILE} não encontrado!")
        return None
    
    print("\n🔐 Iniciando autenticação manual...")
    print("-" * 70)
    
    try:
        # usar out-of-band para permitir entrada manual do código
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_FILE),
            scopes=SCOPES
        )
        
        # Gerar URL com redirect_uri correto para autorização manual
        auth_url, _ = flow.authorization_url(
            redirect_uri='urn:ietf:wg:oauth:2.0:oob',
            prompt='consent',
            access_type='offline'
        )
        
        print("\n1️⃣  Abra este link no seu navegador:")
        print(auth_url)
        print("\n2️⃣  Autorize o acesso")
        print("\n3️⃣  Copie o código de autorização exibido")
        
        # Aguardar código
        code = input("\n📋 Cole o código de autorização aqui: ").strip()
        
        if not code:
            print("❌ Código não fornecido")
            return None
        
        # Trocar código por credenciais com redirect_uri correto
        creds = flow.fetch_token(code=code, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        
        # Salvar para próximo uso
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
    """Encontra pasta por nome"""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)', pageSize=1).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def file_exists(service, folder_id, filename):
    """Verifica se arquivo já existe na pasta"""
    query = f"parents='{folder_id}' and name='{filename}' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id)', pageSize=1).execute()
    return len(results.get('files', [])) > 0

def upload_file(service, file_path, folder_id):
    """Faz upload (pulando se já existe)"""
    if file_exists(service, folder_id, file_path.name):
        return False  # Já existe
    
    file_metadata = {
        'name': file_path.name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(str(file_path))
    service.files().create(body=file_metadata, media_body=media).execute()
    return True

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("📤 UPLOAD DE INFORMATIVOS PARA GOOGLE DRIVE")
    print("=" * 70)
    
    # Autenticar
    print("\n🔐 Verificando autenticação...")
    service = autenticar()
    if not service:
        print("\n❌ Falha na autenticação")
        exit(1)
    
    # Verificar estrutura de pastas
    print("\n📁 Verificando estrutura de pastas...")
    main_id = find_folder(service, 'DOD - Informativos')
    if main_id:
        print("✓ Pasta 'DOD - Informativos' encontrada")
    else:
        print("✓ Criando pasta 'DOD - Informativos'...")
        main_id = create_folder(service, 'DOD - Informativos')
    
    stf_id = find_folder(service, 'Informativos_STF')
    if not stf_id:
        print("✓ Criando pasta 'Informativos_STF'...")
        stf_id = create_folder(service, 'Informativos_STF', main_id)
    else:
        print("✓ Pasta 'Informativos_STF' encontrada")
    
    stj_id = find_folder(service, 'Informativos_STJ')
    if not stj_id:
        print("✓ Criando pasta 'Informativos_STJ'...")
        stj_id = create_folder(service, 'Informativos_STJ', main_id)
    else:
        print("✓ Pasta 'Informativos_STJ' encontrada")
    
    # Upload STF
    print(f"\n📤 Upload STF...")
    stf_files = sorted(STF_DIR.glob("*.pdf"))
    stf_novo = 0
    stf_exist = 0
    
    for i, f in enumerate(stf_files, 1):
        try:
            if upload_file(service, f, stf_id):
                stf_novo += 1
            else:
                stf_exist += 1
            
            if i % 100 == 0 or i == len(stf_files):
                print(f"   Processados {i}/{len(stf_files)} (novo: {stf_novo}, existente: {stf_exist})")
        except Exception as e:
            print(f"   ✗ Erro em {f.name}: {str(e)[:40]}")
    
    # Upload STJ
    print(f"\n📤 Upload STJ...")
    stj_files = sorted(STJ_DIR.glob("*.pdf"))
    stj_novo = 0
    stj_exist = 0
    
    for i, f in enumerate(stj_files, 1):
        try:
            if upload_file(service, f, stj_id):
                stj_novo += 1
            else:
                stj_exist += 1
            
            if i % 100 == 0 or i == len(stj_files):
                print(f"   Processados {i}/{len(stj_files)} (novo: {stj_novo}, existente: {stj_exist})")
        except Exception as e:
            print(f"   ✗ Erro em {f.name}: {str(e)[:40]}")
    
    # Resumo
    print("\n" + "=" * 70)
    print("✅ UPLOAD CONCLUÍDO")
    print("=" * 70)
    print(f"\nSTF: {stf_novo} novo(s), {stf_exist} já existente(s)")
    print(f"STJ: {stj_novo} novo(s), {stj_exist} já existente(s)")
    print(f"TOTAL: {stf_novo + stj_novo} arquivo(s) novo(s)")
    print(f"\n📍 Pasta no Drive: DOD - Informativos")
