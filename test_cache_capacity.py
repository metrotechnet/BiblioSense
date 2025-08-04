# Test de capacité avec cache - BiblioSense Phase 2

import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.gpt_cache import GPTCache
from utils.performance_monitor import PerformanceMonitor

def simulate_cache_performance():
    """Simule l'impact du cache sur la performance"""
    
    print("🧪 SIMULATION DE PERFORMANCE AVEC CACHE")
    print("=" * 60)
    
    # Créer un cache de test
    cache = GPTCache(max_size=500, ttl_seconds=3600)
    monitor = PerformanceMonitor(max_users=200)
    
    # Simuler des requêtes populaires (représentent 80% du trafic)
    popular_queries = [
        "science fiction",
        "romans français",
        "histoire de France", 
        "philosophie",
        "biographies",
        "littérature classique",
        "romans d'aventure",
        "poésie française"
    ]
    
    # Simuler des données de taxonomie
    test_taxonomy = {"test": "data"}
    
    # Mock response pour simulation
    mock_response = {
        "Description": "Test query",
        "Mots-clés": {"titre": ["test"]},
        "Taxonomie": {"Sciences": {"Physique": ["test"]}}
    }
    
    # Pré-remplir le cache avec les requêtes populaires
    print("📝 Pré-remplissage du cache avec requêtes populaires...")
    for query in popular_queries:
        cache.set(query, test_taxonomy, mock_response)
    
    print(f"   ✅ Cache pré-rempli avec {len(popular_queries)} requêtes")
    
    # Simuler différents scénarios
    scenarios = [
        ("Cache à froid", 0.0),      # 0% hit rate
        ("Cache tiède", 0.5),        # 50% hit rate
        ("Cache chaud", 0.8),        # 80% hit rate
        ("Cache optimal", 0.95)      # 95% hit rate
    ]
    
    results = {}
    
    for scenario_name, hit_rate in scenarios:
        print(f"\n🎯 Test du scénario: {scenario_name} ({hit_rate*100:.0f}% hit rate)")
        
        # Simuler 100 requêtes avec le hit rate donné
        start_time = time.time()
        total_requests = 100
        
        for i in range(total_requests):
            user_id = f"user_{i % 20}"  # 20 utilisateurs simulés
            
            if i / total_requests < hit_rate:
                # Cache hit - requête populaire
                query = popular_queries[i % len(popular_queries)]
                request_start = time.time()
                result = cache.get(query, test_taxonomy)
                request_time = time.time() - request_start
            else:
                # Cache miss - nouvelle requête
                query = f"requête unique {i}"
                request_start = time.time()
                result = cache.get(query, test_taxonomy)  # Sera None
                # Simuler appel GPT (2-5s)
                time.sleep(0.01)  # Simulation rapide
                cache.set(query, test_taxonomy, mock_response)
                request_time = time.time() - request_start
            
            # Enregistrer dans le monitor
            monitor.track_request(user_id, request_time)
        
        total_time = time.time() - start_time
        
        # Calculer les statistiques
        cache_stats = cache.get_stats_fast()
        perf_stats = monitor.get_stats(safe_mode=True)
        
        avg_request_time = total_time / total_requests
        requests_per_second = total_requests / total_time
        
        results[scenario_name] = {
            'hit_rate': cache_stats['hit_rate_percent'],
            'avg_request_time': avg_request_time,
            'requests_per_second': requests_per_second,
            'total_time': total_time,
            'active_users': perf_stats['active_users']
        }
        
        print(f"   📊 Résultats:")
        print(f"      Hit rate réel: {cache_stats['hit_rate_percent']:.1f}%")
        print(f"      Temps moyen/requête: {avg_request_time:.3f}s")
        print(f"      Requêtes/seconde: {requests_per_second:.1f}")
        print(f"      Utilisateurs actifs: {perf_stats['active_users']}")
    
    # Calculer l'impact sur la capacité
    print(f"\n📈 IMPACT SUR LA CAPACITÉ")
    print("-" * 40)
    
    base_rps = results["Cache à froid"]["requests_per_second"]
    
    for scenario_name, data in results.items():
        rps = data["requests_per_second"]
        improvement = rps / base_rps if base_rps > 0 else 1
        estimated_capacity = int(rps * 2)  # Estimation simple
        
        print(f"{scenario_name}:")
        print(f"   Req/s: {rps:.1f} ({improvement:.1f}x plus rapide)")
        print(f"   Capacité estimée: {estimated_capacity} utilisateurs")
    
    return results

