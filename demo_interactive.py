#!/usr/bin/env python3
"""
Démonstration interactive de BiblioSense
Permet de tester des requêtes manuellement
"""

import json
import requests
import sys
from typing import Optional

class BiblioSenseDemo:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_connection(self) -> bool:
        """Teste la connexion à l'API"""
        try:
            response = self.session.get(f"{self.base_url}/books", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def search_books(self, query: str) -> Optional[dict]:
        """Effectue une recherche de livres"""
        try:
            response = self.session.post(
                f"{self.base_url}/filter",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
            return None
    
    def display_results(self, results: dict) -> None:
        """Affiche les résultats de manière formatée"""
        books = results.get('book_list', [])
        description = results.get('description', '')
        
        print(f"\n📖 Description: {description}")
        print(f"📚 {len(books)} livre(s) trouvé(s)\n")
        
        for i, book in enumerate(books[:5], 1):  # Limite à 5 résultats
            print(f"📖 {i}. {book.get('titre', 'Titre inconnu')}")
            if book.get('auteur'):
                print(f"   👤 Auteur: {book.get('auteur')}")
            if book.get('editeur'):
                print(f"   🏢 Éditeur: {book.get('editeur')}")
            if book.get('parution'):
                print(f"   📅 Parution: {book.get('parution')}")
            if book.get('pages'):
                print(f"   📄 Pages: {book.get('pages')}")
            if book.get('score'):
                print(f"   ⭐ Score: {book.get('score')}")
            print()
        
        if len(books) > 5:
            print(f"... et {len(books) - 5} autres résultats\n")
    
    def run_demo(self) -> None:
        """Lance la démonstration interactive"""
        print("🔬 BiblioSense - Démonstration Interactive")
        print("=" * 50)
        print(f"🔗 URL: {self.base_url}")
        
        # Test de connexion
        print("🔍 Test de connexion...", end=" ")
        if self.test_connection():
            print("✅ Connecté!")
        else:
            print("❌ Impossible de se connecter à l'API")
            print("Vérifiez que l'application est lancée")
            return
        
        # Suggestions d'exemples
        examples = [
            "Je cherche des romans de science-fiction",
            "Livres de Victor Hugo",
            "Ouvrages sur l'intelligence artificielle",
            "Romans français contemporains",
            "Biographies d'entrepreneurs",
            "Le Petit Prince"
        ]
        
        print(f"\n💡 Exemples de requêtes:")
        for i, example in enumerate(examples, 1):
            print(f"   {i}. {example}")
        
        print(f"\n📝 Tapez vos requêtes (tapez 'quit' pour quitter):")
        print("=" * 50)
        
        while True:
            try:
                query = input("\n🔍 Votre requête: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Au revoir!")
                    break
                
                if not query:
                    continue
                
                if query.isdigit() and 1 <= int(query) <= len(examples):
                    query = examples[int(query) - 1]
                    print(f"📝 Requête sélectionnée: {query}")
                
                print("🔄 Recherche en cours...")
                results = self.search_books(query)
                
                if results:
                    self.display_results(results)
                else:
                    print("❌ Aucun résultat ou erreur")
                    
            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    # Vous pouvez modifier l'URL ici
    base_url = "http://localhost:8080"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    demo = BiblioSenseDemo(base_url)
    demo.run_demo()

if __name__ == "__main__":
    main()
