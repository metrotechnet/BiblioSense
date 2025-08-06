"""
Services GPT pour BiblioSense
Contient les fonctions d'interaction avec OpenAI pour la classification et la description.
"""

import json
import os
import time
from openai import OpenAI

# -------------------- Query Logging Functions --------------------

def log_query(user_id, query_text, results_count, response_time, gpt_categories=None, score_stats=None, query_log_file="dbase/query_log.json"):
    """
    Log search queries to a file for analysis
    
    Args:
        user_id (str): User session ID
        query_text (str): The search query
        results_count (int): Number of results found
        response_time (float): Time taken to process the query
        gpt_categories (dict): GPT classification results (optional)
        score_stats (dict): Score statistics from book filtering (optional)
        query_log_file (str): Path to the log file (default: "dbase/query_log.json")
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(query_log_file), exist_ok=True)
        
        # Load existing logs
        logs = []
        if os.path.exists(query_log_file):
            try:
                with open(query_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logs = []
        
        # Create new log entry
        log_entry = {
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "user_id": user_id,
            "query": query_text,
            "results_count": results_count,
            "response_time": response_time,
            "success": results_count > 0
        }
        
        # Add GPT categories if provided (but keep it lightweight)
        if gpt_categories:
            log_entry["has_gpt_classification"] = True
            log_entry["description"] = gpt_categories.get("Description", "")[:200]  # Limit description length
            
            # Add mots-clés (keywords) information
            if "Mots-clés" in gpt_categories:
                mots_cles = gpt_categories["Mots-clés"]
                log_entry["mots_cles"] = {
                    "fields_used": list(mots_cles.keys()),
                    "total_keywords": sum(len(keywords) if isinstance(keywords, list) else 1 for keywords in mots_cles.values()),
                    "keywords_by_field": {field: keywords if isinstance(keywords, list) else [keywords] for field, keywords in mots_cles.items()}
                }
            
            # Add taxonomie information
            if "Taxonomie" in gpt_categories:
                taxonomie = gpt_categories["Taxonomie"]
                log_entry["taxonomie"] = {
                    "categories_used": list(taxonomie.keys()),
                    "total_categories": len(taxonomie),
                    "taxonomy_structure": taxonomie  # Store the full taxonomy structure for analysis
                }
        else:
            log_entry["has_gpt_classification"] = False
        
        # Add score statistics if provided
        if score_stats:
            log_entry["score_stats"] = score_stats
        
        # Add to logs
        logs.append(log_entry)
        
        # Keep only last 1000 queries to prevent file from growing too large
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        # Save logs
        with open(query_log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"⚠️  Error logging query: {e}")
        # Don't raise exception - logging should not break the main functionality

# -------------------- GPT Service Functions --------------------


def get_catagories_with_gpt_cached(text, taxonomy_data, openai_client, gpt_cache=None):
    """
    Version cachée de get_catagories_with_gpt qui utilise le cache GPT
    
    Args:
        text (str): Texte de la requête utilisateur
        taxonomy_data (dict): Données de taxonomie
        openai_client: Client OpenAI
        gpt_cache: Instance du cache GPT (optionnel)
    
    Returns:
        dict: Catégories et description de la requête
    """
    if gpt_cache is None:
        # Fallback vers l'appel direct si pas de cache
        return get_catagories_with_gpt(text, taxonomy_data, openai_client)
    
    # Essayer le cache d'abord
    start_time = time.time()
    categories = gpt_cache.get(text, taxonomy_data)
    
    if categories:
        cache_time = time.time() - start_time
        print(f"⚡ GPT response from cache: {cache_time:.3f}s")
        return categories
    else:
        # Cache miss - appeler GPT et stocker le résultat
        gpt_start = time.time()
        categories = get_catagories_with_gpt(text, taxonomy_data, openai_client)
        gpt_time = time.time() - gpt_start
        
        # Stocker dans le cache pour les requêtes futures
        gpt_cache.set(text, taxonomy_data, categories)
        print(f"⏱️  GPT categories classification (new): {gpt_time:.2f}s")
        
        return categories


def create_cached_gpt_function(gpt_cache, openai_client, taxonomy_data):
    """
    Factory function pour créer une fonction GPT pré-configurée avec cache
    
    Args:
        gpt_cache: Instance du cache GPT
        openai_client: Client OpenAI
        taxonomy_data: Données de taxonomie
    
    Returns:
        function: Fonction pré-configurée qui ne nécessite que le texte
    """
    def cached_gpt_call(text):
        return get_catagories_with_gpt_cached(text, taxonomy_data, openai_client, gpt_cache)
    
    return cached_gpt_call


def get_catagories_with_gpt(text, taxonomy, openai_client):
    """
    Use GPT to classify a book query into taxonomy categories.

    Args:
        text (str): User query or book description.
        taxonomy (list): Taxonomy nodes for context.
        openai_client (OpenAI): Instance du client OpenAI configuré.

    Returns:
        list or dict: Parsed GPT response as JSON.
    """
    prompt = f"""
        Tu es un classificateur de requêtes spécialisé dans la recherche de livres. 
        Analyse la requête ci-dessous et renvoie uniquement un objet JSON (aucun texte hors JSON) 
        qui contient les catégories pertinentes de la taxonomie ainsi que les mots-clés extraits.
        Par la suite, transforme la taxonomie trouvée en une description simple et spécifique à la requête, claire et fluide en français, destinée à un lecteur non spécialiste. 
        Ajoute une phrase de description générale sur la taxonomie des livres.
        Exprime-toi avec des phrases complètes et évite tout jargon technique.

        ### Taxonomie :
        {json.dumps(taxonomy, ensure_ascii=False, indent=2)}

        ### Champs disponibles pour les mots-clés :
        - titre : titre du livre
        - auteur : nom(s) d’auteur(s)
        - resume : résumé ou description du livre (important)
        - editeur : éditeur
        - langue : langue
        - categorie : catégorie ou domaine
        - parution : date de publication
        - pages : nombre de pages

        ### Requête utilisateur :
        {text}

        ### Instructions spéciales pour les mots-clés :
        - Pour chaque champ pertinent, fournis une liste de mots-clés synonymes et variantes
        - Inclus les variantes orthographiques, les synonymes, les termes connexes
        - Exemples : "romantique" → ["romantique", "sentimental", "romance", "amoureux", "passion"]
        - Exemples : "science-fiction" → ["science-fiction", "sci-fi", "SF", "anticipation", "futuriste"]
        - Exemples : "policier" → ["policier", "polar", "thriller", "enquête", "crime", "detective"]

        ### Format de réponse attendu (strictement au format JSON) :
        {{
        "Taxonomie": {{structure taxonomique filtrée}},
        "Mots-clés": {{
            "titre": ["mot_clé_1", "synonyme_1", "variante_1"],
            "auteur": ["nom_auteur", "variante_nom"],
            "resume": ["concept_1", "synonyme_1", "terme_connexe"],
            "editeur": ["nom_editeur"],
            "langue": ["français", "french"],
            "categorie": ["genre_1", "synonyme_genre", "variante_genre"],
            "parution": ["année", "période"],
            "pages": ["nombre_pages"]
        }},
        "Description": "Texte descriptif en français, clair et fluide."
        }}
        
        ### Exemples de synonymes par domaine :
        - Romance : romantique, sentimental, amoureux, passion, coeur, amour
        - Thriller : suspense, polar, policier, enquête, crime, mystère
        - Fantasy : fantastique, merveilleux, magie, épique, heroic-fantasy
        - Science-fiction : sci-fi, SF, anticipation, futuriste, technologique
        - Historique : période, époque, siècle, chronique, passé
        - Jeunesse : enfant, ado, adolescent, young adult, junior

        ### Exemple de style attendu pour la description :
        "Les livres sont ..."

        - N'inclus que les champs pertinents pour la requête.
        - Si une information est absente, omets simplement le champ.
        - Assure-toi que chaque liste de mots-clés contient au moins 2-3 variantes quand c'est pertinent.
        """

    try:
        # Call OpenAI GPT model with the constructed prompt
        response = openai_client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        # Extract the text output from the response
        gpt_response = response.output_text
        # Remove possible code block wrappers from GPT output
        gpt_response = gpt_response.replace("```json", "").replace("```", "").strip()
        # Parse the JSON response
        return json.loads(gpt_response)
    except Exception as e:
        # Raise a runtime error if anything goes wrong
        raise RuntimeError(f"Erreur : {str(e)}")

