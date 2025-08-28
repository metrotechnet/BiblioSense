#!/usr/bin/env python3
"""
Script pour fusionner tous les fichiers JSON du dossier pretnumerique
en un seul fichier JSON consolidé avec des statistiques détaillées.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import datetime

def load_json_file(file_path):
    """Charge un fichier JSON et retourne son contenu."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]  # Convert single dict to list
            else:
                print(f"⚠️  Format inattendu dans {file_path}: {type(data)}")
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

def get_category_from_filename(filename):
    """Extrait le nom de la catégorie du nom de fichier."""
    return filename.replace('.json', '').replace('_', ' ')

def validate_book_data(book, source_file):
    """Valide et nettoie les données d'un livre."""
    if not isinstance(book, dict):
        print(f"⚠️  Livre non valide dans {source_file}: {type(book)}")
        return None
    
    # Champs obligatoires
    required_fields = ['titre']
    for field in required_fields:
        if field not in book or not book[field]:
            print(f"⚠️  Livre sans {field} dans {source_file}: {book}")
            return None
    
    # Nettoyer et standardiser les données
    cleaned_book = {}
    for key, value in book.items():
        if isinstance(value, str):
            cleaned_book[key] = value.strip()
        else:
            cleaned_book[key] = value
    
    # Ajouter la source du fichier
    cleaned_book['source_fichier'] = source_file
    
    return cleaned_book

def remove_duplicates(all_books):
    """Supprime les doublons basés sur le titre et l'auteur."""
    print("\n🔍 Recherche et suppression des doublons...")
    
    seen_books = {}  # Dictionnaire pour stocker les livres déjà vus
    unique_books = []
    duplicates_found = []
    
    for book in all_books:
        # Créer une clé unique basée sur titre et auteur (normalisés)
        titre = book.get('titre', '').strip().lower()
        auteur = book.get('auteur', '').strip().lower()
        
        # Nettoyer l'auteur (enlever les mentions comme "(Auteur)", "(Narrateur)", etc.)
        import re
        auteur_clean = re.sub(r'\([^)]*\)', '', auteur).strip()
        
        # Créer la clé unique
        unique_key = f"{titre}|||{auteur_clean}"
        
        if unique_key in seen_books:
            # Doublon trouvé
            original_book = seen_books[unique_key]
            duplicate_info = {
                'titre': book.get('titre', ''),
                'auteur': book.get('auteur', ''),
                'source_original': original_book.get('source_fichier', ''),
                'source_doublon': book.get('source_fichier', ''),
                'lien_original': original_book.get('lien', ''),
                'lien_doublon': book.get('lien', '')
            }
            duplicates_found.append(duplicate_info)
            
            # Choisir le meilleur livre à conserver (celui avec le plus d'informations)
            original_score = sum(1 for v in original_book.values() if v and str(v).strip())
            current_score = sum(1 for v in book.values() if v and str(v).strip())
            
            if current_score > original_score:
                # Le livre actuel a plus d'informations, remplacer l'original
                seen_books[unique_key] = book
                # Mettre à jour la liste des livres uniques
                for i, unique_book in enumerate(unique_books):
                    if unique_book is original_book:
                        unique_books[i] = book
                        break
                print(f"   📝 Doublon remplacé: '{book.get('titre', '')}' - Nouvelle source: {book.get('source_fichier', '')}")
            else:
                print(f"   🔄 Doublon ignoré: '{book.get('titre', '')}' de {book.get('source_fichier', '')}")
        else:
            # Nouveau livre unique
            seen_books[unique_key] = book
            unique_books.append(book)
    
    print(f"\n📊 RÉSULTATS DE LA DÉDUPLICATION:")
    print(f"   📚 Livres originaux: {len(all_books)}")
    print(f"   ✅ Livres uniques: {len(unique_books)}")
    print(f"   🔄 Doublons supprimés: {len(duplicates_found)}")
    
    # Afficher les doublons trouvés pour information
    if duplicates_found:
        print(f"\n📋 DOUBLONS DÉTECTÉS:")
        for i, dup in enumerate(duplicates_found[:10], 1):  # Afficher les 10 premiers
            print(f"   {i:2d}. '{dup['titre']}' par {dup['auteur']}")
            print(f"       📁 Sources: {dup['source_original']} ➜ {dup['source_doublon']}")
        
        if len(duplicates_found) > 10:
            print(f"   ... et {len(duplicates_found) - 10} autres doublons")
    
    return unique_books, duplicates_found

def generate_statistics(all_books, duplicates_info=None):
    """Génère des statistiques détaillées sur les livres."""
    stats = {
        'total_livres': len(all_books),
        'par_categorie': defaultdict(int),
        'par_editeur': defaultdict(int),
        'par_langue': defaultdict(int),
        'par_annee': defaultdict(int),
        'avec_couverture': 0,
        'sans_couverture': 0,
        'avec_resume': 0,
        'sans_resume': 0,
        'date_fusion': datetime.datetime.now().isoformat()
    }
    
    # Ajouter les statistiques de déduplication si disponibles
    if duplicates_info:
        stats['deduplication'] = {
            'doublons_trouves': len(duplicates_info),
            'doublons_details': duplicates_info
        }
    
    for book in all_books:
        # Statistiques par catégorie
        categorie = book.get('categorie', 'Non définie')
        stats['par_categorie'][categorie] += 1
        
        # Statistiques par éditeur
        editeur = book.get('editeur', 'Non défini')
        stats['par_editeur'][editeur] += 1
        
        # Statistiques par langue
        langue = book.get('langue', 'Non définie')
        stats['par_langue'][langue] += 1
        
        # Statistiques par année de parution
        parution = book.get('parution', '')
        if parution:
            # Extraire l'année (format peut être "Janvier 2024", "2024", etc.)
            try:
                # Chercher un nombre de 4 chiffres dans la chaîne
                import re
                year_match = re.search(r'\b(20\d{2})\b', parution)
                if year_match:
                    year = year_match.group(1)
                    stats['par_annee'][year] += 1
            except:
                pass
        
        # Statistiques couverture et résumé
        if book.get('couverture') and book['couverture'].strip():
            stats['avec_couverture'] += 1
        else:
            stats['sans_couverture'] += 1
            
        if book.get('resume') and book['resume'].strip():
            stats['avec_resume'] += 1
        else:
            stats['sans_resume'] += 1
    
    # Convertir defaultdict en dict normal pour la sérialisation JSON
    stats['par_categorie'] = dict(stats['par_categorie'])
    stats['par_editeur'] = dict(stats['par_editeur'])
    stats['par_langue'] = dict(stats['par_langue'])
    stats['par_annee'] = dict(stats['par_annee'])
    
    return stats

