#!/usr/bin/env python3
"""
Script de validation finale pour comparer les résultats de get_keywords_with_gpt 
avec les résultats attendus.
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

def load_expected_results():
    """Charge les résultats attendus du fichier de validation"""
    try:
        with open("keywords_validation_expected.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data["test_cases"]
    except FileNotFoundError:
        print("❌ Fichier keywords_validation_expected.json non trouvé")
        print("💡 Lancez d'abord generate_validation_template.py")
        return []

def validate_result(expected, actual):
    """
    Compare un résultat attendu avec un résultat réel
    
    Returns:
        dict: Résultat de la validation avec score et notes
    """
    validation = {
        "score": 0,
        "max_score": 100,
        "details": {},
        "passed": False,
        "notes": []
    }
    
    if not actual or "keywords" not in actual:
        validation["notes"].append("❌ Format invalide - pas de clé 'keywords'")
        return validation
    
    expected_keywords = expected.get("keywords", {})
    actual_keywords = actual.get("keywords", {})
    
    # 1. Vérifier le champ principal (40 points)
    expected_fields = set(expected_keywords.keys())
    actual_fields = set(actual_keywords.keys())
    
    if expected_fields == actual_fields:
        validation["score"] += 40
        validation["details"]["field_match"] = "✅ Champ(s) correct(s)"
    elif expected_fields.intersection(actual_fields):
        validation["score"] += 20
        validation["details"]["field_match"] = "⚠️ Champ partiellement correct"
        validation["notes"].append(f"Attendu: {list(expected_fields)}, Reçu: {list(actual_fields)}")
    else:
        validation["details"]["field_match"] = "❌ Champ incorrect"
        validation["notes"].append(f"Attendu: {list(expected_fields)}, Reçu: {list(actual_fields)}")
    
    # 2. Vérifier la qualité des mots-clés (40 points)
    keyword_quality_score = 0
    for field in expected_fields:
        if field in actual_keywords:
            expected_kw = set(expected_keywords[field])
            actual_kw = set(actual_keywords[field])
            
            # Calculer l'intersection
            intersection = expected_kw.intersection(actual_kw)
            if intersection:
                # Score basé sur le pourcentage de mots-clés qui correspondent
                quality = len(intersection) / len(expected_kw) * 40
                keyword_quality_score = max(keyword_quality_score, quality)
    
    validation["score"] += int(keyword_quality_score)
    validation["details"]["keyword_quality"] = f"Score qualité: {int(keyword_quality_score)}/40"
    
    # 3. Vérifier le format JSON (20 points)
    if isinstance(actual_keywords, dict) and all(isinstance(v, list) for v in actual_keywords.values()):
        validation["score"] += 20
        validation["details"]["format"] = "✅ Format JSON correct"
    else:
        validation["details"]["format"] = "❌ Format JSON incorrect"
    
    # Déterminer si le test passe (seuil: 60/100)
    validation["passed"] = validation["score"] >= 60
    
    return validation

def run_validation_test():
    """
    Lance la validation complète avec les données attendues
    """
    print("🔍 Validation des résultats get_keywords_with_gpt")
    print("=" * 55)
    
    # Charger les résultats attendus
    expected_results = load_expected_results()
    if not expected_results:
        return
    
    print(f"📊 {len(expected_results)} cas de test chargés")
    
    # Simuler quelques tests (sans vraie API)
    print("\n🧪 Simulation de validation sur un échantillon...")
    print("-" * 55)
    
    # Prendre un échantillon représentatif
    sample_indices = [0, 12, 18, 28, 33, 53]  # Différents types de requêtes
    
    validation_results = []
    
    for idx in sample_indices:
        if idx >= len(expected_results):
            continue
            
        case = expected_results[idx]
        query = case["query"]
        expected = case["expected_result"]
        
        print(f"\n📝 Test: '{query}'")
        print(f"    Attendu: {json.dumps(expected, ensure_ascii=False)}")
        
        # Simuler différents types de résultats (à remplacer par de vrais appels GPT)
        simulated_result = simulate_gpt_result(query, expected)
        print(f"    Simulé:  {json.dumps(simulated_result, ensure_ascii=False)}")
        
        # Valider
        validation = validate_result(expected, simulated_result)
        
        status = "✅ PASS" if validation["passed"] else "❌ FAIL"
        print(f"    Résultat: {status} ({validation['score']}/100)")
        
        if validation["notes"]:
            for note in validation["notes"]:
                print(f"    Note: {note}")
        
        validation_results.append({
            "query": query,
            "expected": expected,
            "actual": simulated_result,
            "validation": validation
        })
    
    # Résumé
    passed = sum(1 for r in validation_results if r["validation"]["passed"])
    total = len(validation_results)
    avg_score = sum(r["validation"]["score"] for r in validation_results) / total
    
    print(f"\n📊 Résumé de validation:")
    print(f"   ✅ Tests réussis: {passed}/{total}")
    print(f"   📈 Score moyen: {avg_score:.1f}/100")
    
    # Sauvegarder les résultats
    output = {
        "validation_summary": {
            "total_tests": total,
            "passed_tests": passed,
            "average_score": avg_score,
            "pass_rate": passed/total * 100
        },
        "detailed_results": validation_results
    }
    
    with open("validation_results.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats détaillés sauvegardés dans: validation_results.json")
    
    # Recommandations
    print(f"\n💡 Recommandations:")
    if avg_score < 70:
        print("   - Le prompt nécessite des améliorations significatives")
        print("   - Vérifier la logique d'extraction des champs")
    elif avg_score < 85:
        print("   - Performance acceptable, quelques améliorations possibles")
        print("   - Examiner les cas qui échouent pour identifier les patterns")
    else:
        print("   - Excellente performance!")
        print("   - Le système est prêt pour la production")

def simulate_gpt_result(query, expected):
    """
    Simule différents types de résultats GPT pour les tests
    (À remplacer par de vrais appels à get_keywords_with_gpt)
    """
    import random
    
    # Simuler différents scenarios
    scenarios = [
        "perfect",      # Résultat parfait
        "good",         # Bon résultat avec quelques différences
        "field_error",  # Mauvais champ
        "format_error", # Erreur de format
        "partial"       # Résultat partiel
    ]
    
    scenario = random.choice(scenarios)
    
    if scenario == "perfect":
        return expected
    
    elif scenario == "good":
        # Même champ, mots-clés légèrement différents
        result = {"keywords": {}}
        for field, keywords in expected["keywords"].items():
            # Garder quelques mots-clés originaux et en ajouter de nouveaux
            new_keywords = keywords[:2] + ["variante", "synonyme"]
            result["keywords"][field] = new_keywords
        return result
    
    elif scenario == "field_error":
        # Mauvais champ mais mots-clés corrects
        wrong_field = "resume" if "auteur" in expected["keywords"] else "auteur"
        first_field = list(expected["keywords"].keys())[0]
        return {"keywords": {wrong_field: expected["keywords"][first_field]}}
    
    elif scenario == "format_error":
        # Erreur de format (string au lieu de liste)
        field = list(expected["keywords"].keys())[0]
        return {"keywords": {field: expected["keywords"][field][0]}}
    
    elif scenario == "partial":
        # Résultat partiel
        if len(expected["keywords"]) > 1:
            field = list(expected["keywords"].keys())[0]
            return {"keywords": {field: expected["keywords"][field][:1]}}
        else:
            return expected
    
    return expected

if __name__ == "__main__":
    run_validation_test()
