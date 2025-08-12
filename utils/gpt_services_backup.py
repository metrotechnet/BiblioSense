"""
Services GPT pour BiblioSense
Contient les fonctions d'interaction avec OpenAI pour la classification et la description.
"""

import json
import os
import time
from openai import OpenAI

# -------------------- Query Logging Functions --------------------

def log_query(user_id, query_text, results_count, response_time, gpt_data=None, score_stats=None, query_log_file="dbase/query_log.json"):
    """
    Log search queries to a file for analysis
    
    Args:
        user_id (str): User session ID
        query_text (str): The search query
        results_count (int): Number of results found
        response_time (float): Time taken to process the query
        gpt_data (dict): GPT data containing Mots-clés and Description (optional)
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
        
        # Add GPT data if provided (but keep it lightweight)
        if gpt_data:
            log_entry["has_gpt_classification"] = True
            log_entry["description"] = gpt_data.get("Description", "")[:200]  # Limit description length
            
            # Add mots-clés (keywords) information
            if "keywords" in gpt_data:
                mots_cles = gpt_data["keywords"]
                log_entry["mots_cles"] = {
                    "fields_used": list(mots_cles.keys()),
                    "total_keywords": sum(len(keywords) if isinstance(keywords, list) else 1 for keywords in mots_cles.values()),
                    "keywords_by_field": {field: keywords if isinstance(keywords, list) else [keywords] for field, keywords in mots_cles.items()}
                }
            
            # Add taxonomie information
            if "Taxonomie" in gpt_data:
                taxonomie = gpt_data["Taxonomie"]
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
        
        return categories


def get_keywords_with_gpt_cached(text, taxonomy_data, openai_client, gpt_cache=None):
    """
    Version cachée de get_keywords_with_gpt qui utilise le cache GPT
    
    Args:
        text (str): Texte de la requête utilisateur
        taxonomy_data (dict): Données de taxonomie
        openai_client: Client OpenAI
        gpt_cache: Instance du cache GPT (optionnel)
    
    Returns:
        dict: Mots-clés extraits de la requête
    """
    if gpt_cache is None:
        # Fallback vers l'appel direct si pas de cache
        return get_keywords_with_gpt(text, taxonomy_data, openai_client)
    
    # Créer une clé de cache spécifique pour les keywords (différente des categories)
    cache_key_suffix = "_keywords"
    
    # Essayer le cache d'abord
    start_time = time.time()
    # Modifier temporairement le texte pour créer une clé différente
    cache_text = text + cache_key_suffix
    keywords = gpt_cache.get(cache_text, taxonomy_data)
    
    if keywords:
        cache_time = time.time() - start_time
        print(f"⚡ GPT keywords from cache: {cache_time:.3f}s")
        return keywords
    else:
        # Cache miss - appeler GPT et stocker le résultat
        gpt_start = time.time()
        keywords = get_keywords_with_gpt(text, taxonomy_data, openai_client)
        gpt_time = time.time() - gpt_start
        
        # Stocker dans le cache pour les requêtes futures
        gpt_cache.set(cache_text, taxonomy_data, keywords)
        
        return keywords


def get_description_with_gpt_cached(text, taxonomy_data, openai_client, gpt_cache=None):
    """
    Version cachée de get_description_with_gpt qui utilise le cache GPT

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
        return get_description_with_gpt(text, taxonomy_data, openai_client)
    
    # Essayer le cache d'abord
    start_time = time.time()
    description = gpt_cache.get(text, taxonomy_data)

    if description:
        cache_time = time.time() - start_time
        print(f"⚡ GPT response from cache: {cache_time:.3f}s")
        return description
    else:
        # Cache miss - appeler GPT et stocker le résultat
        gpt_start = time.time()
        description = get_description_with_gpt(text, taxonomy_data, openai_client)
        gpt_time = time.time() - gpt_start
        
        # Stocker dans le cache pour les requêtes futures
        gpt_cache.set(text, taxonomy_data, description)

        return description


