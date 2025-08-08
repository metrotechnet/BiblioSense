#!/usr/bin/env python3
"""
🧹 Script de nettoyage pour le dossier tests/
============================================

Ce script supprime les anciens fichiers de test qui ne font pas partie
du système de validation principal.

Usage:
    python cleanup.py [--dry-run]
    
Options:
    --dry-run : Affiche ce qui serait supprimé sans le faire
"""

import os
import sys
import argparse
from pathlib import Path

# Fichiers à conserver (système de validation principal)
KEEP_FILES = {
    '__init__.py',
    'README.md',
    'generate_validation_template.py',
    'test_keywords_validation.py',
    'test_keywords_real.py',
    'validate_keywords.py',
    'simple_test.py',
    'run_simple_test.py',
    'cleanup.py',
    'keywords_validation_expected.json',
    'validation_results.json'
}

# Extensions à nettoyer
CLEANUP_EXTENSIONS = {'.py', '.json', '.txt', '.log'}

def main():
    parser = argparse.ArgumentParser(description='Nettoie le dossier tests/')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Affiche ce qui serait supprimé sans le faire')
    args = parser.parse_args()
    
    tests_dir = Path(__file__).parent
    files_to_remove = []
    
    print("🧹 Nettoyage du dossier tests/")
    print("=" * 50)
    
    # Scanner tous les fichiers
    for file_path in tests_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name
            
            # Garder les fichiers essentiels
            if filename in KEEP_FILES:
                continue
                
            # Nettoyer les fichiers avec certaines extensions
            if file_path.suffix in CLEANUP_EXTENSIONS:
                files_to_remove.append(file_path)
    
    if not files_to_remove:
        print("✅ Aucun fichier à nettoyer trouvé")
        return
    
    print(f"📋 {len(files_to_remove)} fichier(s) à supprimer:")
    for file_path in files_to_remove:
        print(f"   🗑️  {file_path.name}")
    
    if args.dry_run:
        print("\n🔍 Mode dry-run: aucun fichier supprimé")
        return
    
    print(f"\n❓ Supprimer ces {len(files_to_remove)} fichier(s) ? (y/N): ", end="")
    response = input().strip().lower()
    
    if response in ['y', 'yes', 'oui', 'o']:
        removed_count = 0
        for file_path in files_to_remove:
            try:
                file_path.unlink()
                print(f"   ✅ Supprimé: {file_path.name}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Erreur: {file_path.name} - {e}")
        
        print(f"\n🎉 Nettoyage terminé: {removed_count}/{len(files_to_remove)} fichiers supprimés")
    else:
        print("🚫 Opération annulée")

if __name__ == "__main__":
    main()
