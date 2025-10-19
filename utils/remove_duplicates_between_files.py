#!/usr/bin/env python3
"""
Script pour supprimer les éléments de prenumerique_montreal_complet2.json
qui existent déjà dans prenumerique_montreal_complet.json
Sauvegarde le résultat dans prenumerique_montreal_complet2_del.json
"""

import json
import os
from pathlib import Path
import re
import unicodedata
import datetime
import argparse

def normalize_string(text):
    """Normalise une chaîne de caractères pour la comparaison."""
    if not text:
        return ""
    
    # Convertir en minuscules
    text = text.lower().strip()
    
    # Supprimer les accents et caractères spéciaux
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Supprimer la ponctuation et les espaces multiples
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def clean_author_name(author):
    """Nettoie le nom de l'auteur en supprimant les mentions comme (Auteur), (Narrateur), etc."""
    if not author:
        return ""
    
    # Supprimer les mentions entre parenthèses
    author_clean = re.sub(r'\([^)]*\)', '', author).strip()
    
    # Supprimer les rôles multiples séparés par des virgules
    author_clean = author_clean.split(',')[0].strip()
    
    return normalize_string(author_clean)

def generate_book_signature(book):
    """Génère une signature unique pour un livre basée sur le titre et l'auteur normalisés."""
    titre = normalize_string(book.get('titre', ''))
    auteur = clean_author_name(book.get('auteur', ''))
    
    # Créer une signature unique
    return f"{titre}|||{auteur}"

