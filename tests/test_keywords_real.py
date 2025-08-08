#!/usr/bin/env python3
"""
Test avec la même initialisation que l'app principale
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

def init_like_main_app():
    """Initialise comme dans app.py"""
    try:
        # Importer les modules nécessaires
        from utils.gpt_services import get_keywords_with_gpt
        from openai import OpenAI
        
        # Essayer d'abord les variables d'environnement
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("⚠️  OPENAI_API_KEY non trouvée en variable d'environnement")
            
            # Essayer avec la config de l'app
            try:
                from utils.config import get_secret
                
                DEFAULT_SECRET_ID = "bibliosense-secrets"
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
                
                if project_id:
                    print(f"🔐 Tentative Secret Manager (projet: {project_id})...")
                    api_key = get_secret(DEFAULT_SECRET_ID, project_id=project_id)
                    
                    if api_key:
                        print("✅ Clé récupérée depuis Secret Manager")
                    else:
                        print("❌ Pas de clé dans Secret Manager")
                else:
                    print("ℹ️  GOOGLE_CLOUD_PROJECT non défini")
                    
            except Exception as e:
                print(f"⚠️  Erreur Secret Manager: {e}")
        
        if not api_key:
            print("❌ Impossible de récupérer la clé API OpenAI")
            print("💡 Solutions:")
            print("   - Définir OPENAI_API_KEY en variable d'environnement")
            print("   - Configurer Google Cloud avec GOOGLE_CLOUD_PROJECT")
            return None, None
        
        # Créer le client
        client = OpenAI(api_key=api_key)
        print("✅ Client OpenAI initialisé")
        
        return client, get_keywords_with_gpt
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None, None

def extract_sample_queries():
    """Extrait quelques requêtes pour test"""
    sample_queries = [
        "Je cherche des romans de science-fiction",
        "Livres de Victor Hugo", 
        "Romans policiers français",
        "Livres en anglais pour débutants",
        "Livres courts de moins de 200 pages"
    ]
    return sample_queries

def run_test():
    """Lance le test"""
    print("🚀 Test get_keywords_with_gpt (initialisation comme app.py)")
    print("=" * 60)
    
    # Initialiser
    client, gpt_func = init_like_main_app()
    
    if not client or not gpt_func:
        print("❌ Initialisation échouée")
        return
    
    # Requêtes de test
    queries = extract_sample_queries()
    results = []
    
    print(f"\n🧪 Test de {len(queries)} requêtes...")
    print("-" * 40)
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}] '{query}'")
        
        try:
            result = gpt_func(query, {}, client)
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
                "error": str(e),
                "status": "error"
            })
    
    # Sauvegarder
    output = {
        "test_date": "2025-08-08",
        "test_type": "get_keywords_with_gpt",
        "results": results
    }
    
    with open("keywords_validation_results.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Résumé
    success_count = len([r for r in results if r["status"] == "success"])
    print(f"\n📊 Résultats:")
    print(f"   ✅ Succès: {success_count}/{len(queries)}")
    print(f"   ❌ Échecs: {len(queries) - success_count}/{len(queries)}")
    print(f"\n💾 Résultats sauvegardés dans: keywords_validation_results.json")
    
    if success_count > 0:
        print(f"\n📝 Prochaines étapes:")
        print("1. Examiner les résultats JSON")
        print("2. Valider si les extractions sont correctes")
        print("3. Ajuster le prompt si nécessaire")
    
    return results

if __name__ == "__main__":
    run_test()
