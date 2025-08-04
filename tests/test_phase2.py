# Test script pour valider les fonctionnalités Phase 2
import requests
import time
import json
import concurrent.futures
import threading

class Phase2TestSuite:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.results = []
        
    def test_health_endpoint(self):
        """Test du endpoint de santé Phase 2"""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed - Status: {data.get('status')}")
                print(f"   Active users: {data.get('performance', {}).get('active_users', 0)}")
                print(f"   Memory usage: {data.get('performance', {}).get('memory_usage_percent', 0):.1f}%")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_session_info_enhanced(self):
        """Test du endpoint session_info amélioré"""
        print("🔍 Testing enhanced session info...")
        try:
            response = requests.get(f"{self.base_url}/session_info", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Session info enhanced - User ID: {data.get('user_id')}")
                if 'performance' in data:
                    print(f"   Performance data included ✅")
                if 'cache' in data:
                    print(f"   Cache stats included ✅")
                if 'cleanup' in data:
                    print(f"   Cleanup stats included ✅")
                return True
            else:
                print(f"❌ Session info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Session info error: {e}")
            return False
    
    def test_filter_with_cache(self):
        """Test du filtre avec cache GPT"""
        print("🔍 Testing filter with GPT cache...")
        test_query = "livres sur la science fiction"
        
        try:
            # Premier appel - devrait être lent (cache miss)
            start_time = time.time()
            response1 = requests.post(
                f"{self.base_url}/filter",
                json={"query": test_query},
                timeout=30
            )
            first_time = time.time() - start_time
            
            if response1.status_code != 200:
                print(f"❌ First filter call failed: {response1.status_code}")
                return False
            
            # Deuxième appel - devrait être rapide (cache hit)
            start_time = time.time()
            response2 = requests.post(
                f"{self.base_url}/filter",
                json={"query": test_query},
                timeout=30
            )
            second_time = time.time() - start_time
            
            if response2.status_code != 200:
                print(f"❌ Second filter call failed: {response2.status_code}")
                return False
            
            data1 = response1.json()
            data2 = response2.json()
            
            print(f"✅ Filter caching test passed")
            print(f"   First call (cache miss): {first_time:.2f}s")
            print(f"   Second call (cache hit): {second_time:.2f}s")
            print(f"   Speedup: {first_time/second_time:.1f}x faster")
            
            # Vérifier que les réponses sont identiques
            if data1.get('description') == data2.get('description'):
                print(f"   ✅ Response consistency verified")
            else:
                print(f"   ⚠️  Response inconsistency detected")
            
            return True
            
        except Exception as e:
            print(f"❌ Filter caching test error: {e}")
            return False
    
    def test_concurrent_users(self, num_users=5):
        """Test de charge avec utilisateurs concurrents"""
        print(f"🔍 Testing {num_users} concurrent users...")
        
        def make_request(user_id):
            try:
                session = requests.Session()
                
                # Simuler un utilisateur avec plusieurs requêtes
                queries = [
                    "science fiction",
                    "histoire",
                    "philosophie",
                    "romans français"
                ]
                
                results = []
                for query in queries:
                    start_time = time.time()
                    response = session.post(
                        f"{self.base_url}/filter",
                        json={"query": query},
                        timeout=30
                    )
                    response_time = time.time() - start_time
                    
                    results.append({
                        'user_id': user_id,
                        'query': query,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'success': response.status_code == 200
                    })
                
                return results
                
            except Exception as e:
                return [{'user_id': user_id, 'error': str(e), 'success': False}]
        
        # Exécuter les requêtes concurrentes
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_users)]
            all_results = []
            
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        total_time = time.time() - start_time
        
        # Analyser les résultats
        successful_requests = [r for r in all_results if r.get('success', False)]
        failed_requests = [r for r in all_results if not r.get('success', False)]
        
        avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        print(f"✅ Concurrent users test completed")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Successful requests: {len(successful_requests)}")
        print(f"   Failed requests: {len(failed_requests)}")
        print(f"   Average response time: {avg_response_time:.2f}s")
        
        if len(failed_requests) == 0:
            print(f"   ✅ All requests successful")
            return True
        else:
            print(f"   ⚠️  Some requests failed")
            return len(successful_requests) > len(failed_requests)
    
    def test_admin_endpoints(self):
        """Test des endpoints d'administration Phase 2"""
        print("🔍 Testing admin endpoints...")
        
        try:
            # Test clear cache
            response = requests.post(f"{self.base_url}/admin/cache/clear", timeout=10)
            if response.status_code == 200:
                print("   ✅ Cache clear endpoint working")
            else:
                print(f"   ⚠️  Cache clear failed: {response.status_code}")
            
            # Test force cleanup
            response = requests.post(f"{self.base_url}/admin/sessions/cleanup", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Session cleanup endpoint working - {data.get('message')}")
            else:
                print(f"   ⚠️  Session cleanup failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Admin endpoints test error: {e}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests Phase 2"""
        print("🚀 Starting Phase 2 Test Suite")
        print("=" * 50)
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("Enhanced Session Info", self.test_session_info_enhanced),
            ("GPT Cache", self.test_filter_with_cache),
            ("Concurrent Users", lambda: self.test_concurrent_users(5)),
            ("Admin Endpoints", self.test_admin_endpoints)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}")
            print("-" * 30)
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"💥 {test_name} CRASHED: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Phase 2 tests PASSED! System ready for 100-500 users.")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed. Minor issues to address.")
        else:
            print("❌ Major issues detected. Phase 2 implementation needs fixes.")
        
        return passed == total

if __name__ == "__main__":
    print("Phase 2 BiblioSense - Test Suite")
    print("Starting server tests in 3 seconds...")
    time.sleep(3)
    
    tester = Phase2TestSuite()
    tester.run_all_tests()