def create_cached_gpt_function(gpt_cache, openai_client, taxonomy_data):
    """
    Factory function pour créer des fonctions GPT pré-configurées avec cache
    
    Args:
        gpt_cache: Instance du cache GPT
        openai_client: Client OpenAI
        taxonomy_data: Données de taxonomie
    
    Returns:
        tuple: (cached_classifier_function, cached_keywords_function)
    """
    def cached_classifier(text):
        return get_catagories_with_gpt_cached(text, taxonomy_data, openai_client, gpt_cache)
    
    def cached_keywords(text):
        return get_keywords_with_gpt_cached(text, taxonomy_data, openai_client, gpt_cache)

    def cached_description(text,taxonomy_data):
        return get_description_with_gpt_cached(text, taxonomy_data, openai_client, gpt_cache)

    return cached_classifier, cached_keywords, cached_description


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
  
    # OPTIMIZED PROMPT (8 lines) - SAME FUNCTIONALITY, BETTER PERFORMANCE
    prompt = f"""Classifie cette requête de livre selon la taxonomie donnée. Retourne seulement les catégories pertinentes.

        Requête: "{text}"
        Taxonomie: {json.dumps(taxonomy, ensure_ascii=False)}

        Règles: Sois précis et ne sur-classifie pas. Ne retourne que les champs non nuls.

        Format JSON: Respecte exactement la structure de la taxonomie fournie."""

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

def get_keywords_with_gpt(text, taxonomy, openai_client):
    """
    Use GPT to extract keywords from a book query.

    Args:
        text (str): User query or book description.
        taxonomy (list): Taxonomy nodes for context.
        openai_client (OpenAI): Instance du client OpenAI configuré.

    Returns:
        dict: Parsed GPT response as JSON with keywords.
    """

#    "type": ["book, livre, livre audio etc.", "variante"], // si type mentionné

    # OPTIMIZED PROMPT (6 lines) - SAME FUNCTIONALITY, BETTER PERFORMANCE  
    prompt = f"""Extrait les mots-clés de recherche pour cette requête de livre. 
                 Sélectionne uniquement le champ le plus pertinent.
                 Éliminer les mots ambigus ou à double sens (ex : son, sa)


        Requête: "{text}"
        Champs possibles: titre, auteur, resume, editeur, langue, categorie, parution, pages

        Format attendu (JSON) :
        {{
            "keywords": {{
                "auteur": ["nom_exact", "variante"], // si auteur présent
                "categorie": ["genre", "synonymes"], // si genre présent
                "resume": ["concept", "synonymes"], // si thème/sujet présent
                "langue": ["langue"], // si langue précisée
                "parution": ["période"], // si date précisée
                "pages": ["nombre_de_pages", "plus de...", "moins de..."], // si pages précisées
            }}
        }}
        Règles :
        - Inclure uniquement les champs explicitement mentionnés dans la requête
        - Ne retourner que les champs non vides
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
        parsed_response = json.loads(gpt_response)


        return parsed_response
        
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON decode error: {e}")
        print(f"⚠️  GPT response was: {gpt_response}")
        # Return a fallback response
        return {"keywords": {"categorie": ["general"]}}
    except Exception as e:
        # Raise a runtime error if anything goes wrong
        raise RuntimeError(f"Erreur : {str(e)}")

def get_description_with_gpt(text, taxonomy, openai_client):
    """
    Use GPT to classify a book query into taxonomy categories.

    Args:
        text (str): User query or book description.
        taxonomy (list): Taxonomy nodes for context.
        openai_client (OpenAI): Instance du client OpenAI configuré.

    Returns:
        list or dict: Parsed GPT response as JSON.
    """
 
    # OPTIMIZED PROMPT (4 lines) - SAME FUNCTIONALITY, BETTER PERFORMANCE
    prompt = f"""Créé une description engageante (2-3 phrases) pour cette recherche de livres basée sur la requête et taxonomie.

        Requête: "{text}"
        Taxonomie: {json.dumps(taxonomy, ensure_ascii=False)}

        Format JSON: {{"Description": "description ici"}}
        Règle: Commence par "Les livres..."""

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