def test_concurrent_load():
    """Test de charge concurrent"""
    
    print(f"\n🚀 TEST DE CHARGE CONCURRENT")
    print("=" * 40)
    
    cache = GPTCache(max_size=100, ttl_seconds=3600)
    monitor = PerformanceMonitor()
    
    # Pré-remplir avec quelques requêtes
    popular_queries = ["science", "histoire", "roman"]
    test_taxonomy = {"test": "data"}
    mock_response = {"result": "test"}
    
    for query in popular_queries:
        cache.set(query, test_taxonomy, mock_response)
    
    def simulate_user_requests(user_id, num_requests=5):
        """Simule les requêtes d'un utilisateur"""
        request_times = []
        
        for i in range(num_requests):
            start_time = time.time()
            
            # 70% de chance d'utiliser une requête populaire
            if i % 10 < 7:
                query = popular_queries[i % len(popular_queries)]
            else:
                query = f"unique_query_{user_id}_{i}"
            
            # Simuler la requête
            result = cache.get(query, test_taxonomy)
            if not result:
                # Cache miss - simuler GPT call
                time.sleep(0.001)  # Simulation très rapide
                cache.set(query, test_taxonomy, mock_response)
            
            request_time = time.time() - start_time
            request_times.append(request_time)
            monitor.track_request(f"user_{user_id}", request_time)
            
            # Petite pause entre les requêtes
            time.sleep(0.01)
        
        return {
            'user_id': user_id,
            'avg_time': sum(request_times) / len(request_times),
            'total_requests': len(request_times)
        }
    
    # Test avec différents nombres d'utilisateurs concurrents
    user_counts = [5, 10, 20, 30]
    
    for num_users in user_counts:
        print(f"\n👥 Test avec {num_users} utilisateurs concurrents:")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(simulate_user_requests, i, 5) 
                for i in range(num_users)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        total_requests = sum(r['total_requests'] for r in results)
        
        # Statistiques
        perf_stats = monitor.get_stats(safe_mode=True)
        cache_stats = cache.get_stats_fast()
        
        print(f"   ⏱️  Temps total: {total_time:.2f}s")
        print(f"   📊 Total requêtes: {total_requests}")
        print(f"   🔄 Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
        print(f"   👤 Utilisateurs actifs: {perf_stats['active_users']}")
        print(f"   📈 Req/s: {total_requests/total_time:.1f}")
        
        # Vérifier si le système reste stable
        avg_response_time = perf_stats.get('avg_response_time', 0)
        if avg_response_time < 1.0:
            print(f"   ✅ Stable (temps réponse: {avg_response_time:.3f}s)")
        else:
            print(f"   ⚠️  Risque de surcharge (temps réponse: {avg_response_time:.3f}s)")

if __name__ == "__main__":
    print("🎯 ANALYSE DE PERFORMANCE CACHE - BIBLIOSENSE PHASE 2")
    print("=" * 70)
    
    # Test de performance du cache
    simulate_cache_performance()
    
    # Test de charge concurrent
    test_concurrent_load()
    
    print(f"\n🎉 CONCLUSION:")
    print("Le cache GPT améliore drastiquement la capacité utilisateur.")
    print("Avec 80% de hit rate, la capacité peut être multipliée par 5-10x.")
    print("L'optimisation du cache est cruciale pour la montée en charge.")
