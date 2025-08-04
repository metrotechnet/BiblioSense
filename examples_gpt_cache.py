# Exemple d'utilisation du cache GPT - BiblioSense Phase 2

"""
Ce fichier montre les différentes façons d'utiliser le cache GPT 
avec get_catagories_with_gpt dans BiblioSense.
"""

from utils.gpt_cache import GPTCache
from utils.gpt_services import get_catagories_with_gpt, get_catagories_with_gpt_cached, create_cached_gpt_function

# ====================================================================
# MÉTHODE 1: Utilisation directe avec cache (comme dans app.py)
# ====================================================================

def example_direct_cache_usage(gpt_cache, taxonomy_data, openai_client):
    """Exemple d'utilisation directe du cache"""
    query = "livres de science fiction"
    
    # Appel avec cache
    categories = get_catagories_with_gpt_cached(
        text=query,
        taxonomy_data=taxonomy_data,
        openai_client=openai_client,
        gpt_cache=gpt_cache
    )
    
    return categories

# ====================================================================
# MÉTHODE 2: Utilisation avec factory function (recommandée)
# ====================================================================

def example_factory_usage():
    """Exemple avec factory function - plus propre"""
    
    # Configuration initiale (une seule fois)
    gpt_cache = GPTCache(max_size=500, ttl_seconds=3600)
    
    # Créer la fonction pré-configurée
    cached_gpt_call = create_cached_gpt_function(
        gpt_cache=gpt_cache,
        openai_client=openai_client,  # Votre client OpenAI
        taxonomy_data=taxonomy_data   # Vos données de taxonomie
    )
    
    # Utilisation simple - juste passer le texte
    query = "romans d'aventure"
    categories = cached_gpt_call(query)
    
    return categories

# ====================================================================
# MÉTHODE 3: Intégration dans une classe (pour applications complexes)
# ====================================================================

class BiblioSenseGPTService:
    """Service GPT avec cache intégré"""
    
    def __init__(self, openai_client, taxonomy_data, cache_size=500, cache_ttl=3600):
        self.openai_client = openai_client
        self.taxonomy_data = taxonomy_data
        self.gpt_cache = GPTCache(max_size=cache_size, ttl_seconds=cache_ttl)
        
        # Créer la fonction cachée
        self.classify_query = create_cached_gpt_function(
            self.gpt_cache, 
            self.openai_client, 
            self.taxonomy_data
        )
    
    def get_categories(self, user_query):
        """Interface simple pour classifier une requête"""
        return self.classify_query(user_query)
    
    def clear_cache(self):
        """Vider le cache"""
        self.gpt_cache.cache.clear()
        self.gpt_cache.reset_stats()
    
    def get_cache_stats(self):
        """Obtenir les statistiques du cache"""
        return self.gpt_cache.get_stats()
    
    def is_cache_healthy(self, min_hit_rate=50.0):
        """Vérifier si le cache est efficace"""
        stats = self.get_cache_stats()
        return stats['hit_rate_percent'] >= min_hit_rate

# ====================================================================
# MÉTHODE 4: Décorateur pour cache automatique
# ====================================================================

def with_gpt_cache(cache_size=500, cache_ttl=3600):
    """Décorateur pour ajouter automatiquement le cache à une fonction GPT"""
    
    def decorator(gpt_function):
        cache = GPTCache(max_size=cache_size, ttl_seconds=cache_ttl)
        
        def wrapper(text, taxonomy_data, openai_client):
            # Essayer le cache
            cached_result = cache.get(text, taxonomy_data)
            if cached_result:
                return cached_result
            
            # Appeler la fonction originale
            result = gpt_function(text, taxonomy_data, openai_client)
            
            # Mettre en cache
            cache.set(text, taxonomy_data, result)
            
            return result
        
        # Ajouter les stats au wrapper
        wrapper.get_cache_stats = lambda: cache.get_stats()
        wrapper.clear_cache = lambda: cache.cache.clear()
        
        return wrapper
    
    return decorator

# Exemple d'utilisation du décorateur
@with_gpt_cache(cache_size=100, cache_ttl=1800)
def my_custom_gpt_function(text, taxonomy_data, openai_client):
    """Ma fonction GPT personnalisée avec cache automatique"""
    return get_catagories_with_gpt(text, taxonomy_data, openai_client)

# ====================================================================
# EXEMPLES D'UTILISATION DANS UNE APPLICATION FLASK
# ====================================================================

def flask_route_example():
    """Exemple d'utilisation dans une route Flask"""
    
    # Méthode utilisée dans app.py (la plus simple)
    @app.route("/filter", methods=["POST"])
    def filter_with_cache():
        data = request.get_json()
        text = data.get("query", "")
        
        # Utilisation de la fonction pré-configurée
        categories = cached_gpt_classifier(text)  # Variable globale
        
        return jsonify(categories)

def performance_monitoring_example():
    """Exemple avec monitoring des performances"""
    
    cache = GPTCache(max_size=500)
    
    # Plusieurs requêtes pour tester le cache
    queries = [
        "science fiction",
        "romans historiques", 
        "science fiction",  # Répétition pour test cache
        "biographies",
        "romans historiques"  # Répétition pour test cache
    ]
    
    for i, query in enumerate(queries):
        print(f"\nRequête {i+1}: {query}")
        
        start_time = time.time()
        result = get_catagories_with_gpt_cached(query, taxonomy_data, openai_client, cache)
        end_time = time.time()
        
        print(f"Temps: {end_time - start_time:.3f}s")
        
        # Stats du cache après chaque requête
        stats = cache.get_stats()
        print(f"Hit rate: {stats['hit_rate_percent']:.1f}%")

# ====================================================================
# CONFIGURATION RECOMMANDÉE POUR PRODUCTION
# ====================================================================

def production_setup():
    """Configuration recommandée pour la production"""
    
    # Cache plus grand et TTL plus long pour la production
    production_cache = GPTCache(
        max_size=1000,      # Plus de requêtes en cache
        ttl_seconds=7200    # 2 heures de cache
    )
    
    # Fonction optimisée pour la production
    production_gpt_classifier = create_cached_gpt_function(
        gpt_cache=production_cache,
        openai_client=openai_client,
        taxonomy_data=taxonomy_data
    )
    
    return production_gpt_classifier

if __name__ == "__main__":
    print("📚 Exemples d'utilisation du cache GPT pour BiblioSense")
    print("Consultez ce fichier pour voir les différentes méthodes d'implémentation.")
