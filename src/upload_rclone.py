#!/usr/bin/env python3
"""
Upload automatizado de informativos para Google Drive usando rclone
"""
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DOWNLOADS = BASE_DIR / "downloads"
STF_DIR = DOWNLOADS / "Informativos_STF"
STJ_DIR = DOWNLOADS / "Informativos_STJ"

def run_command(cmd, description=""):
    """Executa comando shell"""
    try:
        if description:
            print(f"\n{description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erro: {result.stderr}")
            return False
        if result.stdout:
            print(result.stdout.strip())
        return True
    except Exception as e:
        print(f"❌ Erro ao executar: {e}")
        return False

def check_rclone():
    """Verifica se rclone está instalado"""
    result = subprocess.run("which rclone", shell=True, capture_output=True)
    return result.returncode == 0

def check_google_drive_config():
    """Verifica se Google Drive está configurado no rclone"""
    result = subprocess.run("rclone listremotes", shell=True, capture_output=True, text=True)
    return 'gdrive' in result.stdout or 'Google' in result.stdout.lower()

def setup_google_drive():
    """Configura Google Drive no rclone interativamente"""
    print("\n" + "=" * 80)
    print("⚙️  CONFIGURANDO GOOGLE DRIVE")
    print("=" * 80)
    print("""
Será aberto um assistente de configuração.

Passos a seguir:
  1. Escolha um nome remoto (exemplo: gdrive)
  2. Selecione "Google Drive"
  3. Deixe em branco quando pedir client_id (use padrão do rclone)
  4. Deixe em branco quando pedir client_secret
  5. Escolha "1 - Full access all files"
  6. Digite "N" quando perguntar "Use auto config?" (vamos usar manual)
  7. Siga o link que aparecer, autorize, copie o código
  8. Cole o código quando pedido

Pode começar? (Enter para continuar)
""")
    input()
    
    # Executar configuração
    os.system("rclone config")
    
    # Verificar se funcionou
    if check_google_drive_config():
        print("✓ Google Drive configurado com sucesso!")
        return True
    else:
        print("❌ Falha na configuração")
        return False

def create_folder_structure():
    """Cria estrutura de pastas no Google Drive"""
    print("\n" + "=" * 80)
    print("📁 CRIANDO ESTRUTURA DE PASTAS")
    print("=" * 80)
    
    commands = [
        ('rclone mkdir gdrive:"DOD - Informativos"', "Criando pasta principal"),
        ('rclone mkdir gdrive:"DOD - Informativos/Informativos_STF"', "Criando pasta STF"),
        ('rclone mkdir gdrive:"DOD - Informativos/Informativos_STJ"', "Criando pasta STJ"),
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    
    return True

def do_upload():
    """Faz upload dos informativos"""
    print("\n" + "=" * 80)
    print("📤 FAZENDO UPLOAD DOS INFORMATIVOS")
    print("=" * 80)
    
    stf_files = len(list(STF_DIR.glob("*.pdf")))
    stj_files = len(list(STJ_DIR.glob("*.pdf")))
    
    print(f"\n📊 Resumo:")
    print(f"  STF: {stf_files} arquivos")
    print(f"  STJ: {stj_files} arquivos")
    print(f"  TOTAL: {stf_files + stj_files} arquivos")
    
    # Upload STF
    print(f"\n📤 Upload STF ({stf_files} arquivos)...")
    cmd_stf = f'rclone copy "{STF_DIR}/" gdrive:"DOD - Informativos/Informativos_STF" -P --transfers 4'
    if not run_command(cmd_stf, "Enviando arquivos STF"):
        return False
    
    # Upload STJ
    print(f"\n📤 Upload STJ ({stj_files} arquivos)...")
    cmd_stj = f'rclone copy "{STJ_DIR}/" gdrive:"DOD - Informativos/Informativos_STJ" -P --transfers 4'
    if not run_command(cmd_stj, "Enviando arquivos STJ"):
        return False
    
    return True

def main():
    """Main"""
    print("\n" + "=" * 80)
    print("📤 UPLOAD DE INFORMATIVOS PARA GOOGLE DRIVE - rclone")
    print("=" * 80)
    
    # Verificar rclone
    print("\n🔍 Verificando rclone...")
    if not check_rclone():
        print("❌ rclone não está instalado")
        print("Instale com: curl https://rclone.org/install.sh | sudo bash")
        sys.exit(1)
    
    print("✓ rclone encontrado")
    
    # Verificar Google Drive configurado
    print("\n🔍 Verificando configuração do Google Drive...")
    if not check_google_drive_config():
        print("❌ Google Drive não está configurado")
        if not setup_google_drive():
            print("❌ Falha na configuração do Google Drive")
            sys.exit(1)
    else:
        print("✓ Google Drive já configurado")
    
    # Criar estrutura
    if not create_folder_structure():
        print("❌ Erro ao criar estrutura de pastas")
        # Continuar mesmo se falhar (pastas podem já existir)
        print("⚠️  Continuando... (as pastas podem já existir)")
    
    # Fazer upload
    if not do_upload():
        print("❌ Erro no upload")
        sys.exit(1)
    
    # Sucesso
    print("\n" + "=" * 80)
    print("✅ UPLOAD CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    print(f"\n📍 Verificar em: https://drive.google.com")
    print(f"📁 Pasta: DOD - Informativos")
    print(f"\n✓ {stf_files + stj_files} arquivos enviados")

if __name__ == "__main__":
    main()