def main():
    """Fonction principale pour fusionner les fichiers JSON."""
    print("🔄 Début de la fusion des fichiers JSON Prêt numérique...")
    print("=" * 60)
    
    # Définir les chemins (script exécuté depuis le dossier pretnumerique)
    pretnumerique_dir = Path("pretnumerique_dbase")  
    output_file = "./dbase/prenumerique_complet.json"
    stats_file = "./dbase/prenumerique_statistiques.json"
    
    # Vérifier que le dossier pretnumerique existe
    if not pretnumerique_dir.exists():
        print(f"❌ Le dossier {pretnumerique_dir} n'existe pas.")
        return

    
    # Collecter tous les fichiers JSON
    json_files = list(pretnumerique_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ Aucun fichier JSON trouvé dans {pretnumerique_dir}")
        return
    
    print(f"📁 {len(json_files)} fichiers JSON trouvés:")
    for file in sorted(json_files):
        print(f"   - {file.name}")
    print()
    
    # Fusionner tous les livres
    all_books = []
    file_stats = {}
    
    for json_file in sorted(json_files):
        print(f"⏳ Traitement de {json_file.name}...")
        
        books = load_json_file(json_file)
        valid_books = []
        
        for book in books:
            validated_book = validate_book_data(book, json_file.name)
            if validated_book:
                valid_books.append(validated_book)
        
        file_stats[json_file.name] = {
            'total_brut': len(books),
            'total_valide': len(valid_books),
            'categorie': get_category_from_filename(json_file.stem)
        }
        
        all_books.extend(valid_books)
        print(f"   ✅ {len(valid_books)} livres valides sur {len(books)} trouvés")
    
    print(f"\n📊 RÉSULTATS DE LA FUSION:")
    print(f"   📚 Total de livres fusionnés: {len(all_books)}")
    print(f"   📁 Fichiers traités: {len(json_files)}")
    
    # Supprimer les doublons
    unique_books, duplicates_found = remove_duplicates(all_books)
    
    # Générer les statistiques
    print("\n⏳ Génération des statistiques...")
    stats = generate_statistics(unique_books, duplicates_found)
    
    # Ajouter les statistiques par fichier
    stats['par_fichier'] = file_stats
    
    # Sauvegarder le fichier fusionné (avec les livres uniques)
    print(f"\n💾 Sauvegarde dans {output_file}...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_books, f, ensure_ascii=False, indent=2)
        print(f"   ✅ Fichier fusionné sauvegardé: {output_file}")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde: {e}")
        return
    
    # Sauvegarder les statistiques
    print(f"💾 Sauvegarde des statistiques dans {stats_file}...")
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"   ✅ Statistiques sauvegardées: {stats_file}")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde des statistiques: {e}")
    
    # Affichage des statistiques principales
    print(f"\n📈 STATISTIQUES PRINCIPALES:")
    print(f"   📚 Total de livres: {stats['total_livres']}")
    if 'deduplication' in stats:
        print(f"   🔄 Doublons supprimés: {stats['deduplication']['doublons_trouves']}")
    print(f"   🏷️  Catégories: {len(stats['par_categorie'])}")
    print(f"   🏢 Éditeurs: {len(stats['par_editeur'])}")
    print(f"   🌍 Langues: {len(stats['par_langue'])}")
    print(f"   📅 Années: {len(stats['par_annee'])}")
    print(f"   🖼️  Avec couverture: {stats['avec_couverture']} ({stats['avec_couverture']/stats['total_livres']*100:.1f}%)")
    print(f"   📖 Avec résumé: {stats['avec_resume']} ({stats['avec_resume']/stats['total_livres']*100:.1f}%)")
    
    # Top 10 des catégories
    print(f"\n🏆 TOP 10 DES CATÉGORIES:")
    sorted_categories = sorted(stats['par_categorie'].items(), key=lambda x: x[1], reverse=True)
    for i, (cat, count) in enumerate(sorted_categories[:10], 1):
        print(f"   {i:2d}. {cat}: {count} livres")
    
    # Top 10 des éditeurs
    print(f"\n🏆 TOP 10 DES ÉDITEURS:")
    sorted_editors = sorted(stats['par_editeur'].items(), key=lambda x: x[1], reverse=True)
    for i, (editor, count) in enumerate(sorted_editors[:10], 1):
        print(f"   {i:2d}. {editor}: {count} livres")
    
    print(f"\n" + "=" * 60)
    print(f"🎉 Fusion terminée avec succès!")
    print(f"📄 Fichier fusionné: {output_file}")
    print(f"📊 Statistiques: {stats_file}")
    print(f"=" * 60)

if __name__ == "__main__":
    main()
