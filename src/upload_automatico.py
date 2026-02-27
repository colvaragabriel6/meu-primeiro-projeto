#!/usr/bin/env python3
"""
Upload de informativos para Google Drive (versão não-interativa)
Execute: OAUTH_CODE="seu_codigo_aqui" python3 upload_automatico.py
Ou: python3 upload_automatico.py (exibirá instrução de autenticação)
"""
import os
import json
import sys
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

def autenticar_com_codigo(code):
    """Autentica usando código OAuth fornecido"""
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_FILE), 
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        creds = flow.fetch_token(code=code)
        
        # Salvar para próximo uso
        with open(CREDS_FILE, 'w') as token:
            token.write(flow.credentials.to_json())
        
        print("✓ Autenticação bem-sucedida!")
        return build('drive', 'v3', credentials=flow.credentials)
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return None

def autenticar_com_token_salvo():
    """Tenta usar token salvo anteriormente"""
    if not CREDS_FILE.exists():
        return None
    
    try:
        creds = Credentials.from_authorized_user_file(str(CREDS_FILE), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(CREDS_FILE, 'w') as token:
                token.write(creds.to_json())
        return build('drive', 'v3', credentials=creds)
    except:
        return None

def autenticar():
    """Autentica com Google Drive API"""
    # Primeiro, tentar token salvo
    service = autenticar_com_token_salvo()
    if service:
        print("✓ Usando credenciais existentes")
        return service
    
    # Tentar código via variável de ambiente
    code = os.environ.get('OAUTH_CODE')
    if code:
        print("🔐 Autenticando com código fornecido...")
        return autenticar_com_codigo(code)
    
    # Instrução para obter código manualmente
    print("\n" + "=" * 80)
    print("AUTENTICAÇÃO NECESSÁRIA")
    print("=" * 80)
    
    if not CLIENT_FILE.exists():
        print(f"❌ Arquivo {CLIENT_FILE} não encontrado!")
        return None
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_FILE), 
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline'
        )
        
        print("\n1️⃣  COPIE E ABRA ESTE LINK NO NAVEGADOR:")
        print("-" * 80)
        print(auth_url)
        print("-" * 80)
        print("\n2️⃣  Faça login e autorize o acesso")
        print("\n3️⃣  Você verá uma página com o 'Código de autorização'")
        print("\n4️⃣  COPIE TODO O CÓDIGO exibido (começa com '4/')")
        print("\n5️⃣  EXECUTE NOVAMENTE COM:")
        print(f'   OAUTH_CODE="seu_codigo_aqui" python3 {__file__}')
        print("\n" + "=" * 80)
        return None
        
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
    
    try:
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder['id']
    except Exception as e:
        print(f"  ✗ Erro ao criar pasta: {e}")
        return None

def find_folder(service, name):
    """Encontra pasta por nome"""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    try:
        results = service.files().list(q=query, spaces='drive', fields='files(id)', pageSize=1).execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None
    except:
        return None

def file_exists(service, folder_id, filename):
    """Verifica se arquivo já existe"""
    query = f"parents='{folder_id}' and name='{filename}' and trashed=false"
    try:
        results = service.files().list(q=query, spaces='drive', fields='files(id)', pageSize=1).execute()
        return len(results.get('files', [])) > 0
    except:
        return False

def upload_file(service, file_path, folder_id):
    """Faz upload"""
    if file_exists(service, folder_id, file_path.name):
        return False  # Já existe
    
    file_metadata = {
        'name': file_path.name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(str(file_path))
    try:
        service.files().create(body=file_metadata, media_body=media).execute()
        return True
    except:
        return None

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("📤 UPLOAD DE INFORMATIVOS PARA GOOGLE DRIVE")
    print("=" * 70)
    
    # Autenticar
    print("\n🔐 Verificando autenticação...")
    service = autenticar()
    
    if not service:
        print("\n❌ Não foi possível autenticar")
        sys.exit(1)
    
    # Estrutura de pastas
    print("\n📁 Preparando estrutura...")
    main_id = find_folder(service, 'DOD - Informativos')
    if main_id:
        print("✓ Pasta principal encontrada")
    else:
        print("✓ Criando pasta principal...")
        main_id = create_folder(service, 'DOD - Informativos')
    
    if not main_id:
        print("❌ Erro ao criar pasta principal")
        sys.exit(1)
    
    stf_id = find_folder(service, 'Informativos_STF')
    if not stf_id:
        print("✓ Criando pasta STF...")
        stf_id = create_folder(service, 'Informativos_STF', main_id)
    else:
        print("✓ Pasta STF encontrada")
    
    stj_id = find_folder(service, 'Informativos_STJ')
    if not stj_id:
        print("✓ Criando pasta STJ...")
        stj_id = create_folder(service, 'Informativos_STJ', main_id)
    else:
        print("✓ Pasta STJ encontrada")
    
    # Upload STF
    print(f"\n📤 Upload STF ({len(list(STF_DIR.glob('*.pdf')))} arquivos)...")
    stf_files = sorted(STF_DIR.glob("*.pdf"))
    stf_novo = stf_exist = stf_erro = 0
    
    for i, f in enumerate(stf_files, 1):
        try:
            result = upload_file(service, f, stf_id)
            if result == True:
                stf_novo += 1
            elif result == False:
                stf_exist += 1
            else:
                stf_erro += 1
            
            if i % 100 == 0 or i == len(stf_files):
                status = f"novo: {stf_novo}, exist: {stf_exist}"
                if stf_erro: status += f", erro: {stf_erro}"
                print(f"   [{i}/{len(stf_files)}] {status}")
        except:
            stf_erro += 1
    
    # Upload STJ
    print(f"\n📤 Upload STJ ({len(list(STJ_DIR.glob('*.pdf')))} arquivos)...")
    stj_files = sorted(STJ_DIR.glob("*.pdf"))
    stj_novo = stj_exist = stj_erro = 0
    
    for i, f in enumerate(stj_files, 1):
        try:
            result = upload_file(service, f, stj_id)
            if result == True:
                stj_novo += 1
            elif result == False:
                stj_exist += 1
            else:
                stj_erro += 1
            
            if i % 100 == 0 or i == len(stj_files):
                status = f"novo: {stj_novo}, exist: {stj_exist}"
                if stj_erro: status += f", erro: {stj_erro}"
                print(f"   [{i}/{len(stj_files)}] {status}")
        except:
            stj_erro += 1
    
    # Resumo
    print("\n" + "=" * 70)
    print("✅ UPLOAD FINALIZADO")
    print("=" * 70)
    print(f"\nSTF: {stf_novo} novo(s)")
    if stf_exist: print(f"     {stf_exist} já existente(s)")
    if stf_erro: print(f"     {stf_erro} erro(s)")
    
    print(f"\nSTJ: {stj_novo} novo(s)")
    if stj_exist: print(f"     {stj_exist} já existente(s)")
    if stj_erro: print(f"     {stj_erro} erro(s)")
    
    print(f"\n📍 Pasta no Drive: DOD - Informativos")
    print(f"📊 Total enviado: {stf_novo + stj_novo} arquivo(s)")
