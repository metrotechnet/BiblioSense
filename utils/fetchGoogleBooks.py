#!/usr/bin/env python3
"""
fetchGoogleLivre.py

Script pour extraire les informations des 10000 romans les plus récents 
depuis l'API Google Books et les sauvegarder en JSON.
MODIFIÉ: Filtrage renforcé pour les livres français uniquement
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os
from urllib.parse import quote
import re
from collections import Counter


# -------- Configuration --------
OUTPUT_FILE = "dbase/google_books_romans.json"
MAX_BOOKS = 10000  # Nombre maximum de livres à extraire
BATCH_SIZE = 40    # Nombre de livres par requête API (max 50 pour Google Books)
DELAY = 1          # Délai entre les requêtes (en secondes)
API_KEY = "AIzaSyAbbIh2GUofeSbDO2cw-yqXKTeMA4YKKCQ"       # Optionnel: clé API Google Books pour plus de requêtes

# Catégories de fiction/romans en français et anglais
FICTION_CATEGORIES = [
    "fiction",
    "roman", 
    "novel",
    "fantasy",
    "science fiction",
    "mystery",
    "thriller",
    "romance",
    "adventure",
    "historical fiction",
    "contemporary fiction",
    "literary fiction"
]

# Langues à inclure
LANGUAGES = ["fr"]

def get_google_books_api_url(query, lang, start_index=0, max_results=40, order_by="newest"):
    """
    Construit l'URL pour l'API Google Books
    
    Args:
        query (str): Requête de recherche
        start_index (int): Index de départ pour la pagination
        max_results (int): Nombre maximum de résultats (max 40)
        order_by (str): Ordre de tri ('relevance' ou 'newest')
    
    Returns:
        str: URL de l'API Google Books
    """
    base_url = "https://www.googleapis.com/books/v1/volumes"
    
    # Construire la requête avec filtres - AJOUT langRestrict=fr
    encoded_query = quote(query)
    url = f"{base_url}?q={encoded_query}&langRestrict={lang}&orderBy={order_by}&maxResults={max_results}&startIndex={start_index}"

    # Ajouter la clé API si disponible
    if API_KEY:
        url += f"&key={API_KEY}"
    
    return url

def extract_book_info(book_item):
    """
    Extrait les informations d'un livre depuis la réponse de l'API Google Books
    
    Args:
        book_item (dict): Item de livre de l'API Google Books
        
    Returns:
        dict: Informations formatées du livre
    """
    volume_info = book_item.get("volumeInfo", {})
    
    # Informations de base
    title = volume_info.get("title", "Titre inconnu")
    authors = volume_info.get("authors", ["Auteur inconnu"])
    author = ", ".join(authors) if isinstance(authors, list) else str(authors)
    
    # Description/résumé
    synopsis = volume_info.get("description", "")

    # Nettoyer et améliorer le synopsis
    if synopsis:
        # Supprimer les balises HTML éventuelles
        import re
        synopsis = re.sub(r'<[^>]+>', '', synopsis)
    else:
        synopsis = ""
    
    # Informations de publication
    publisher = volume_info.get("publisher", "Éditeur inconnu")
    published_date = volume_info.get("publishedDate", "Date inconnue")
    
    # Détails du livre
    page_count = volume_info.get("pageCount", 0)
    language = volume_info.get("language", "")
    
    # Catégories
    categories = volume_info.get("categories", [])
    category = ", ".join(categories) if categories else "Fiction"
    
    # ISBN et identifiants
    industry_identifiers = volume_info.get("industryIdentifiers", [])
    isbn = ""
    for identifier in industry_identifiers:
        if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
            isbn = identifier.get("identifier", "")
            break
    
    # Image de couverture
    image_links = volume_info.get("imageLinks", {})
    cover_url = (image_links.get("thumbnail") or 
                image_links.get("smallThumbnail") or 
                image_links.get("small") or "")
    
    # Lien vers Google Books
    google_link = volume_info.get("infoLink", "")
    
    # Générer un ID unique
    book_id = book_item.get("id", f"google_book_{hash(title + author)}")
    
    return {
        "id": book_id,
        "titre": title,
        "auteur": author,
        "resume": synopsis,
        "editeur": publisher,
        "parution": published_date,
        "pages": str(page_count) if page_count > 0 else "Inconnu",
        "langue": language,
        "categorie": category,
        "isbn": isbn,
        "couverture": cover_url,
        "lien": google_link,
        "source": "Google Books API"
    }

def search_books_by_query(query, lang, max_books_per_query=1000):
    """
    Recherche des livres pour une requête spécifique
    
    Args:
        query (str): Requête de recherche
        max_books_per_query (int): Nombre maximum de livres à extraire pour cette requête
        
    Returns:
        list: Liste des livres trouvés
    """
    books = []
    start_index = 0
    
    print(f"🔍 Recherche: {query}")
    
    while len(books) < max_books_per_query:
        try:
            # Calculer le nombre de résultats à demander
            remaining = max_books_per_query - len(books)
            max_results = min(BATCH_SIZE, remaining)
            
            # Construire l'URL de l'API
            url = get_google_books_api_url(query, lang, start_index, max_results)
            
            # Faire la requête
            print(f"   📡 Requête API: index {start_index}, résultats {max_results}")
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"   ❌ Erreur API: {response.status_code}")
                if response.status_code == 429:  # Rate limit
                    print("   ⏳ Rate limit atteint, attente 60 secondes...")
                    time.sleep(60)
                    continue
                elif response.status_code == 403:
                    print("   🔑 Erreur 403: Vérifiez votre clé API ou les quotas")
                    break
                else:
                    break
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                print(f"   ✅ Aucun livre supplémentaire trouvé")
                break
            
            # Traiter chaque livre - AJOUT DEBUG
            for item in items:
                try:
                    book_info = extract_book_info(item)
                    
                    # Debug: afficher la langue détectée pour les premiers livres
                    # if len(books) < 5:
                    #     print(f"   🔍 Debug: '{book_info['titre']}' - Langue: '{book_info['langue']}'")
                    
                    # Filtrer les livres (vérifier si c'est de la fiction française)
                    # if is_fiction_book(book_info):
                    if book_info["langue"] == lang and is_fiction_book(book_info):
                        books.append(book_info)

                    if len(books) > 0 and len(books) % 100 == 0:
                        print(f"   📚 {len(books)} livres extraits...")
                            
                except Exception as e:
                    print(f"   ⚠️  Erreur extraction livre: {e}")
                    continue
            
            start_index += len(items)
            
            # Respecter les limites de l'API
            time.sleep(DELAY)
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erreur réseau: {e}")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"   ❌ Erreur inattendue: {e}")
            break
    
    print(f"   ✅ {len(books)} livres trouvés pour '{query}'")
    return books

def is_fiction_book(book_info):
    """
    Vérifie si un livre est probablement de la fiction ET en français
    
    Args:
        book_info (dict): Informations du livre
        
    Returns:
        bool: True si le livre semble être de la fiction en français
    """
    # D'abord vérifier la langue - CRITIQUE pour éviter les livres anglais
    language = book_info.get("langue", "").lower()
    if language and language not in ["fr", "french", "français"]:
        return False
    
    # Vérifier les catégories
    category = book_info.get("categorie", "").lower()
    fiction_keywords = [
        "fiction", "novel", "roman", "littérature", "literature",
        "fantasy", "science fiction", "mystery", "thriller", "romance",
        "adventure", "historical fiction", "contemporary fiction"
    ]
    
    # Vérifier si une des catégories contient des mots-clés de fiction
    for keyword in fiction_keywords:
        if keyword in category:
            return True
    
    # Vérifier dans le titre et la description (plus conservateur)
    title = book_info.get("titre", "").lower()
    description = book_info.get("resume", "").lower()
    
    # Exclure les livres non-fiction évidents
    non_fiction_keywords = [
        "cookbook", "manual", "guide", "handbook", "textbook",
        "biography", "autobiography", "memoir", "histoire vraie",
        "self-help", "how to", "comment faire"
    ]
    
    for keyword in non_fiction_keywords:
        if keyword in title or keyword in description:
            return False
    
    return True

def save_books_to_json(books, filename):
    """
    Sauvegarde la liste des livres en format JSON
    
    Args:
        books (list): Liste des livres
        filename (str): Nom du fichier de sortie
    """
    # Créer le répertoire si nécessaire
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Sauvegarder en JSON avec formatage
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    
    print(f"📁 {len(books)} livres sauvegardés dans {filename}")

def main():
    """
    Fonction principale pour extraire les romans depuis Google Books API
    """
    print("🚀 Début de l'extraction des romans depuis Google Books API")
    print(f"🎯 Objectif: {MAX_BOOKS} livres maximum")
    print(f"📁 Fichier de sortie: {OUTPUT_FILE}")
    print("🇫🇷 FILTRAGE FRANÇAIS RENFORCÉ ACTIVÉ")
    print("-" * 60)
    
    all_books = []
    books_per_category = MAX_BOOKS // len(FICTION_CATEGORIES)
    
    try:
        for i, category in enumerate(FICTION_CATEGORIES):
            print(f"\n📖 Catégorie {i+1}/{len(FICTION_CATEGORIES)}: {category}")
            
            # Construire des requêtes pour différentes langues
            for lang in LANGUAGES:
                if len(all_books) >= MAX_BOOKS:
                    break
                    
                # Construire la requête SIMPLIFIÉE (langRestrict dans URL)
                query = f"subject:{category}"
                
                # Calculer combien de livres extraire pour cette requête
                remaining_books = MAX_BOOKS - len(all_books)
                max_books_this_query = min(books_per_category // len(LANGUAGES), remaining_books)
                
                # if max_books_this_query <= 0:
                #     break
                
                # Rechercher les livres
                category_books = search_books_by_query(query, lang, max_books_this_query)
                
                # Éviter les doublons (basé sur titre + auteur)
                existing_keys = {(book['titre'], book['auteur']) for book in all_books}
                new_books = [book for book in category_books 
                           if (book['titre'], book['auteur']) not in existing_keys]
                
                all_books.extend(new_books)
                print(f"   ➕ {len(new_books)} nouveaux livres ajoutés (total: {len(all_books)})")
                
                # Sauvegarder périodiquement
                if len(all_books) % 100 == 0:
                    print(f"💾 Sauvegarde intermédiaire: {len(all_books)} livres")
                    save_books_to_json(all_books, OUTPUT_FILE.replace('.json', '_temp.json'))
            
            if len(all_books) >= MAX_BOOKS:
                print(f"🎯 Objectif atteint: {len(all_books)} livres extraits")
                break
    
    except KeyboardInterrupt:
        print("\n⚠️  Extraction interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
    
    finally:
        # Sauvegarder les résultats finaux
        if all_books:
            save_books_to_json(all_books, OUTPUT_FILE)
            
            # Supprimer le fichier temporaire s'il existe
            temp_file = OUTPUT_FILE.replace('.json', '_temp.json')
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            print(f"\n✅ Extraction terminée!")
            print(f"📚 Total de livres extraits: {len(all_books)}")
            print(f"📁 Fichier de sortie: {OUTPUT_FILE}")
            print(f"🕐 Temps d'exécution: {datetime.now()}")
        else:
            print("\n❌ Aucun livre extrait")

if __name__ == "__main__":
    main()