# Guide de Test BiblioSense

## 📋 Fichiers de Test

### 1. `EXEMPLES_REQUETES.md`
Guide complet avec des exemples de requêtes utilisateurs organisés par catégorie :
- Recherches par genre (fiction, non-fiction)
- Recherches par auteur
- Recherches thématiques
- Requêtes complexes
- Recherches par humeur/mood

### 2. `test_queries.json` 
20 requêtes de test structurées avec métadonnées pour tests automatisés.

### 3. `test_api.py`
Script Python pour tester automatiquement l'API avec toutes les requêtes.

### 4. `demo_interactive.py`
Démonstration interactive permettant de tester manuellement des requêtes.

## 🚀 Comment Utiliser

### Test Automatique
```bash
# Lancer votre application BiblioSense
python app.py

# Dans un autre terminal, lancer les tests
python test_api.py
```

### Démonstration Interactive
```bash
# Lancer la démo interactive
python demo_interactive.py

# Ou avec une URL personnalisée
python demo_interactive.py https://your-service.run.app
```

## 📊 Résultats des Tests

Les tests automatiques génèrent un fichier `test_results.json` avec :
- Timestamp des tests
- Nombre de tests réussis/échoués
- Temps de réponse
- Nombre de livres trouvés par requête
- Messages d'erreur détaillés

## 🎯 Exemples de Requêtes Populaires

### Simple
- "Je cherche des romans de science-fiction"
- "Livres de Victor Hugo"
- "Le Petit Prince"

### Complexe
- "Roman policier français publié après 2020"
- "Livre de cuisine végétarienne de moins de 300 pages"
- "Biographies d'entrepreneures femmes"

### Par Humeur
- "Je veux quelque chose de léger et drôle"
- "Un livre pour me motiver"
- "Romans tristes qui font pleurer"

## 🔧 Configuration

### URL de Test
Modifiez la variable `base_url` dans les scripts :
- Local: `http://localhost:8080`
- Cloud Run: `https://your-service.run.app`

### Timeout
Les scripts utilisent un timeout de 30 secondes pour les requêtes GPT.

## 📈 Métriques à Surveiller

1. **Taux de succès** : % de requêtes qui retournent des résultats
2. **Temps de réponse** : Latence moyenne des requêtes
3. **Pertinence** : Nombre moyen de livres trouvés
4. **Couverture** : Diversité des catégories testées

## 🐛 Dépannage

### "Connection refused"
- Vérifiez que l'application est lancée
- Vérifiez l'URL et le port

### "Timeout"
- Les requêtes GPT peuvent être lentes
- Augmentez le timeout si nécessaire

### "No results"
- Vérifiez que la base de données contient des livres
- Vérifiez la clé API OpenAI

## 📝 Ajouter de Nouveaux Tests

Pour ajouter une nouvelle requête de test, modifiez `test_queries.json` :

```json
{
  "id": 21,
  "category": "nouvelle_categorie",
  "query": "Votre nouvelle requête",
  "expected_keywords": ["mot-clé1", "mot-clé2"],
  "expected_categories": ["Catégorie1", "Catégorie2"]
}
```
