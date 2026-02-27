#!/usr/bin/env python3
"""
Script para reorganizar arquivos baixados conforme requisitos:
- Informativos_STJ: todos em uma pasta (sem subpastas por ano)
- Informativos_STF: todos em uma pasta (sem subpastas por ano)
- OUTROS: com subpastas por ano (Revisões, Alterações, etc.)
"""

import os
import re
import shutil
from pathlib import Path

DOWNLOADS_DIR = Path("downloads")
YEAR_PATTERN = re.compile(r"(19|20)\d{2}")


def extract_year_from_filename(filename: str) -> str:
    """Tenta extrair ano do nome do arquivo"""
    match = YEAR_PATTERN.search(filename)
    if match:
        return match.group(0)
    return "2024"  # fallback


def reorganize():
    """Reorganiza a estrutura de arquivos"""
    
    print("🔄 Iniciando reorganização de arquivos...\n")
    
    # 1. Reorganizar Informativos_STJ
    print("📂 Processando Informativos_STJ...")
    stj_base = DOWNLOADS_DIR / "Informativos_STJ"
    if stj_base.exists():
        # Move todos os arquivos das subpastas para a raiz de Informativos_STJ
        for year_folder in stj_base.iterdir():
            if year_folder.is_dir():
                year = year_folder.name
                print(f"  ├─ Movendo arquivos de {year}...")
                for file in year_folder.iterdir():
                    if file.is_file():
                        dest = stj_base / file.name
                        # Se já existe, adiciona sufixo
                        if dest.exists():
                            name, ext = os.path.splitext(file.name)
                            dest = stj_base / f"{name}_{year}{ext}"
                        shutil.move(str(file), str(dest))
                        print(f"    ✓ {file.name}")
                # Remove pasta vazia
                year_folder.rmdir()
                print(f"  └─ Pasta {year} removida")
    
    # 2. Reorganizar Informativos_STF
    print("\n📂 Processando Informativos_STF...")
    stf_base = DOWNLOADS_DIR / "Informativos_STF"
    if stf_base.exists():
        for year_folder in stf_base.iterdir():
            if year_folder.is_dir():
                year = year_folder.name
                print(f"  ├─ Movendo arquivos de {year}...")
                for file in year_folder.iterdir():
                    if file.is_file():
                        dest = stf_base / file.name
                        if dest.exists():
                            name, ext = os.path.splitext(file.name)
                            dest = stf_base / f"{name}_{year}{ext}"
                        shutil.move(str(file), str(dest))
                        print(f"    ✓ {file.name}")
                year_folder.rmdir()
                print(f"  └─ Pasta {year} removida")
    
    # 3. Reorganizar Revisões e outros em OUTROS/ANO
    print("\n📂 Processando outras categorias...")
    
    # Criar pasta OUTROS
    outros_base = DOWNLOADS_DIR / "OUTROS"
    outros_base.mkdir(exist_ok=True)
    
    # Mover Revisões
    revisoes_folder = DOWNLOADS_DIR / "Revisoes"
    if revisoes_folder.exists():
        print("  ├─ Movendo Revisões...")
        for file in revisoes_folder.iterdir():
            if file.is_file():
                year = extract_year_from_filename(file.name)
                year_folder = outros_base / year
                year_folder.mkdir(exist_ok=True)
                dest = year_folder / file.name
                if dest.exists():
                    name, ext = os.path.splitext(file.name)
                    dest = year_folder / f"{name}_v2{ext}"
                shutil.move(str(file), str(dest))
                print(f"    ✓ {file.name} → OUTROS/{year}/")
        revisoes_folder.rmdir()
        print("  └─ Pasta Revisões removida")
    
    # Mover Alterações_Legislativas (se existir)
    alter_folder = DOWNLOADS_DIR / "Alteracoes_Legislativas"
    if alter_folder.exists():
        print("  ├─ Movendo Alterações Legislativas...")
        for file in alter_folder.iterdir():
            if file.is_file():
                year = extract_year_from_filename(file.name)
                year_folder = outros_base / year
                year_folder.mkdir(exist_ok=True)
                dest = year_folder / file.name
                if dest.exists():
                    name, ext = os.path.splitext(file.name)
                    dest = year_folder / f"{name}_v2{ext}"
                shutil.move(str(file), str(dest))
                print(f"    ✓ {file.name} → OUTROS/{year}/")
        alter_folder.rmdir()
        print("  └─ Pasta Alterações_Legislativas removida")
    
    # Mover Materiais_Diversos (se existir)
    materiais_folder = DOWNLOADS_DIR / "Materiais_Diversos"
    if materiais_folder.exists():
        print("  ├─ Movendo Materiais Diversos...")
        for file in materiais_folder.iterdir():
            if file.is_file():
                year = extract_year_from_filename(file.name)
                year_folder = outros_base / year
                year_folder.mkdir(exist_ok=True)
                dest = year_folder / file.name
                if dest.exists():
                    name, ext = os.path.splitext(file.name)
                    dest = year_folder / f"{name}_v2{ext}"
                shutil.move(str(file), str(dest))
                print(f"    ✓ {file.name} → OUTROS/{year}/")
        materiais_folder.rmdir()
        print("  └─ Pasta Materiais_Diversos removida")
    
    # 4. Exibir estrutura final
    print("\n" + "="*50)
    print("✅ REORGANIZAÇÃO CONCLUÍDA!")
    print("="*50)
    
    print("\n📊 Estrutura final:")
    print("\nInfomativos_STJ:")
    stj_files = list((DOWNLOADS_DIR / "Informativos_STJ").glob("*.pdf"))
    print(f"  └─ {len(stj_files)} arquivos")
    
    print("\nInformativos_STF:")
    stf_files = list((DOWNLOADS_DIR / "Informativos_STF").glob("*.pdf"))
    print(f"  └─ {len(stf_files)} arquivos")
    
    print("\nOUTROS (por ano):")
    if outros_base.exists():
        for year_folder in sorted(outros_base.iterdir()):
            if year_folder.is_dir():
                files = list(year_folder.glob("*.pdf"))
                print(f"  ├─ {year_folder.name}: {len(files)} arquivos")
    
    print("\n✨ Pronto para usar!")


if __name__ == "__main__":
    reorganize()
