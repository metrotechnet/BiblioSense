#!/usr/bin/env python3
"""
Script pour supprimer les doublons dans le fichier book_dbase_montreal.json
Détecte et supprime les livres en double basés sur le titre et l'auteur.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
import datetime
import argparse

def normalize_string(text):
    """Normalise une chaîne de caractères pour la comparaison de doublons."""
    if not text:
        return ""
    
    # Convertir en minuscules
    text = text.lower().strip()
    
    # Supprimer les accents et caractères spéciaux
    import unicodedata
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

def generate_unique_key(book):
    """Génère une clé unique pour un livre basée sur le titre et l'auteur normalisés."""
    titre = normalize_string(book.get('titre', ''))
    auteur = clean_author_name(book.get('auteur', ''))
    
    # Créer une clé unique
    return f"{titre}|||{auteur}"

def calculate_book_score(book):
    """Calcule un score de qualité pour un livre basé sur la complétude des données."""
    score = 0
    important_fields = ['titre', 'auteur', 'resume', 'categorie', 'editeur', 'parution', 'pages', 'langue', 'couverture']
    
    for field in important_fields:
        value = book.get(field, '')
        if value and str(value).strip() and str(value).strip().lower() not in ['inconnu', 'non défini', 'non définie', '']:
            score += 1
            
        # Bonus pour les champs particulièrement importants
        if field in ['resume', 'couverture'] and value and len(str(value).strip()) > 10:
            score += 1
    
    return score

def find_and_remove_duplicates(books_list, verbose=True):
    """
    Trouve et supprime les doublons dans la liste de livres.
    Retourne la liste nettoyée et les informations sur les doublons.
    """
    if verbose:
        print(f"\n🔍 Analyse des doublons sur {len(books_list)} livres...")
    
    seen_books = {}  # Dictionnaire pour stocker les livres déjà vus
    unique_books = []
    duplicates_info = []
    
    for i, book in enumerate(books_list):
        # Générer la clé unique
        unique_key = generate_unique_key(book)
        
        if not unique_key or unique_key == "|||":
            # Livre avec des données manquantes critiques
            if verbose:
                print(f"   ⚠️  Livre ignoré (données manquantes): {book.get('titre', 'TITRE MANQUANT')}")
            continue
        
        if unique_key in seen_books:
            # Doublon détecté
            original_book = seen_books[unique_key]
            original_score = calculate_book_score(original_book)
            current_score = calculate_book_score(book)
            
            duplicate_entry = {
                'titre': book.get('titre', ''),
                'auteur': book.get('auteur', ''),
                'original_id': original_book.get('id', ''),
                'duplicate_id': book.get('id', ''),
                'original_score': original_score,
                'duplicate_score': current_score,
                'kept': 'current' if current_score > original_score else 'original'
            }
            duplicates_info.append(duplicate_entry)
            
            if current_score > original_score:
                # Le livre actuel est meilleur, remplacer l'original
                seen_books[unique_key] = book
                # Trouver et remplacer dans la liste des uniques
                for j, unique_book in enumerate(unique_books):
                    if unique_book is original_book:
                        unique_books[j] = book
                        break
                        
                if verbose:
                    print(f"   🔄 Doublon remplacé: '{book.get('titre', '')}' (ID: {book.get('id', '')}) - Score: {current_score} > {original_score}")
            else:
                # Garder l'original
                if verbose:
                    print(f"   ❌ Doublon supprimé: '{book.get('titre', '')}' (ID: {book.get('id', '')}) - Score: {current_score} <= {original_score}")
        else:
            # Nouveau livre unique
            seen_books[unique_key] = book
            unique_books.append(book)
    
    if verbose:
        print(f"\n📊 RÉSULTATS DE LA DÉDUPLICATION:")
        print(f"   📚 Livres originaux: {len(books_list)}")
        print(f"   ✅ Livres uniques: {len(unique_books)}")
        print(f"   🔄 Doublons supprimés: {len(duplicates_info)}")
        print(f"   📈 Réduction: {len(books_list) - len(unique_books)} livres ({((len(books_list) - len(unique_books)) / len(books_list) * 100):.1f}%)")
    
    return unique_books, duplicates_info

