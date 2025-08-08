#!/usr/bin/env python3
"""
Script de validation pour get_keywords_with_gpt
Teste toutes les requêtes du fichier EXEMPLES_REQUETES.md et génère les résultats attendus.
"""

import json
import os
import re
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from openai import OpenAI
from utils.gpt_services import get_keywords_with_gpt
from utils.config import get_config, get_secret

def extract_queries_from_markdown(file_path):
    """
    Extrait toutes les requêtes du fichier EXEMPLES_REQUETES.md
    
    Returns:
        list: Liste des requêtes extraites
    """
    queries = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour extraire les requêtes entre guillemets
    quote_pattern = r'"([^"]+)"'
    quoted_queries = re.findall(quote_pattern, content)
    
    # Pattern pour extraire les requêtes de format "- phrase"
    bullet_pattern = r'^- ([^"]*[^"])$'
    bullet_queries = re.findall(bullet_pattern, content, re.MULTILINE)
    
    # Combiner toutes les requêtes
    all_queries = quoted_queries + bullet_queries
    
    # Nettoyer et filtrer
    for query in all_queries:
        query = query.strip()
        # Ignorer les requêtes trop courtes ou contenant du JSON
        if len(query) > 5 and not query.startswith('{') and not query.startswith('```'):
            queries.append(query)
    
    # Supprimer les doublons en gardant l'ordre
    seen = set()
    unique_queries = []
    for query in queries:
        if query not in seen:
            unique_queries.append(query)
            seen.add(query)
    
    return unique_queries

# Configuration OpenAI
DEFAULT_SECRET_ID = "openai-api-key"
DEFAULT_CREDENTIALS_PATH = "../bibliosense-467520-789ce439ce99.json"
PROJECT_ID = "bibliosense-467520"

def init_openai_client():
    """
    Initialize OpenAI client with API key from Secret Manager or environment variables.
    Also clears GPT cache for a fresh start.
    """
    global openai_client, gpt_cache
    
    # Si exécuté en local, charger les credentials depuis un fichier
    project_id = PROJECT_ID
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = DEFAULT_CREDENTIALS_PATH
        try:
            with open(DEFAULT_CREDENTIALS_PATH, 'r') as f:
                credentials = json.load(f)
            project_id = credentials['project_id']
        except Exception as e:
            print(f"⚠️  Error loading credentials file: {e}")

    # Essayer Secret Manager seulement si pas de variable d'environnement
    try:
        OPENAI_API_KEY = get_secret(DEFAULT_SECRET_ID, project_id=project_id)
        if OPENAI_API_KEY:
            print("✅ Clé OpenAI récupérée depuis Secret Manager")
        else:
            raise ValueError("OPENAI_API_KEY non trouvée")
    except Exception as e:
        print(f"Erreur Secret Manager: {str(e)[:100]}...")
        raise ValueError("OPENAI_API_KEY n'est pas définie (ni dans .env ni dans Secret Manager)")

    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized")
    return openai_client
    


