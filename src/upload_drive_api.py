#!/usr/bin/env python3
"""
Upload de informativos para Google Drive via API
Versão melhorada com autenticação robusta e recuperação de erros
"""
import os
import json
import time
from pathlib import Path
from typing import Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configurações
SCOPES = ['https://www.googleapis.com/auth/drive']
BASE_DIR = Path(__file__).parent.parent
CREDS_FILE = BASE_DIR / 'secrets/drive_token.json'
CLIENT_FILE = BASE_DIR / 'secrets/oauth_client.json'
DOWNLOADS = BASE_DIR / "downloads"
STF_DIR = DOWNLOADS / "Informativos_STF"
STJ_DIR = DOWNLOADS / "Informativos_STJ"

class GoogleDriveUploader:
    def __init__(self):
        self.service = None
        self.folder_ids = {}
        
    def autenticar(self) -> bool:
        """Autentica com Google Drive API"""
        try:
            creds = None
            
            # Carregar token existente se houver
            if os.path.exists(CREDS_FILE):
                try:
                    creds = Credentials.from_authorized_user_file(str(CREDS_FILE), SCOPES)
                    if creds.expired and creds.refresh_token:
                        print("🔄 Atualizando token expirado...")
                        creds.refresh(Request())
                    print("✓ Token carregado com sucesso")
                    self.service = build('drive', 'v3', credentials=creds)
                    return True
                except Exception as e:
                    print(f"⚠️  Token inválido/expirado: {str(e)[:50]}")
                    print("   Removendo token para nova autenticação...")
                    try:
                        os.remove(CREDS_FILE)
                    except:
                        pass
            
            # Se não houver token, fazer OAuth
            if not os.path.exists(CLIENT_FILE):
                print("❌ Arquivo oauth_client.json não encontrado!")
                print(f"   Coloque em: {CLIENT_FILE}")
                return False
            
            print("🔐 Iniciando fluxo OAuth (Out-of-Band)...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_FILE), 
                SCOPES
            )
            
            # Gerar URL de autorização
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            print("\n" + "="*70)
            print("1️⃣  Abra este link no seu navegador:")
            print("="*70)
            print(auth_url)
            print("="*70)
            print("\n2️⃣  Autorize o acesso ao seu Google Drive")
            print("3️⃣  Copie o código de autorização exibido")
            print("\n")
            
            # Aguardar código
            code = input("📋 Cole o código de autorização aqui: ").strip()
            
            if not code:
                print("❌ Código não fornecido")
                return False
            
            # Trocar código por credenciais
            creds = flow.fetch_token(code=code)
            
            # Salvar token para próximo uso
            with open(CREDS_FILE, 'w') as token:
                token.write(creds.to_json())
            print("✓ Token salvo com sucesso")
            
            self.service = build('drive', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            print(f"❌ Erro de autenticação: {e}")
            return False
    
    def criar_pasta(self, nome: str, pasta_pai: Optional[str] = None) -> Optional[str]:
        """Cria pasta no Google Drive"""
        try:
            file_metadata = {
                'name': nome,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if pasta_pai:
                file_metadata['parents'] = [pasta_pai]
            
            result = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            return result.get('id')
        except HttpError as e:
            print(f"❌ Erro ao criar pasta '{nome}': {e}")
            return None
    
    def buscar_pasta(self, nome: str) -> Optional[str]:
        """Procura pasta existente por nome"""
        try:
            query = f"name='{nome}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            items = results.get('files', [])
            return items[0]['id'] if items else None
        except Exception as e:
            print(f"⚠️  Erro ao buscar pasta '{nome}': {e}")
            return None
    
    def preparar_estrutura(self) -> bool:
        """Prepara estrutura de pastas"""
        print("\n📁 Preparando estrutura de pastas...")
        
        # Pasta principal
        pasta_principal = self.buscar_pasta('DOD - Informativos')
        if pasta_principal:
            print(f"✓ Pasta 'DOD - Informativos' encontrada")
            self.folder_ids['main'] = pasta_principal
        else:
            print("  Criando pasta 'DOD - Informativos'...")
            pasta_principal = self.criar_pasta('DOD - Informativos')
            if not pasta_principal:
                return False
            print(f"  ✓ Criada")
            self.folder_ids['main'] = pasta_principal
        
        # Subpasta STF
        stf_pasta = self.buscar_pasta('Informativos_STF')
        if stf_pasta:
            print(f"✓ Pasta 'Informativos_STF' encontrada")
            self.folder_ids['stf'] = stf_pasta
        else:
            print("  Criando pasta 'Informativos_STF'...")
            stf_pasta = self.criar_pasta('Informativos_STF', pasta_principal)
            if not stf_pasta:
                return False
            print(f"  ✓ Criada")
            self.folder_ids['stf'] = stf_pasta
        
        # Subpasta STJ
        stj_pasta = self.buscar_pasta('Informativos_STJ')
        if stj_pasta:
            print(f"✓ Pasta 'Informativos_STJ' encontrada")
            self.folder_ids['stj'] = stj_pasta
        else:
            print("  Criando pasta 'Informativos_STJ'...")
            stj_pasta = self.criar_pasta('Informativos_STJ', pasta_principal)
            if not stj_pasta:
                return False
            print(f"  ✓ Criada")
            self.folder_ids['stj'] = stj_pasta
        
        return True
    
    def fazer_upload(self, filepath: Path, pasta_id: str) -> bool:
        """Faz upload de arquivo para pasta específica"""
        try:
            file_metadata = {
                'name': filepath.name,
                'parents': [pasta_id]
            }
            media = MediaFileUpload(
                str(filepath),
                resumable=True,
                chunksize=5242880  # 5MB chunks
            )
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )
            
            response = None
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        # Mostrar progresso silenciosamente
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        print(f"  ⚠️  Erro temporário em {filepath.name}, tentando novamente...")
                        time.sleep(2)
                        continue
                    raise
            
            return True
        except Exception as e:
            print(f"❌ Erro ao fazer upload de {filepath.name}: {e}")
            return False
    
    def fazer_upload_lote(self, arquivos: list, pasta_id: str, tipo: str) -> Tuple[int, int]:
        """Faz upload de um lote de arquivos"""
        sucesso = 0
        erro = 0
        total = len(arquivos)
        
        for i, arquivo in enumerate(arquivos, 1):
            if self.fazer_upload(arquivo, pasta_id):
                sucesso += 1
            else:
                erro += 1
            
            # Mostrar progresso a cada 50 arquivos
            if i % 50 == 0 or i == total:
                percent = int((i / total) * 100)
                print(f"  {tipo}: {i}/{total} ({percent}%)")
                time.sleep(1)  # Pequena pausa para não sobrecarregar a API
        
        return sucesso, erro
    
    def executar(self) -> bool:
        """Executa o upload completo"""
        print("=" * 60)
        print("📤 UPLOAD DE INFORMATIVOS PARA GOOGLE DRIVE")
        print("=" * 60)
        
        # Autenticar
        print("\n🔐 Autenticando com Google Drive...")
        if not self.autenticar():
            return False
        print("✓ Autenticado com sucesso\n")
        
        # Preparar estrutura
        if not self.preparar_estrutura():
            print("❌ Erro ao preparar estrutura de pastas")
            return False
        
        # Upload STF
        print(f"\n📤 Fazendo upload de informativos STF...")
        stf_files = sorted(STF_DIR.glob("*.pdf"))
        if not stf_files:
            print("⚠️  Nenhum arquivo STF encontrado em", STF_DIR)
        else:
            stf_sucesso, stf_erro = self.fazer_upload_lote(
                stf_files,
                self.folder_ids['stf'],
                'STF'
            )
        
        # Upload STJ
        print(f"\n📤 Fazendo upload de informativos STJ...")
        stj_files = sorted(STJ_DIR.glob("*.pdf"))
        if not stj_files:
            print("⚠️  Nenhum arquivo STJ encontrado em", STJ_DIR)
        else:
            stj_sucesso, stj_erro = self.fazer_upload_lote(
                stj_files,
                self.folder_ids['stj'],
                'STJ'
            )
        
        # Resumo
        print("\n" + "=" * 60)
        print("✅ RESUMO DO UPLOAD")
        print("=" * 60)
        print(f"STF: {stf_sucesso}/{len(stf_files)} enviados")
        if stf_erro > 0:
            print(f"     {stf_erro} erros")
        print(f"STJ: {stj_sucesso}/{len(stj_files)} enviados")
        if stj_erro > 0:
            print(f"     {stj_erro} erros")
        total_enviados = (stf_sucesso if stf_files else 0) + (stj_sucesso if stj_files else 0)
        total_arquivos = len(stf_files) + len(stj_files)
        print(f"TOTAL: {total_enviados}/{total_arquivos}")
        print(f"\n📍 Pasta: DOD - Informativos")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    uploader = GoogleDriveUploader()
    sucesso = uploader.executar()
    exit(0 if sucesso else 1)
