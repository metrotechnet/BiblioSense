#!/usr/bin/env python3
"""
Script de test simple pour get_keywords_with_gpt
"""

import json
import os
import re
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

def extract_queries():
    """Extrait les requêtes du fichier EXEMPLES_REQUETES.md"""
    try:
        with open("../EXEMPLES_REQUETES.md", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire les requêtes entre guillemets
        queries = re.findall(r'"([^"]+)"', content)
        
        # Filtrer et nettoyer
        filtered = []
        for q in queries:
            if len(q) > 5 and not q.startswith('{'):
                filtered.append(q.strip())
        
        # Supprimer doublons
        return list(dict.fromkeys(filtered))
        
    except FileNotFoundError:
        print("❌ Fichier EXEMPLES_REQUETES.md non trouvé")
        return []

def test_function():
    """Test simple de la fonction"""
    print("🧪 Test de get_keywords_with_gpt")
    print("=" * 40)
    
    # Essayer d'importer
    try:
        from utils.gpt_services import get_keywords_with_gpt
        from openai import OpenAI
        print("✅ Imports réussis")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return
    
    # Clé API
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY non définie")
        print("💡 Définissez cette variable d'environnement")
        return
    
    try:
        client = OpenAI(api_key=api_key)
        print("✅ Client OpenAI créé")
    except Exception as e:
        print(f"❌ Erreur client: {e}")
        return
    
    # Extraire requêtes
    queries = extract_queries()
    if not queries:
        print("❌ Aucune requête trouvée")
        return
    
    print(f"✅ {len(queries)} requêtes extraites")
    
    # Tester 5 requêtes
    sample = queries[:5]
    results = []
    
    print("\n🔍 Tests:")
    for i, query in enumerate(sample, 1):
        print(f"\n[{i}] {query}")
        
        try:
            result = get_keywords_with_gpt(query, {}, client)
            print(f"    ✅ {json.dumps(result, ensure_ascii=False)}")
            results.append({"query": query, "result": result, "ok": True})
        except Exception as e:
            print(f"    ❌ {e}")
            results.append({"query": query, "error": str(e), "ok": False})
    
    # Sauvegarder
    with open("test_results.json", 'w', encoding='utf-8') as f:
        json.dump({
            "total_queries": len(queries),
            "tested": len(sample),
            "results": results,
            "all_queries": queries
        }, f, indent=2, ensure_ascii=False)
    
    success = sum(1 for r in results if r["ok"])
    print(f"\n📊 {success}/{len(sample)} réussis")
    print("💾 Résultats dans test_results.json")

if __name__ == "__main__":
    test_function()