def load_json_file(file_path):
    """Charge un fichier JSON et retourne son contenu."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                print(f"❌ Le fichier {file_path} doit contenir une liste, trouvé: {type(data)}")
                return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON dans {file_path}: {e}")
        return []
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {file_path}: {e}")
        return []

def build_book_index(books_list, verbose=True):
    """Construit un index des livres basé sur leurs signatures."""
    book_index = {}
    duplicates_in_source = 0
    
    if verbose:
        print(f"   📚 Construction de l'index pour {len(books_list)} livres...")
    
    for i, book in enumerate(books_list):
        signature = generate_book_signature(book)
        
        if not signature or signature == "|||":
            if verbose:
                print(f"   ⚠️  Livre ignoré (données manquantes): index {i}")
            continue
        
        if signature in book_index:
            duplicates_in_source += 1
            if verbose and duplicates_in_source <= 5:  # Afficher seulement les 5 premiers
                print(f"   🔄 Doublon détecté dans le fichier source: '{book.get('titre', '')}'")
        else:
            book_index[signature] = {
                'book': book,
                'index': i
            }
    
    if verbose and duplicates_in_source > 5:
        print(f"   🔄 ... et {duplicates_in_source - 5} autres doublons dans le fichier source")
    
    if verbose:
        print(f"   ✅ Index créé avec {len(book_index)} signatures uniques")
        if duplicates_in_source > 0:
            print(f"   ⚠️  {duplicates_in_source} doublons trouvés dans le fichier source")
    
    return book_index

def remove_existing_items(source_books, target_books, verbose=True):
    """
    Supprime de target_books tous les éléments qui existent dans source_books.
    Retourne la liste filtrée et les statistiques.
    """
    if verbose:
        print(f"\n🔍 Analyse des éléments à supprimer...")
        print(f"   📚 Fichier source: {len(source_books)} livres")
        print(f"   📚 Fichier cible: {len(target_books)} livres")
    
    # Construire l'index du fichier source
    source_index = build_book_index(source_books, verbose)
    
    # Filtrer le fichier cible
    filtered_books = []
    removed_books = []
    
    if verbose:
        print(f"\n   🔄 Filtrage en cours...")
    
    for i, book in enumerate(target_books):
        signature = generate_book_signature(book)
        
        if not signature or signature == "|||":
            if verbose:
                print(f"   ⚠️  Livre cible ignoré (données manquantes): index {i}")
            continue
        
        if signature in source_index:
            # Ce livre existe dans le fichier source, le supprimer
            removed_info = {
                'target_index': i,
                'source_index': source_index[signature]['index'],
                'titre': book.get('titre', ''),
                'auteur': book.get('auteur', ''),
                'signature': signature
            }
            removed_books.append(removed_info)
            
            if verbose and len(removed_books) <= 10:  # Afficher les 10 premiers
                print(f"   ❌ Supprimé: '{book.get('titre', '')}' (existe à l'index {source_index[signature]['index']} du fichier source)")
        else:
            # Ce livre n'existe pas dans le fichier source, le garder
            filtered_books.append(book)
    
    if verbose and len(removed_books) > 10:
        print(f"   ❌ ... et {len(removed_books) - 10} autres livres supprimés")
    
    return filtered_books, removed_books

def generate_removal_report(removed_books, output_file):
    """Génère un rapport détaillé des éléments supprimés."""
    report = {
        'date_traitement': datetime.datetime.now().isoformat(),
        'total_supprimes': len(removed_books),
        'elements_supprimes': removed_books,
        'statistiques': {
            'signatures_uniques_supprimees': len(set(item['signature'] for item in removed_books))
        }
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"   📊 Rapport de suppression sauvegardé: {output_file}")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde du rapport: {e}")

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description='Supprime les éléments dupliqués entre deux fichiers JSON')
    parser.add_argument('--source', '-s', default='./dbase/prenumerique_quebec_complet.json', 
                       help='Fichier JSON source (référence) (défaut: ./dbase/prenumerique_quebec_complet.json)')
    parser.add_argument('--target', '-t', default='./dbase/prenumerique_quebec_complet2.json',
                       help='Fichier JSON cible à filtrer (défaut: ./dbase/prenumerique_quebec_complet2.json)')
    parser.add_argument('--output', '-o', default='./dbase/prenumerique_quebec_complet2_del.json',
                       help='Fichier JSON de sortie (défaut: ./dbase/prenumerique_quebec_complet2_del.json)')
    parser.add_argument('--report', '-r', default='./dbase/removal_report.json',
                       help='Fichier de rapport des suppressions (défaut: ./dbase/removal_report.json)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Afficher les éléments à supprimer sans créer le fichier de sortie')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Mode silencieux (moins de messages)')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    if verbose:
        print("🔄 Suppression des éléments dupliqués entre fichiers JSON")
        print("=" * 60)
        print(f"📖 Fichier source (référence): {args.source}")
        print(f"📖 Fichier cible (à filtrer): {args.target}")
        print(f"💾 Fichier de sortie: {args.output}")
    
    # Vérifier que les fichiers d'entrée existent
    if not os.path.exists(args.source):
        print(f"❌ Le fichier source {args.source} n'existe pas.")
        return 1
    
    if not os.path.exists(args.target):
        print(f"❌ Le fichier cible {args.target} n'existe pas.")
        return 1
    
    # Charger les fichiers JSON
    if verbose:
        print(f"\n📖 Chargement des fichiers...")
    
    source_books = load_json_file(args.source)
    if not source_books:
        return 1
    
    target_books = load_json_file(args.target)
    if not target_books:
        return 1
    
    if verbose:
        print(f"   ✅ Fichier source chargé: {len(source_books)} livres")
        print(f"   ✅ Fichier cible chargé: {len(target_books)} livres")
    
    # Supprimer les éléments existants
    filtered_books, removed_books = remove_existing_items(source_books, target_books, verbose)
    
    # Afficher les statistiques
    if verbose:
        print(f"\n📊 RÉSULTATS:")
        print(f"   📚 Livres dans le fichier source: {len(source_books)}")
        print(f"   📚 Livres dans le fichier cible: {len(target_books)}")
        print(f"   ❌ Livres supprimés (dupliqués): {len(removed_books)}")
        print(f"   ✅ Livres conservés: {len(filtered_books)}")
        print(f"   📈 Réduction: {len(removed_books)} livres ({(len(removed_books) / len(target_books) * 100):.1f}%)")
    
    # Afficher quelques exemples de suppressions
    if verbose and removed_books:
        print(f"\n📋 EXEMPLES D'ÉLÉMENTS SUPPRIMÉS:")
        for i, item in enumerate(removed_books[:5], 1):
            print(f"   {i}. '{item['titre']}' par {item['auteur']}")
        
        if len(removed_books) > 5:
            print(f"   ... et {len(removed_books) - 5} autres éléments supprimés")
    
    # Mode dry-run
    if args.dry_run:
        if verbose:
            print(f"\n🔍 MODE DRY-RUN: Aucun fichier de sortie créé")
        if removed_books:
            generate_removal_report(removed_books, args.report)
        return 0
    
    # Sauvegarder le fichier filtré
    if verbose:
        print(f"\n💾 Sauvegarde du fichier filtré: {args.output}")
    
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(filtered_books, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"   ✅ Fichier sauvegardé avec {len(filtered_books)} livres")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde: {e}")
        return 1
    
    # Générer le rapport des suppressions
    if removed_books:
        generate_removal_report(removed_books, args.report)
    
    if verbose:
        print(f"\n" + "=" * 60)
        print(f"🎉 Suppression des doublons terminée!")
        print(f"📄 Fichier filtré: {args.output}")
        if removed_books:
            print(f"📊 Rapport des suppressions: {args.report}")
        print(f"📈 {len(removed_books)} éléments supprimés sur {len(target_books)} ({(len(removed_books) / len(target_books) * 100):.1f}% de réduction)")
        print("=" * 60)
    
    return 0

if __name__ == "__main__":
    exit(main())