def generate_duplicate_report(duplicates_info, output_file):
    """Génère un rapport détaillé des doublons trouvés."""
    report = {
        'date_analyse': datetime.datetime.now().isoformat(),
        'total_doublons': len(duplicates_info),
        'doublons_detailles': duplicates_info,
        'statistiques': {
            'doublons_remplaces': len([d for d in duplicates_info if d['kept'] == 'current']),
            'doublons_supprimes': len([d for d in duplicates_info if d['kept'] == 'original'])
        }
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"   📊 Rapport de doublons sauvegardé: {output_file}")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde du rapport: {e}")

def backup_original_file(file_path):
    """Crée une sauvegarde du fichier original."""
    backup_path = f"{file_path}.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"   💾 Sauvegarde créée: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde: {e}")
        return None

def main():
    """Fonction principale pour supprimer les doublons."""
    parser = argparse.ArgumentParser(description='Supprime les doublons du fichier book_dbase_montreal.json')
    parser.add_argument('--input', '-i', default='./dbase/book_dbase_montreal.json', 
                       help='Fichier JSON d\'entrée (défaut: ./dbase/book_dbase_montreal.json)')
    parser.add_argument('--output', '-o', 
                       help='Fichier JSON de sortie (défaut: même que l\'entrée)')
    parser.add_argument('--report', '-r', default='./dbase/duplicates_report.json',
                       help='Fichier de rapport des doublons (défaut: ./dbase/duplicates_report.json)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Ne pas créer de sauvegarde du fichier original')
    parser.add_argument('--dry-run', action='store_true',
                       help='Afficher les doublons sans modifier le fichier')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Mode silencieux (moins de messages)')
    
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output or input_file
    report_file = args.report
    verbose = not args.quiet
    
    if verbose:
        print("🔄 Suppression des doublons dans book_dbase_montreal.json")
        print("=" * 60)
    
    # Vérifier que le fichier d'entrée existe
    if not os.path.exists(input_file):
        print(f"❌ Le fichier {input_file} n'existe pas.")
        return 1
    
    # Charger le fichier JSON
    if verbose:
        print(f"📖 Chargement du fichier: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            books_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON dans le fichier: {e}")
        return 1
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return 1
    
    if not isinstance(books_data, list):
        print(f"❌ Le fichier doit contenir une liste de livres, trouvé: {type(books_data)}")
        return 1
    
    if verbose:
        print(f"   ✅ {len(books_data)} livres chargés")
    
    # Détecter et supprimer les doublons
    unique_books, duplicates_info = find_and_remove_duplicates(books_data, verbose)
    
    # Afficher quelques exemples de doublons
    if verbose and duplicates_info:
        print(f"\n📋 EXEMPLES DE DOUBLONS TRAITÉS:")
        for i, dup in enumerate(duplicates_info[:5], 1):
            kept_symbol = "✅" if dup['kept'] == 'current' else "🔄"
            print(f"   {i}. {kept_symbol} '{dup['titre']}' par {dup['auteur']}")
            print(f"      IDs: {dup['original_id']} vs {dup['duplicate_id']} (scores: {dup['original_score']} vs {dup['duplicate_score']})")
        
        if len(duplicates_info) > 5:
            print(f"   ... et {len(duplicates_info) - 5} autres doublons")
    
    # Mode dry-run
    if args.dry_run:
        if verbose:
            print(f"\n🔍 MODE DRY-RUN: Aucune modification apportée au fichier")
        if duplicates_info:
            generate_duplicate_report(duplicates_info, report_file)
        return 0
    
    # Créer une sauvegarde si demandée
    if not args.no_backup and input_file == output_file:
        backup_original_file(input_file)
    
    # Sauvegarder le fichier nettoyé
    if verbose:
        print(f"\n💾 Sauvegarde du fichier nettoyé: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_books, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"   ✅ Fichier sauvegardé avec {len(unique_books)} livres uniques")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde: {e}")
        return 1
    
    # Générer le rapport des doublons
    if duplicates_info:
        generate_duplicate_report(duplicates_info, report_file)
    
    if verbose:
        print(f"\n" + "=" * 60)
        print(f"🎉 Suppression des doublons terminée!")
        print(f"📄 Fichier nettoyé: {output_file}")
        if duplicates_info:
            print(f"📊 Rapport des doublons: {report_file}")
        print(f"📈 {len(books_data) - len(unique_books)} doublons supprimés ({((len(books_data) - len(unique_books)) / len(books_data) * 100):.1f}% de réduction)")
        print("=" * 60)
    
    return 0

if __name__ == "__main__":
    exit(main())