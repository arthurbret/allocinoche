#!/usr/bin/env python3
"""
Script de nettoyage des fichiers dépréciés.
"""
import os
from pathlib import Path

# Fichiers à supprimer
DEPRECATED_FILES = [
    'ugc.py',
    'scrape_ugc_cinemas.py', 
    'scrape_ugc_showtimes.py',
    'explore_pathe.py',
    'explore_pathe_network.py',
    'check_config.py',
    'cleanup.py',
    'ugc_final_fixed.json'
]

def main():
    """Nettoie les fichiers dépréciés"""
    root = Path(__file__).parent
    
    print("🧹 Nettoyage des fichiers dépréciés...\n")
    
    removed = []
    not_found = []
    
    for filename in DEPRECATED_FILES:
        filepath = root / filename
        
        if filepath.exists():
            try:
                filepath.unlink()
                removed.append(filename)
                print(f"   ✅ Supprimé: {filename}")
            except Exception as e:
                print(f"   ❌ Erreur lors de la suppression de {filename}: {e}")
        else:
            not_found.append(filename)
            print(f"   ⏭️  Déjà absent: {filename}")
    
    print(f"\n📊 Résumé:")
    print(f"   - Fichiers supprimés: {len(removed)}")
    print(f"   - Fichiers déjà absents: {len(not_found)}")
    
    if removed:
        print(f"\n💡 Les fichiers suivants ont été supprimés car ils sont remplacés par la nouvelle architecture:")
        for f in removed:
            print(f"      - {f}")
        print(f"\n   Utilisez maintenant: python main.py --help")

if __name__ == "__main__":
    main()
