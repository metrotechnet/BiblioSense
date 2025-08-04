# Test rapide pour vérifier que les blocages sont résolus
import time
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cache_no_blocking():
    """Test que le cache ne bloque plus"""
    
    print("🧪 Test de non-blocage du cache GPT")
    
    try:
        from utils.gpt_cache import GPTCache
        from utils.performance_monitor import PerformanceMonitor
        
        # Test du cache
        print("   Testing GPTCache...")
        cache = GPTCache(max_size=10, ttl_seconds=60)
        
        start_time = time.time()
        stats = cache.get_stats_fast()
        fast_time = time.time() - start_time
        print(f"   ✅ get_stats_fast: {fast_time:.3f}s")
        
        start_time = time.time()
        stats = cache.get_stats(cleanup_expired=False)
        safe_time = time.time() - start_time
        print(f"   ✅ get_stats(safe): {safe_time:.3f}s")
        
        # Test du performance monitor
        print("   Testing PerformanceMonitor...")
        monitor = PerformanceMonitor()
        
        start_time = time.time()
        perf_stats = monitor.get_stats(safe_mode=True)
        monitor_time = time.time() - start_time
        print(f"   ✅ get_stats(safe_mode): {monitor_time:.3f}s")
        
        # Vérifier que tous les appels sont rapides
        if fast_time < 0.1 and safe_time < 0.1 and monitor_time < 0.1:
            print("🎉 Tous les tests de non-blocage ont réussi!")
            return True
        else:
            print("⚠️  Certains appels sont encore lents:")
            print(f"     Cache fast: {fast_time:.3f}s")
            print(f"     Cache safe: {safe_time:.3f}s")
            print(f"     Monitor safe: {monitor_time:.3f}s")
            return False
            
    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_functionality():
    """Test que le cache fonctionne toujours correctement"""
    
    print("\n🧪 Test de fonctionnalité du cache")
    
    try:
        from utils.gpt_cache import GPTCache
        
        cache = GPTCache(max_size=5, ttl_seconds=3600)
        
        # Test d'ajout et récupération
        test_data = {"test": "value"}
        test_response = {"result": "test_response"}
        
        # Ajouter au cache
        success = cache.set("test query", test_data, test_response)
        if success:
            print("   ✅ Cache set réussi")
        else:
            print("   ❌ Cache set échoué")
            return False
        
        # Récupérer du cache
        cached_result = cache.get("test query", test_data)
        if cached_result == test_response:
            print("   ✅ Cache get réussi")
        else:
            print("   ❌ Cache get échoué")
            return False
        
        # Test des statistiques
        stats = cache.get_stats_fast()
        if stats['cache_hits'] > 0 and stats['cache_size'] > 0:
            print("   ✅ Statistiques correctes")
            print(f"      Hits: {stats['cache_hits']}, Size: {stats['cache_size']}")
            return True
        else:
            print("   ❌ Statistiques incorrectes")
            return False
            
    except Exception as e:
        print(f"❌ Erreur pendant le test de fonctionnalité: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test de résolution des blocages - BiblioSense Phase 2")
    print("=" * 60)
    
    # Test de non-blocage
    no_blocking = test_cache_no_blocking()
    
    # Test de fonctionnalité
    functionality = test_cache_functionality()
    
    print("\n" + "=" * 60)
    if no_blocking and functionality:
        print("🎉 Tous les tests ont réussi! Le cache est optimisé pour le debug.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez l'implémentation.")
    
    print("📋 Utilisation recommandée:")
    print("   - En développement: utilisez get_stats_fast() et safe_mode=True")
    print("   - En production: utilisez get_stats() avec cleanup_expired=True")
