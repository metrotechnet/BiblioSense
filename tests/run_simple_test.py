#!/usr/bin/env python3
"""
Script simple pour générer les résultats de get_keywords_with_gpt
Première passe pour créer la base de données de validation.
"""

import json
import os
import re
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

def extract_queries_from_markdown(file_path):
    """Extrait toutes les requêtes du fichier EXEMPLES_REQUETES.md"""
    queries = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour extraire les requêtes entre guillemets
    quote_pattern = r'"([^"]+)"'
    quoted_queries = re.findall(quote_pattern, content)
    
    # Ajouter les requêtes et supprimer les doublons
    seen = set()
    for query in quoted_queries:
        query = query.strip()
        if len(query) > 5 and query not in seen:
            queries.append(query)
            seen.add(query)
    
    return queries

def run_simple_test():
    """
    Lance un test simple sans validation complète
    """
    print("🚀 Test simple de get_keywords_with_gpt")
    print("=" * 50)
    
    # Importer après avoir ajouté le path
    try:
        from openai import OpenAI
        from utils.gpt_services import get_keywords_with_gpt
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Assurez-vous que les modules sont installés et accessibles")
        return
    
def init_openai_client():
    """
    Initialise le client OpenAI en utilisant la même logique que l'app principale
    """
    try:
        # Importer les modules de configuration de l'app
        from utils.config import get_secret
        from openai import OpenAI
        
        # Essayer d'abord avec la variable d'environnement
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            # Essayer avec le Secret Manager (comme dans app.py)
            try:
                DEFAULT_SECRET_ID = "bibliosense-secrets"
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
                
                if project_id:
                    print("🔐 Tentative de récupération depuis Google Secret Manager...")
                    api_key = get_secret(DEFAULT_SECRET_ID, project_id=project_id)
                    
                    if api_key:
                        print("✅ Clé API récupérée depuis Secret Manager")
                    else:
                        print("❌ Clé API non trouvée dans Secret Manager")
                else:
                    print("ℹ️  GOOGLE_CLOUD_PROJECT non défini, Secret Manager ignoré")
                    
            except Exception as e:
                print(f"⚠️  Erreur Secret Manager: {e}")
        
        if not api_key:
            print("❌ OPENAI_API_KEY non disponible")
            print("💡 Options :")
            print("   1. Définir la variable d'environnement OPENAI_API_KEY")
            print("   2. Configurer Google Cloud Secret Manager")
            return None
        
        client = OpenAI(api_key=api_key)
        print("✅ Client OpenAI initialisé")
        return client
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Utilisez la variable d'environnement OPENAI_API_KEY comme fallback")
        
        # Fallback simple
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            from openai import OpenAI
            return OpenAI(api_key=api_key)
        else:
            print("❌ OPENAI_API_KEY non définie")
            return None
    
    # Initialiser OpenAI
    client = init_openai_client()
    if not client:
        return    # Extraire les requêtes
    try:
        queries = extract_queries_from_markdown("../EXEMPLES_REQUETES.md")
        print(f"✅ {len(queries)} requêtes extraites")
    except FileNotFoundError:
        print("❌ Fichier EXEMPLES_REQUETES.md non trouvé")
        return
    
    # Tester un échantillon des requêtes
    sample_queries = queries[:10]  # Prendre les 10 premières pour commencer
    results = []
    
    print(f"\n🧪 Test de {len(sample_queries)} requêtes d'exemple...")
    print("-" * 50)
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n[{i:2d}] '{query}'")
        
        try:
            result = get_keywords_with_gpt(query, {}, client)
            print(f"    ✅ {json.dumps(result, ensure_ascii=False)}")
            
            results.append({
                "query": query,
                "result": result,
                "status": "success"
            })
            
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
            results.append({
                "query": query,
                "result": None,
                "status": "error",
                "error": str(e)
            })
    
    # Sauvegarder les résultats
    output_data = {
        "test_info": {
            "date": "2025-08-08",
            "function": "get_keywords_with_gpt",
            "sample_size": len(sample_queries),
            "total_available": len(queries)
        },
        "results": results,
        "all_queries": queries  # Pour référence
    }
    
    with open("keywords_test_results.json", 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Résultats:")
    success_count = len([r for r in results if r["status"] == "success"])
    print(f"   ✅ Succès: {success_count}/{len(sample_queries)}")
    print(f"   ❌ Erreurs: {len(sample_queries) - success_count}/{len(sample_queries)}")
    print(f"\n💾 Résultats sauvegardés dans: keywords_test_results.json")
    
    print(f"\n📝 Prochaines étapes:")
    print("1. Examiner les résultats dans keywords_test_results.json")
    print("2. Ajuster le prompt si nécessaire")
    print("3. Relancer le test complet si satisfait")

if __name__ == "__main__":
    run_simple_test()
