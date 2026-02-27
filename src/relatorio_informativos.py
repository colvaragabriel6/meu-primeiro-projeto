#!/usr/bin/env python3
"""
Relatório detalhado dos informativos coletados
"""

from pathlib import Path
import re

DOWNLOADS_DIR = Path("downloads")

def gerar_relatorio():
    """Gera relatório detalhado"""
    
    stj_folder = DOWNLOADS_DIR / "Informativos_STJ"
    stf_folder = DOWNLOADS_DIR / "Informativos_STF"
    
    # Coleta informativos STJ
    stj_nums = set()
    if stj_folder.exists():
        for file in stj_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+)-stj", file.name, re.IGNORECASE)
            if match:
                stj_nums.add(int(match.group(1)))
    
    # Coleta informativos STF
    stf_nums = set()
    if stf_folder.exists():
        for file in stf_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+)-stf", file.name, re.IGNORECASE)
            if match:
                stf_nums.add(int(match.group(1)))
    
    print("\n" + "="*70)
    print("📊 RELATÓRIO DE COBERTURA DE INFORMATIVOS")
    print("="*70)
    
    print("\n🏛️  INFORMATIVOS DO STJ")
    print("─"*70)
    if stj_nums:
        nums_sorted = sorted(stj_nums)
        print(f"Total coletado: {len(nums_sorted)} informativos")
        print(f"Range: {min(nums_sorted)} a {max(nums_sorted)}")
        
        # Verifica gaps
        gaps = []
        for i in range(min(nums_sorted), max(nums_sorted)):
            if i not in stj_nums:
                gaps.append(i)
        
        if gaps and len(gaps) <= 20:
            print(f"\n⚠️  Gaps identificados ({len(gaps)}):")
            for gap in gaps[:20]:
                print(f"   • Info-{gap}-STJ faltando")
            if len(gaps) > 20:
                print(f"   ... e mais {len(gaps) - 20}")
        elif gaps:
            print(f"\n⚠️  {len(gaps)} informativos com gaps")
    
    print("\n🏛️  INFORMATIVOS DO STF")
    print("─"*70)
    if stf_nums:
        nums_sorted = sorted(stf_nums)
        print(f"Total coletado: {len(nums_sorted)} informativos")
        print(f"Range: {min(nums_sorted)} a {max(nums_sorted)}")
        
        # Verifica gaps
        gaps = []
        for i in range(min(nums_sorted), max(nums_sorted)):
            if i not in stf_nums:
                gaps.append(i)
        
        if gaps and len(gaps) <= 20:
            print(f"\n⚠️  Gaps identificados ({len(gaps)}):")
            for gap in gaps[:20]:
                print(f"   • Info-{gap}-STF faltando")
            if len(gaps) > 20:
                print(f"   ... e mais {len(gaps) - 20}")
        elif gaps:
            print(f"\n⚠️  {len(gaps)} informativos com gaps")
    
    # Estatísticas gerais
    print("\n" + "─"*70)
    print("📈 RESUMO GERAL")
    print("─"*70)
    
    stj_files = list((DOWNLOADS_DIR / "Informativos_STJ").glob("*.pdf")) if (DOWNLOADS_DIR / "Informativos_STJ").exists() else []
    stf_files = list((DOWNLOADS_DIR / "Informativos_STF").glob("*.pdf")) if (DOWNLOADS_DIR / "Informativos_STF").exists() else []
    
    print(f"\nArquivos STJ:")
    print(f"  • Total de arquivos: {len(stj_files)}")
    print(f"  • Informativos únicos: {len(stj_nums)}")
    print(f"  • Taxa de duplicação: {len(stj_files) / len(stj_nums) if stj_nums else 0:.2f}x")
    
    print(f"\nArquivos STF:")
    print(f"  • Total de arquivos: {len(stf_files)}")
    print(f"  • Informativos únicos: {len(stf_nums)}")
    print(f"  • Taxa de duplicação: {len(stf_files) / len(stf_nums) if stf_nums else 0:.2f}x")
    
    print(f"\nTotal geral:")
    print(f"  • Arquivos: {len(stj_files) + len(stf_files)}")
    print(f"  • Informativos únicos: {len(stj_nums) + len(stf_nums)}")
    
    # Instruções para verificação manual
    print("\n" + "="*70)
    print("🔍 COMO VERIFICAR COMPLETUDE NO SITE")
    print("="*70)
    
    print("\n1. Acesse https://www.dizerodireito.com.br")
    print("\n2. Navegue para o arquivo de cada ano:")
    print("   • https://www.dizerodireito.com.br/2024/")
    print("   • https://www.dizerodireito.com.br/2025/")
    print("\n3. Procure por:")
    print("   • 'Informativos STJ' - deverá ter informativos numerados")
    print("   • 'Informativos STF' - deverá ter informativos numerados")
    print("\n4. Conte os informativos disponíveis e compare com o relatório acima")
    print("\n💡 NOTA: O script de raspagem (aula5_2024_baixar_site.py) foi")
    print("   configurado para coletar todos da página /2024/ e /2025/")
    print("   A completude depende do que estava disponível no momento")
    print("   de execução do script.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    gerar_relatorio()
