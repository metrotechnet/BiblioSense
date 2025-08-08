# 🧪 Scripts de Validation pour get_keywords_with_gpt

Ce dossier contient plusieurs scripts pour tester et valider la fonction `get_keywords_with_gpt` de BiblioSense.

## 📋 Vue d'ensemble

La validation de `get_keywords_with_gpt` se fait en plusieurs étapes :

1. **Génération des résultats attendus** - Analyse automatique des requêtes
2. **Tests avec l'API réelle** - Appels à OpenAI GPT
3. **Validation comparative** - Comparaison des résultats réels vs attendus

## 📂 Fichiers créés

### Scripts principaux

- **`generate_validation_template.py`** ✅
  - Génère automatiquement les résultats attendus pour toutes les requêtes
  - Analyse les patterns dans `EXEMPLES_REQUETES.md`
  - Crée `keywords_validation_expected.json`

- **`test_keywords_real.py`** 🔑
  - Script pour tester avec la vraie API OpenAI
  - Utilise la même logique d'initialisation que `app.py`
  - Nécessite `OPENAI_API_KEY` ou Google Cloud Secret Manager

- **`validate_keywords.py`** ✅
  - Compare les résultats réels avec les attendus
  - Système de scoring sur 100 points
  - Génère des rapports de validation détaillés

### Scripts de support

- **`test_keywords_validation.py`** - Version complète avec tous les cas de test
- **`simple_test.py`** - Test basique simplifié

## 🚀 Comment utiliser

### Étape 1 : Générer les résultats attendus

```bash
cd tests
python generate_validation_template.py
```

Ce script va :
- Extraire toutes les requêtes de `../EXEMPLES_REQUETES.md`
- Analyser chaque requête pour prédire le résultat attendu
- Créer le fichier `keywords_validation_expected.json`

**Résultat** : 82 cas de test avec résultats attendus

### Étape 2 : Tester avec l'API réelle (optionnel)

```bash
# Définir la clé API
$env:OPENAI_API_KEY = "your-api-key-here"

# Ou configurer Google Cloud
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"

# Lancer le test
python test_keywords_real.py
```

### Étape 3 : Valider les résultats

```bash
python validate_keywords.py
```

Ce script va :
- Charger les résultats attendus
- Simuler ou utiliser les vrais résultats GPT
- Comparer et scorer chaque test
- Générer un rapport de validation

## 📊 Système de scoring

Chaque test est noté sur **100 points** :

- **40 points** : Champ correct (auteur, titre, categorie, etc.)
- **40 points** : Qualité des mots-clés (pertinence, complétude)
- **20 points** : Format JSON correct

**Seuil de réussite** : 60/100

## 📈 Résultats de validation

### État actuel (simulation)
- ✅ **Tests réussis** : 4/6 (66.7%)
- 📈 **Score moyen** : 74.3/100
- 📊 **Performance** : Acceptable

### Cas problématiques identifiés

1. **Erreur de champ** : 
   - `"Le Petit Prince"` → Identifié comme auteur au lieu de titre
   
2. **Format incorrect** :
   - Retour de string au lieu de liste pour les mots-clés

## 🔧 Améliorer les résultats

### 1. Ajuster le prompt GPT

Dans `utils/gpt_services.py`, modifier le prompt pour :
- Mieux distinguer titres vs auteurs
- Renforcer les instructions de format
- Ajouter des exemples explicites

### 2. Post-traitement

Ajouter une validation du format de sortie :
```python
def validate_format(result):
    if "keywords" not in result:
        return {"keywords": {"categorie": ["general"]}}
    
    for field, keywords in result["keywords"].items():
        if isinstance(keywords, str):
            result["keywords"][field] = [keywords]
    
    return result
```

### 3. Règles spécifiques

Implémenter des règles pour les cas évidents :
- Titres connus (Le Petit Prince, 1984, etc.)
- Auteurs célèbres (Victor Hugo, etc.)
- Patterns de langue ("en anglais", "en français")

## 📁 Fichiers générés

- `keywords_validation_expected.json` - Résultats attendus (82 cas)
- `validation_results.json` - Résultats détaillés des tests
- `test_results.json` - Résultats bruts des appels GPT

## 🎯 Prochaines étapes

1. **Examiner les résultats** dans `keywords_validation_expected.json`
2. **Corriger manuellement** les cas mal analysés
3. **Tester avec l'API réelle** quand disponible
4. **Itérer sur le prompt** basé sur les résultats
5. **Automatiser** les tests dans la CI/CD

## 💡 Notes importantes

- Les résultats attendus sont générés automatiquement et peuvent nécessiter des ajustements manuels
- La simulation est utilisée en l'absence de clé API OpenAI
- Le scoring est indicatif et peut être ajusté selon les priorités business
- Les tests couvrent différents types de requêtes : auteurs, genres, langues, formats, etc.

## 🆘 Dépannage

### Erreur : "OPENAI_API_KEY non définie"
```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# Ou créer un fichier .env
echo "OPENAI_API_KEY=sk-..." > .env
```

### Erreur : "Fichier non trouvé"
Vérifiez que `EXEMPLES_REQUETES.md` existe dans le répertoire courant.

### Erreur d'import
```bash
pip install openai
```
