#!/usr/bin/env python3
"""
Script para analisar sequência numérica e identificar faltantes
"""

from pathlib import Path
import re

DOWNLOADS_DIR = Path("downloads")


def analisar_sequencia():
    """Analisa sequência numérica de informativos"""
    
    stj_folder = DOWNLOADS_DIR / "Informativos_STJ"
    stf_folder = DOWNLOADS_DIR / "Informativos_STF"
    
    # Coleta informativos
    stj_nums = set()
    stf_nums = set()
    
    if stj_folder.exists():
        for file in stj_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+)-stj", file.name, re.IGNORECASE)
            if match:
                stj_nums.add(int(match.group(1)))
    
    if stf_folder.exists():
        for file in stf_folder.glob("*.pdf"):
            match = re.search(r"info-(\d+)-stf", file.name, re.IGNORECASE)
            if match:
                stf_nums.add(int(match.group(1)))
    
    print("\n" + "="*80)
    print("🔢 ANÁLISE DE SEQUÊNCIA NUMÉRICA DE INFORMATIVOS")
    print("="*80)
    
    # Análise STJ
    print("\n" + "─"*80)
    print("🏛️  INFORMATIVOS STJ")
    print("─"*80)
    
    if stj_nums:
        stj_sorted = sorted(stj_nums)
        min_stj = min(stj_sorted)
        max_stj = max(stj_sorted)
        
        print(f"\n📊 Resumo STJ:")
        print(f"   • Menor: {min_stj}")
        print(f"   • Maior: {max_stj}")
        print(f"   • Total coletado: {len(stj_nums)}")
        print(f"   • Esperado (se contínuo): {max_stj - min_stj + 1}")
        
        # Identifica faltantes
        faltantes_stj = []
        for i in range(min_stj, max_stj + 1):
            if i not in stj_nums:
                faltantes_stj.append(i)
        
        print(f"\n⚠️  Informativos faltando: {len(faltantes_stj)}")
        
        if faltantes_stj:
            print(f"\n   Números faltantes:")
            # Agrupa em ranges contínuos
            ranges = []
            start = faltantes_stj[0]
            end = faltantes_stj[0]
            
            for num in faltantes_stj[1:]:
                if num == end + 1:
                    end = num
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = num
                    end = num
            
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            
            # Exibe ranges
            for i, r in enumerate(ranges):
                print(f"   • Info-{r}-STJ", end="")
                if (i + 1) % 3 == 0:
                    print()
                else:
                    print("  |  ", end="")
            if len(ranges) % 3 != 0:
                print()
        else:
            print("\n   ✅ SEQUÊNCIA COMPLETA - Todos os informativos STJ foram coletados!")
        
        print(f"\n📈 Taxa de cobertura STJ: {len(stj_nums) / (max_stj - min_stj + 1) * 100:.1f}%")
    
    # Análise STF
    print("\n" + "─"*80)
    print("🏛️  INFORMATIVOS STF")
    print("─"*80)
    
    if stf_nums:
        stf_sorted = sorted(stf_nums)
        min_stf = min(stf_sorted)
        max_stf = max(stf_sorted)
        
        print(f"\n📊 Resumo STF:")
        print(f"   • Menor: {min_stf}")
        print(f"   • Maior: {max_stf}")
        print(f"   • Total coletado: {len(stf_nums)}")
        print(f"   • Esperado (se contínuo): {max_stf - min_stf + 1}")
        
        # Identifica faltantes
        faltantes_stf = []
        for i in range(min_stf, max_stf + 1):
            if i not in stf_nums:
                faltantes_stf.append(i)
        
        print(f"\n⚠️  Informativos faltando: {len(faltantes_stf)}")
        
        if faltantes_stf:
            print(f"\n   Números faltantes:")
            # Agrupa em ranges contínuos
            ranges = []
            start = faltantes_stf[0]
            end = faltantes_stf[0]
            
            for num in faltantes_stf[1:]:
                if num == end + 1:
                    end = num
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = num
                    end = num
            
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            
            # Exibe ranges
            for i, r in enumerate(ranges):
                print(f"   • Info-{r}-STF", end="")
                if (i + 1) % 3 == 0:
                    print()
                else:
                    print("  |  ", end="")
            if len(ranges) % 3 != 0:
                print()
        else:
            print("\n   ✅ SEQUÊNCIA COMPLETA - Todos os informativos STF foram coletados!")
        
        print(f"\n📈 Taxa de cobertura STF: {len(stf_nums) / (max_stf - min_stf + 1) * 100:.1f}%")
    
    # Resumo geral
    print("\n" + "="*80)
    print("📋 RESUMO GERAL")
    print("="*80)
    
    stj_cobertura = len(stj_nums) / (max_stj - min_stj + 1) * 100 if stj_nums else 0
    stf_cobertura = len(stf_nums) / (max_stf - min_stf + 1) * 100 if stf_nums else 0
    
    total_faltantes = len(faltantes_stj) + len(faltantes_stf) if stj_nums and stf_nums else 0
    
    print(f"\n📊 Estatísticas finais:")
    print(f"   STJ: {stj_cobertura:.1f}% de cobertura ({len(faltantes_stj)} faltando)")
    print(f"   STF: {stf_cobertura:.1f}% de cobertura ({len(faltantes_stf)} faltando)")
    print(f"   Total: {total_faltantes} informativos ainda não coletados")
    
    if stj_cobertura == 100 and stf_cobertura == 100:
        print(f"\n✅ TUDO COMPLETO! Todas as sequências foram completamente raspadas!")
    else:
        print(f"\n⚠️  Ainda faltam informativos para completar a cobertura")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    analisar_sequencia()
