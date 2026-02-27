#!/usr/bin/env python3
"""
Script mais simples para verificar a cobertura local de informativos
Conta os arquivos locais de 2024 e 2025
"""

from pathlib import Path
import re

DOWNLOADS_DIR = Path("downloads")
INFORMATIVO_PATTERN = re.compile(r"info-(\d+)-(stj|stf)", re.IGNORECASE)


def extrair_ano_do_arquivo(filename: str) -> str:
    """Tenta extrair ano do nome do arquivo"""
    match = re.search(r"(202[0-9])", filename)
    if match:
        return match.group(1)
    return "desconhecido"


def contar_informativos():
    """Conta informativos locais por ano e tribunal"""
    
    print("\n" + "="*70)
    print("📊 ESTATÍSTICAS DE INFORMATIVOS LOCAIS")
    print("="*70 + "\n")
    
    # Coleta arquivos do STJ
    stj_folder = DOWNLOADS_DIR / "Informativos_STJ"
    stf_folder = DOWNLOADS_DIR / "Informativos_STF"
    
    informativos_2024 = {"STJ": set(), "STF": set()}
    informativos_2025 = {"STJ": set(), "STF": set()}
    
    # Processa STJ
    if stj_folder.exists():
        print("📁 Processando Informativos_STJ...")
        for file in stj_folder.glob("*.pdf"):
            match = INFORMATIVO_PATTERN.search(file.name)
            if match:
                num, tribunal = match.groups()
                
                # Tenta extrair ano do nome (padrão: info-XXX-STJ.pdf)
                # Se não tiver, assume que é arquivo não nomeado com ano
                # Vamos verificar a estrutura real
                
                # Adiciona sem duplicatas (só o número)
                info_id = int(num)
                
                # Heurística: informativos de STJ costumam ter números menores
                # STJ: >800, STF: >1100 (típico)
                # Mas como não temos info do ano no nome, vamos contar todos
                informativos_2024["STJ"].add(info_id)
    
    # Processa STF
    if stf_folder.exists():
        print("📁 Processando Informativos_STF...")
        for file in stf_folder.glob("*.pdf"):
            match = INFORMATIVO_PATTERN.search(file.name)
            if match:
                num, tribunal = match.groups()
                info_id = int(num)
                informativos_2024["STF"].add(info_id)
    
    # Resumo
    print("\n" + "─"*70)
    print("📋 RESUMO DE INFORMATIVOS COLETADOS")
    print("─"*70)
    
    stj_count = len(informativos_2024["STJ"])
    stf_count = len(informativos_2024["STF"])
    
    print(f"\n📌 Informativos STJ: {stj_count}")
    if informativos_2024["STJ"]:
        nums = sorted(informativos_2024["STJ"])
        print(f"   Range: {min(nums)} a {max(nums)}")
        print(f"   Primeiros 10: {sorted(nums)[:10]}")
        print(f"   Últimos 10:  {sorted(nums)[-10:]}")
    
    print(f"\n📌 Informativos STF: {stf_count}")
    if informativos_2024["STF"]:
        nums = sorted(informativos_2024["STF"])
        print(f"   Range: {min(nums)} a {max(nums)}")
        print(f"   Primeiros 10: {sorted(nums)[:10]}")
        print(f"   Últimos 10:  {sorted(nums)[-10:]}")
    
    # Análise de duplicatas
    print("\n" + "─"*70)
    print("🔍 ANÁLISE DE ARQUIVOS")
    print("─"*70)
    
    if stj_folder.exists():
        stj_files = list(stj_folder.glob("*.pdf"))
        stj_versioned = [f for f in stj_files if "_v" in f.name]
        print(f"\nInformativos_STJ:")
        print(f"  • Total de arquivos: {len(stj_files)}")
        print(f"  • Arquivos versioned (_vX): {len(stj_versioned)}")
        print(f"  • Informativos únicos: {stj_count}")
    
    if stf_folder.exists():
        stf_files = list(stf_folder.glob("*.pdf"))
        stf_versioned = [f for f in stf_files if "_v" in f.name]
        print(f"\nInformativos_STF:")
        print(f"  • Total de arquivos: {len(stf_files)}")
        print(f"  • Arquivos versioned (_vX): {len(stf_versioned)}")
        print(f"  • Informativos únicos: {stf_count}")
    
    print("\n" + "="*70 + "\n")
    
    # Recomendações
    print("💡 NOTAS:")
    print("  • Como a página do blog não expõe lista HTML direta,")
    print("    a verificação precisa ser feita pelo site principal.")
    print("  • Recomenda-se acessar https://www.dizerodireito.com.br")
    print("    e verificar manualmente a seção de informativos.")
    print()


if __name__ == "__main__":
    contar_informativos()
