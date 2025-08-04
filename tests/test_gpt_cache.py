# Test du cache GPT pour BiblioSense
import time
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.gpt_cache import GPTCache
from utils.gpt_services import get_catagories_with_gpt_cached, create_cached_gpt_function

def test_gpt_cache_performance():
    """Test des performances du cache GPT"""
    
    # Simuler des données de test
    test_taxonomy = {
        "Sciences": ["Physique", "Chimie", "Biologie"],
        "Littérature": ["Roman", "Poésie", "Théâtre"]
    }
    
    # Créer une instance de cache
    cache = GPTCache(max_size=10, ttl_seconds=3600)
    
    # Mock de la fonction GPT pour les tests
    def mock_gpt_call(text, taxonomy_data, client):
        time.sleep(0.5)  # Simuler un délai GPT
        return {
            "Description": f"Recherche pour: {text}",
            "Mots-clés": {"titre": [text.lower()]},
            "Taxonomie": {"Sciences": {"Physique": ["optique", "mécanique"]}}
        }
    
    # Remplacer temporairement la fonction GPT réelle
    original_function = None
    try:
        from utils import gpt_services
        original_function = gpt_services.get_catagories_with_gpt
        gpt_services.get_catagories_with_gpt = mock_gpt_call
        
        test_query = "livres de science fiction"
        
        print("🧪 Test 1: Premier appel (cache miss)")
        start_time = time.time()
        result1 = get_catagories_with_gpt_cached(test_query, test_taxonomy, None, cache)
        first_call_time = time.time() - start_time
        print(f"   Temps: {first_call_time:.3f}s")
        print(f"   Résultat: {result1['Description']}")
        
        print("\n🧪 Test 2: Deuxième appel (cache hit)")
        start_time = time.time()
        result2 = get_catagories_with_gpt_cached(test_query, test_taxonomy, None, cache)
        second_call_time = time.time() - start_time
        print(f"   Temps: {second_call_time:.3f}s")
        print(f"   Résultat: {result2['Description']}")
        
        # Vérifier la cohérence
        if result1 == result2:
            print("   ✅ Résultats identiques")
        else:
            print("   ❌ Résultats différents")
        
        # Calculer l'amélioration
        speedup = first_call_time / second_call_time if second_call_time > 0 else 0
        print(f"\n📊 Amélioration de performance: {speedup:.1f}x plus rapide")
        
        # Test des statistiques du cache
        stats = cache.get_stats()
        print(f"\n📈 Statistiques du cache:")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Cache misses: {stats['cache_misses']}")
        print(f"   Hit rate: {stats['hit_rate_percent']:.1f}%")
        print(f"   Taille du cache: {stats['cache_size']}")
        
        # Test de la factory function
        print("\n🧪 Test 3: Factory function")
        cached_function = create_cached_gpt_function(cache, None, test_taxonomy)
        
        start_time = time.time()
        result3 = cached_function("romans français")
        factory_time = time.time() - start_time
        print(f"   Temps (nouveau query): {factory_time:.3f}s")
        
        start_time = time.time()
        result4 = cached_function("romans français")
        factory_cached_time = time.time() - start_time
        print(f"   Temps (cache hit): {factory_cached_time:.3f}s")
        
        # Statistiques finales
        final_stats = cache.get_stats()
        print(f"\n📈 Statistiques finales:")
        print(f"   Cache hits: {final_stats['cache_hits']}")
        print(f"   Cache misses: {final_stats['cache_misses']}")
        print(f"   Hit rate: {final_stats['hit_rate_percent']:.1f}%")
        
        if final_stats['hit_rate_percent'] > 0:
            print("✅ Test du cache GPT réussi!")
            return True
        else:
            print("❌ Test du cache GPT échoué!")
            return False
            
    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        return False
    finally:
        # Restaurer la fonction originale
        if original_function:
            gpt_services.get_catagories_with_gpt = original_function

def test_cache_invalidation():
    """Test de l'invalidation du cache"""
    print("\n🧪 Test d'invalidation du cache")
    
    # Cache avec TTL très court pour les tests
    cache = GPTCache(max_size=5, ttl_seconds=1)
    
    test_data = {"test": "data"}
    
    # Ajouter une entrée
    cache.set("test_query", test_data, {"result": "test"})
    
    # Vérifier qu'elle existe
    result = cache.get("test_query", test_data)
    if result:
        print("   ✅ Cache fonctionne immédiatement")
    else:
        print("   ❌ Cache ne fonctionne pas")
        return False
    
    # Attendre l'expiration
    print("   Attente de l'expiration du cache...")
    time.sleep(1.5)
    
    # Vérifier que l'entrée a expiré
    result = cache.get("test_query", test_data)
    if result is None:
        print("   ✅ Cache expiré correctement")
        return True
    else:
        print("   ❌ Cache n'a pas expiré")
        return False

if __name__ == "__main__":
    print("🚀 Test du système de cache GPT pour BiblioSense")
    print("=" * 60)
    
    try:
        # Test des performances
        perf_success = test_gpt_cache_performance()
        
        # Test de l'invalidation
        invalidation_success = test_cache_invalidation()
        
        print("\n" + "=" * 60)
        if perf_success and invalidation_success:
            print("🎉 Tous les tests du cache GPT ont réussi!")
        else:
            print("⚠️  Certains tests ont échoué.")
            
    except Exception as e:
        print(f"💥 Erreur critique dans les tests: {e}")
        import traceback
        traceback.print_exc()
