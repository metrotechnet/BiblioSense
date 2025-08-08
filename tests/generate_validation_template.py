#!/usr/bin/env python3
"""
Générateur de template de validation pour get_keywords_with_gpt
Crée des résultats attendus basés sur l'analyse des requêtes sans appeler l'API
"""

import json
import re

def extract_queries_from_markdown():
    """Extrait toutes les requêtes du fichier EXEMPLES_REQUETES.md"""
    try:
        with open("../EXEMPLES_REQUETES.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire les requêtes entre guillemets
        queries = re.findall(r'"([^"]+)"', content)
        
        # Filtrer et nettoyer
        filtered = []
        for q in queries:
            if len(q) > 5 and not q.startswith('{') and not '```' in q:
                filtered.append(q.strip())
        
        # Supprimer doublons en gardant l'ordre
        return list(dict.fromkeys(filtered))
        
    except FileNotFoundError:
        print("❌ Fichier EXEMPLES_REQUETES.md non trouvé")
        return []

def analyze_query(query):
    """
    Analyse une requête et prédit ce que get_keywords_with_gpt devrait retourner
    """
    query_lower = query.lower()
    
    # Patterns pour détecter les types de requêtes
    author_patterns = [
        r'livres?\s+de\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*)',
        r'œuvres?\s+(?:complètes?\s+)?d[\'e]\s*([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*)',
        r'romans?\s+de\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*)',
        r'tout\s+de\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*)'
    ]
    
    # Vérifier si c'est une requête auteur
    for pattern in author_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            author_name = match.group(1)
            return {
                "keywords": {
                    "auteur": [author_name, author_name.split()[-1]]  # Nom complet + nom de famille
                }
            }
    
    # Genres littéraires
    genre_mapping = {
        'science-fiction': ['science-fiction', 'sci-fi', 'SF', 'anticipation'],
        'fantasy': ['fantasy', 'fantastique', 'merveilleux', 'épique'],
        'thriller': ['thriller', 'suspense'],
        'policier': ['policier', 'polar', 'crime', 'enquête'],
        'romance': ['romance', 'romantique', 'sentimental', 'amour'],
        'historique': ['historique', 'histoire', 'époque', 'période'],
        'biographie': ['biographie', 'vie de'],
        'développement personnel': ['développement personnel', 'self-help', 'croissance'],
        'philosophie': ['philosophie', 'métaphysique'],
        'cuisine': ['cuisine', 'culinaire', 'recettes']
    }
    
    for genre, keywords in genre_mapping.items():
        if any(keyword in query_lower for keyword in keywords):
            return {
                "keywords": {
                    "categorie": keywords
                }
            }
    
    # Langues
    if 'anglais' in query_lower:
        return {"keywords": {"langue": ["anglais", "english"]}}
    elif 'français' in query_lower and 'en français' in query_lower:
        return {"keywords": {"langue": ["français", "french"]}}
    elif 'espagnol' in query_lower:
        return {"keywords": {"langue": ["espagnol", "spanish"]}}
    elif 'italien' in query_lower:
        return {"keywords": {"langue": ["italien", "italian"]}}
    
    # Pages / format
    if 'moins de' in query_lower and 'pages' in query_lower:
        match = re.search(r'moins de (\d+) pages', query_lower)
        if match:
            return {"keywords": {"pages": [f"moins de {match.group(1)}", "court", "bref"]}}
    
    if 'plus de' in query_lower and 'pages' in query_lower:
        match = re.search(r'plus de (\d+) pages', query_lower)
        if match:
            return {"keywords": {"pages": [f"plus de {match.group(1)}", "volumineux", "long"]}}
    
    # Titres spécifiques
    known_titles = {
        'le petit prince': ['Le Petit Prince', 'Petit Prince'],
        '1984': ['1984', 'Nineteen Eighty-Four'],
        "l'étranger": ["L'Étranger", "Etranger"],
        'harry potter': ['Harry Potter', 'Potter'],
        'da vinci code': ['Da Vinci Code', 'Code Da Vinci']
    }
    
    for title_key, title_variants in known_titles.items():
        if title_key in query_lower:
            return {"keywords": {"titre": title_variants}}
    
    # Thèmes généraux
    theme_mapping = {
        'intelligence artificielle': ['intelligence artificielle', 'IA', 'AI', 'technologie'],
        'seconde guerre mondiale': ['Seconde Guerre mondiale', 'WWII', 'guerre', '1939-1945'],
        'management': ['management', 'gestion', 'leadership', 'équipe'],
        'voyage': ['voyage', 'tourisme', 'guide', 'découverte'],
        'art': ['art', 'peinture', 'sculpture', 'artistique']
    }
    
    for theme, keywords in theme_mapping.items():
        if theme in query_lower:
            return {"keywords": {"resume": keywords}}
    
    # Si aucun pattern spécifique, essayer de détecter le champ principal
    if 'livre' in query_lower or 'roman' in query_lower:
        # Extraire le mot-clé principal après "de/sur"
        match = re.search(r'(?:de|sur)\s+([a-zà-ÿ\s]+)', query_lower)
        if match:
            keyword = match.group(1).strip()
            return {"keywords": {"categorie": [keyword]}}
    
    # Fallback générique
    words = query_lower.replace('"', '').split()
    main_words = [w for w in words if len(w) > 3 and w not in ['livres', 'romans', 'cherche', 'veux', 'avez', 'vous', 'pour']]
    
    if main_words:
        return {"keywords": {"categorie": main_words[:3]}}
    
    return {"keywords": {"categorie": ["general"]}}

def generate_validation_data():
    """
    Génère un fichier de validation avec les résultats attendus
    """
    print("🎯 Génération des données de validation pour get_keywords_with_gpt")
    print("=" * 65)
    
    # Extraire les requêtes
    queries = extract_queries_from_markdown()
    
    if not queries:
        print("❌ Aucune requête trouvée")
        return
    
    print(f"📝 Analyse de {len(queries)} requêtes...")
    
    validation_data = []
    
    for i, query in enumerate(queries, 1):
        print(f"[{i:2d}] {query}")
        
        # Analyser la requête
        expected_result = analyze_query(query)
        print(f"    → {json.dumps(expected_result, ensure_ascii=False)}")
        
        # Créer l'entrée de validation
        validation_entry = {
            "query": query,
            "expected_result": expected_result,
            "analysis_notes": "",  # À remplir manuellement si nécessaire
            "priority": "normal",  # normal, high, low
            "test_category": classify_test_category(query),
            "validation_status": "to_validate"  # to_validate, validated, needs_review
        }
        
        validation_data.append(validation_entry)
    
    # Créer le fichier de validation complet
    output = {
        "metadata": {
            "generation_date": "2025-08-08",
            "function_tested": "get_keywords_with_gpt",
            "total_test_cases": len(validation_data),
            "description": "Données de validation générées automatiquement basées sur l'analyse des requêtes"
        },
        "test_guidelines": {
            "validation_criteria": [
                "Le champ sélectionné est-il le plus approprié pour la requête?",
                "Les mots-clés extraits sont-ils pertinents et complets?",
                "Les synonymes/variantes sont-ils appropriés?",
                "Le format JSON est-il correct et cohérent?"
            ],
            "field_priorities": {
                "auteur": "Priorité haute - noms d'auteurs explicites",
                "titre": "Priorité haute - titres de livres spécifiques", 
                "categorie": "Priorité moyenne - genres et catégories",
                "langue": "Priorité moyenne - langues spécifiées",
                "resume": "Priorité basse - thèmes et concepts généraux",
                "pages": "Priorité basse - critères de format"
            }
        },
        "test_cases": validation_data
    }
    
    # Sauvegarder
    with open("keywords_validation_expected.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Statistiques
    categories = {}
    for entry in validation_data:
        cat = entry["test_category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📊 Statistiques:")
    for cat, count in categories.items():
        print(f"   {cat}: {count} requêtes")
    
    print(f"\n💾 Fichier généré: keywords_validation_expected.json")
    print(f"\n📋 Prochaines étapes:")
    print("1. Examiner le fichier généré")
    print("2. Ajuster manuellement les résultats attendus si nécessaire")
    print("3. Utiliser ce fichier comme référence pour les tests")
    print("4. Implémenter un script de validation automatique")

def classify_test_category(query):
    """Classifie le type de test pour organiser les validations"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['de ', 'œuvres', 'tout de']):
        if any(name.istitle() for name in query.split()):
            return "author_query"
    
    if any(word in query_lower for word in ['romans', 'livres']):
        if any(genre in query_lower for genre in ['science-fiction', 'fantasy', 'policier', 'romance', 'thriller']):
            return "genre_query"
    
    if any(word in query_lower for word in ['anglais', 'français', 'espagnol', 'italien']):
        return "language_query"
    
    if 'pages' in query_lower:
        return "format_query"
    
    if query.startswith('"') and query.endswith('"'):
        return "title_query"
    
    if any(word in query_lower for word in ['sur', 'traitant', 'parlent']):
        return "theme_query"
    
    return "general_query"

if __name__ == "__main__":
    generate_validation_data()
