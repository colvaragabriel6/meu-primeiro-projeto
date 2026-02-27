#!/bin/bash

# Script de upload automatizado com rclone
# Este script configura e faz upload de informativos para Google Drive

set -e

echo "================================================================================"
echo "📤 UPLOAD DE INFORMATIVOS PARA GOOGLE DRIVE - rclone"
echo "================================================================================"

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretórios
BASE_DIR="/workspaces/meu-primeiro-projeto"
STF_DIR="$BASE_DIR/downloads/Informativos_STF"
STJ_DIR="$BASE_DIR/downloads/Informativos_STJ"

# Funções
check_rclone() {
    if ! command -v rclone &> /dev/null; then
        echo -e "${RED}❌ rclone não encontrado${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ rclone encontrado${NC}"
    return 0
}

check_gdrive_config() {
    if rclone listremotes 2>/dev/null | grep -qi "gdrive\|google"; then
        echo -e "${GREEN}✓ Google Drive já configurado${NC}"
        return 0
    fi
    return 1
}

setup_gdrive() {
    echo ""
    echo -e "${BLUE}📌 CONFIGURANDO GOOGLE DRIVE${NC}"
    echo ""
    echo "Será necessário autorizar o acesso via navegador."
    echo ""
    echo "Passos:"
    echo "  1. Será aberto um assistente de configuração"
    echo "  2. Digite 'gdrive' como nome"
    echo "  3. Selecione 'Google Drive' (opção 17 geralmente)"
    echo "  4. Deixe client_id e client_secret em branco (usar padrão)"
    echo "  5. Escolha '1' para 'Full access all files'"
    echo "  6. Digite 'n' para 'Use auto config?'"
    echo "  7. Siga o link no navegador, autorize e copie o código"
    echo "  8. Cole o código quando solicitado"
    echo ""
    read -p "Pressione ENTER para continuar..."
    
    rclone config
}

create_folders() {
    echo ""
    echo -e "${BLUE}📁 CRIANDO ESTRUTURA DE PASTAS${NC}"
    
    echo "  Criando pasta principal..."
    rclone mkdir gdrive:"DOD - Informativos" 2>/dev/null || true
    
    echo "  Criando pasta STF..."
    rclone mkdir gdrive:"DOD - Informativos/Informativos_STF" 2>/dev/null || true
    
    echo "  Criando pasta STJ..."
    rclone mkdir gdrive:"DOD - Informativos/Informativos_STJ" 2>/dev/null || true
    
    echo -e "${GREEN}✓ Pastas criadas/verificadas${NC}"
}

do_upload() {
    echo ""
    echo -e "${BLUE}📤 FAZENDO UPLOAD DOS INFORMATIVOS${NC}"
    echo ""
    
    STF_COUNT=$(find "$STF_DIR" -type f -name "*.pdf" 2>/dev/null | wc -l)
    STJ_COUNT=$(find "$STJ_DIR" -type f -name "*.pdf" 2>/dev/null | wc -l)
    TOTAL=$((STF_COUNT + STJ_COUNT))
    
    echo "📊 Resumo:"
    echo "  STF: $STF_COUNT arquivos"
    echo "  STJ: $STJ_COUNT arquivos"
    echo "  TOTAL: $TOTAL arquivos"
    echo ""
    
    # Upload STF
    echo "⏳ Upload STF..."
    rclone copy "$STF_DIR/" gdrive:"DOD - Informativos/Informativos_STF" \
        --progress --transfers 4 --stats 10s
    echo -e "${GREEN}✓ STF concluído${NC}"
    
    # Upload STJ
    echo ""
    echo "⏳ Upload STJ..."
    rclone copy "$STJ_DIR/" gdrive:"DOD - Informativos/Informativos_STJ" \
        --progress --transfers 4 --stats 10s
    echo -e "${GREEN}✓ STJ concluído${NC}"
    
    echo ""
    echo "================================================================================}"
    echo -e "${GREEN}✅ UPLOAD FINALIZADO COM SUCESSO!${NC}"
    echo "================================================================================}"
    echo ""
    echo "📍 Verifique em: https://drive.google.com"
    echo "📁 Pasta: DOD - Informativos"
    echo "📊 Total enviado: $TOTAL arquivos"
    echo ""
}

# Main
cd "$BASE_DIR"

# Verificações
check_rclone || exit 1

# Configurar se necessário
if ! check_gdrive_config; then
    setup_gdrive
fi

# Criar estrutura e fazer upload
create_folders
do_upload

echo "✓ Tudo pronto!"