def test_keywords_extraction(queries, openai_client, output_file="test_results_keywords.json"):
    """
    Teste get_keywords_with_gpt sur toutes les requêtes et sauvegarde les résultats
    
    Args:
        queries (list): Liste des requêtes à tester
        openai_client: Client OpenAI
        output_file (str): Fichier de sortie pour les résultats
    """
    results = []
    taxonomy_data = {}  # On utilise une taxonomie vide pour ce test
    
    print(f"🧪 Début des tests sur {len(queries)} requêtes...")
    print("=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i:2d}/{len(queries)}] Test: '{query}'")
        
        try:
            # Appeler get_keywords_with_gpt
            result = get_keywords_with_gpt(query, taxonomy_data, openai_client)
            
            # Créer l'entrée de résultat
            test_result = {
                "query": query,
                "gpt_result": result,
                "status": "success",
                "expected_result": None,  # À remplir manuellement
                "validation_notes": "",   # À remplir manuellement
                "test_passed": None       # À valider manuellement
            }
            
            # Afficher le résultat
            print(f"✅ Résultat: {json.dumps(result, ensure_ascii=False)}")
            
        except Exception as e:
            # En cas d'erreur
            test_result = {
                "query": query,
                "gpt_result": None,
                "status": "error",
                "error": str(e),
                "expected_result": None,
                "validation_notes": f"Erreur: {str(e)}",
                "test_passed": False
            }
            
            print(f"❌ Erreur: {str(e)}")
        
        results.append(test_result)
    
    # Sauvegarder les résultats
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "test_metadata": {
                "total_queries": len(queries),
                "successful_tests": len([r for r in results if r["status"] == "success"]),
                "failed_tests": len([r for r in results if r["status"] == "error"]),
                "test_date": "2025-08-08",
                "function_tested": "get_keywords_with_gpt"
            },
            "test_results": results
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"🏁 Tests terminés!")
    print(f"📊 Résultats: {len([r for r in results if r['status'] == 'success'])}/{len(queries)} réussis")
    print(f"💾 Résultats sauvegardés dans: {output_file}")
    print("\n📝 Prochaines étapes:")
    print("1. Ouvrir le fichier JSON généré")
    print("2. Remplir les champs 'expected_result' avec les résultats attendus")
    print("3. Ajouter des notes de validation dans 'validation_notes'")
    print("4. Marquer 'test_passed' comme true/false selon la validation")

def generate_validation_template():
    """
    Génère un template pour faciliter la validation manuelle
    """
    template = {
        "validation_guidelines": {
            "keywords_quality": "Les mots-clés extraits sont-ils pertinents pour la requête?",
            "field_selection": "Le champ sélectionné est-il le plus approprié?",
            "synonyms_completeness": "Les synonymes/variantes sont-ils complets?",
            "format_compliance": "Le format JSON est-il correct?",
            "edge_cases": "Comment la fonction gère-t-elle les cas particuliers?"
        },
        "validation_criteria": {
            "excellent": "Extraction parfaite, champ optimal, synonymes complets",
            "good": "Extraction correcte avec quelques améliorations possibles",
            "acceptable": "Extraction basique mais fonctionnelle",
            "poor": "Extraction incorrecte ou champ inapproprié",
            "failed": "Erreur ou résultat inutilisable"
        },
        "common_expected_fields": {
            "auteur_queries": ["Victor Hugo", "Stephen King", "Agatha Christie"],
            "genre_queries": ["science-fiction", "fantasy", "policier", "romance"],
            "theme_queries": ["intelligence artificielle", "Seconde Guerre mondiale"],
            "language_queries": ["anglais", "français", "espagnol"],
            "format_queries": ["moins de 200 pages", "romans volumineux"],
            "mixed_queries": "Requêtes complexes nécessitant plusieurs champs"
        }
    }
    
    with open("validation_template.json", 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print("📋 Template de validation créé: validation_template.json")

def main():
    """
    Fonction principale du script de test
    """
    try:
        print("🚀 Script de validation pour get_keywords_with_gpt")
        print("=" * 60)
        
        # 1. Extraire les requêtes du fichier markdown
        print("📖 Extraction des requêtes depuis EXEMPLES_REQUETES.md...")
        queries = extract_queries_from_markdown("./tests/EXEMPLES_REQUETES.md")
        print(f"✅ {len(queries)} requêtes extraites")
        
        # 2. Initialiser le client OpenAI
        print("🔑 Initialisation du client OpenAI...")
        openai_client = init_openai_client()
        print("✅ Client OpenAI initialisé")
        
        # 3. Générer le template de validation
        print("📋 Génération du template de validation...")
        generate_validation_template()
        
        # 4. Lancer les tests
        print("🧪 Lancement des tests...")
        test_keywords_extraction(queries, openai_client)
        
    except FileNotFoundError as e:
        print(f"❌ Fichier non trouvé: {e}")
        print("💡 Assurez-vous que EXEMPLES_REQUETES.md existe dans le répertoire parent")
        
    except ValueError as e:
        print(f"❌ Erreur de configuration: {e}")
        print("💡 Vérifiez que la variable d'environnement OPENAI_API_KEY est définie")
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()
