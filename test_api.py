#!/usr/bin/env python3
"""
Script de test pour BiblioSense API
Teste automatiquement les requêtes d'exemple contre l'API
"""

import json
import requests
import time
from typing import Dict, List

class BiblioSenseAPITester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.test_results = []
    
    def load_test_queries(self, filename: str = "test_queries.json") -> List[Dict]:
        """Charge les requêtes de test depuis le fichier JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('test_queries', [])
        except FileNotFoundError:
            print(f"❌ Fichier {filename} non trouvé")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Erreur de parsing JSON: {e}")
            return []
    
    def test_single_query(self, test_case: Dict) -> Dict:
        """Teste une seule requête"""
        query_id = test_case.get('id')
        query_text = test_case.get('query')
        category = test_case.get('category')
        
        print(f"\n🧪 Test {query_id}: {category}")
        print(f"📝 Requête: '{query_text}'")
        
        try:
            # Faire la requête à l'API
            response = requests.post(
                f"{self.base_url}/filter",
                json={"query": query_text},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                books_found = len(result.get('book_list', []))
                description = result.get('description', 'Aucune description')
                
                print(f"✅ Succès: {books_found} livres trouvés")
                print(f"📖 Description: {description[:100]}...")
                
                return {
                    'id': query_id,
                    'category': category,
                    'query': query_text,
                    'status': 'success',
                    'books_found': books_found,
                    'description': description,
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                return {
                    'id': query_id,
                    'category': category,
                    'query': query_text,
                    'status': 'error',
                    'error': f"HTTP {response.status_code}",
                    'response_time': response.elapsed.total_seconds()
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
            return {
                'id': query_id,
                'category': category,
                'query': query_text,
                'status': 'connection_error',
                'error': str(e),
                'response_time': None
            }
    
    def run_all_tests(self) -> None:
        """Exécute tous les tests"""
        test_queries = self.load_test_queries()
        
        if not test_queries:
            print("❌ Aucune requête de test trouvée")
            return
        
        print(f"🚀 Démarrage de {len(test_queries)} tests...")
        print(f"🔗 URL de base: {self.base_url}")
        
        start_time = time.time()
        
        for test_case in test_queries:
            result = self.test_single_query(test_case)
            self.test_results.append(result)
            
            # Petite pause entre les requêtes
            time.sleep(0.5)
        
        total_time = time.time() - start_time
        self.print_summary(total_time)
        self.save_results()
    
    def print_summary(self, total_time: float) -> None:
        """Affiche un résumé des tests"""
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r['status'] == 'success'])
        failed_tests = total_tests - successful_tests
        
        avg_books_found = 0
        if successful_tests > 0:
            total_books = sum(r.get('books_found', 0) for r in self.test_results if r['status'] == 'success')
            avg_books_found = total_books / successful_tests
        
        print(f"\n" + "="*60)
        print(f"📊 RÉSUMÉ DES TESTS")
        print(f"="*60)
        print(f"✅ Tests réussis: {successful_tests}/{total_tests}")
        print(f"❌ Tests échoués: {failed_tests}/{total_tests}")
        print(f"📚 Moyenne de livres trouvés: {avg_books_found:.1f}")
        print(f"⏱️  Temps total: {total_time:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ Tests échoués:")
            for result in self.test_results:
                if result['status'] != 'success':
                    print(f"  - Test {result['id']}: {result.get('error', 'Erreur inconnue')}")
    
    def save_results(self, filename: str = "test_results.json") -> None:
        """Sauvegarde les résultats des tests"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_tests': len(self.test_results),
                    'successful_tests': len([r for r in self.test_results if r['status'] == 'success']),
                    'results': self.test_results
                }, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Résultats sauvegardés dans {filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")

def main():
    """Fonction principale"""
    print("🔬 BiblioSense API Tester")
    print("=" * 40)
    
    # Vous pouvez modifier l'URL ici pour tester votre déploiement Cloud Run
    # base_url = "https://your-service-url.run.app"
    base_url = "http://localhost:8080"
    
    tester = BiblioSenseAPITester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()
