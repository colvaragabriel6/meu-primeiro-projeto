#!/usr/bin/env python3
"""
Script para corrigir arquivos do STF que foram armazenados erroneamente em Informativos_STJ
"""

import re
from pathlib import Path
import shutil

DOWNLOADS_DIR = Path("downloads")

# Padrões para identificar STF
STF_PATTERNS = [
    re.compile(r"\bstf\b", re.IGNORECASE),
    re.compile(r"info-\d+-stf", re.IGNORECASE),  # padrão como "info-1161-stf"
]

STJ_PATTERNS = [
    re.compile(r"\bstj\b", re.IGNORECASE),
    re.compile(r"info-\d+-stj", re.IGNORECASE),  # padrão como "info-834-stj"
]


def is_stf_file(filename: str) -> bool:
    """Verifica se o arquivo é do STF"""
    for pattern in STF_PATTERNS:
        if pattern.search(filename):
            return True
    return False


def is_stj_file(filename: str) -> bool:
    """Verifica se o arquivo é do STJ"""
    for pattern in STJ_PATTERNS:
        if pattern.search(filename):
            return True
    return False


def corrigir_informativos():
    """Corrige arquivos mal classificados"""
    
    stj_folder = DOWNLOADS_DIR / "Informativos_STJ"
    stf_folder = DOWNLOADS_DIR / "Informativos_STF"
    stf_folder.mkdir(exist_ok=True, parents=True)
    
    if not stj_folder.exists():
        print("❌ Pasta Informativos_STJ não encontrada!")
        return
    
    print("🔍 Procurando arquivos do STF na pasta do STJ...\n")
    
    moved_count = 0
    files_list = list(stj_folder.glob("*.pdf"))
    
    for file in files_list:
        filename = file.name
        
        # Se tem padrão de STF mas está em STJ
        if is_stf_file(filename):
            dest = stf_folder / filename
            
            # Se já existe na pasta STF, renomeia
            if dest.exists():
                name, ext = filename.rsplit(".", 1)
                counter = 1
                while (stf_folder / f"{name}_v{counter}.{ext}").exists():
                    counter += 1
                dest = stf_folder / f"{name}_v{counter}.{ext}"
            
            print(f"📤 Movendo para STF: {filename}")
            shutil.move(str(file), str(dest))
            moved_count += 1
    
    print(f"\n✅ Correção concluída!")
    print(f"   {moved_count} arquivo(s) movido(s) para Informativos_STF")
    
    # Estatísticas finais
    print("\n📊 Estatísticas finais:")
    stj_count = len(list(stj_folder.glob("*.pdf")))
    stf_count = len(list(stf_folder.glob("*.pdf")))
    
    print(f"   Informativos_STJ: {stj_count} arquivos")
    print(f"   Informativos_STF: {stf_count} arquivos")


if __name__ == "__main__":
    corrigir_informativos()
