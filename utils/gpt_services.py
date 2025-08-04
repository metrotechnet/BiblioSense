"""
Services GPT pour BiblioSense
Contient les fonctions d'interaction avec OpenAI pour la classification et la description.
"""

import json
import os
from openai import OpenAI
from google.cloud import secretmanager


def get_secret(secret_name, project_id=None):
    """
    Récupère un secret depuis Google Secret Manager
    
    Args:
        secret_name (str): Nom du secret dans Secret Manager
        project_id (str): ID du projet GCP (optionnel, utilisera le projet par défaut si non spécifié)
    
    Returns:
        str: Valeur du secret
    """
    try:
        # Créer le client Secret Manager
        client = secretmanager.SecretManagerServiceClient()

        if not project_id:
            project_id = "BiblioSense"  # Nom de projet GCP valide (minuscules)

        # Construire le nom de la ressource du secret
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        # Récupérer le secret
        response = client.access_secret_version(request={"name": name})
        
        # Décoder et retourner la valeur
        payload = response.payload.data.decode("UTF-8")
        return json.loads(payload)['OPENAI_API_KEY']

    except Exception as e:
        print(f"⚠️  Erreur lors de la récupération du secret '{secret_name}': {e}")
        print(f"🔄 Fallback vers les variables d'environnement...")
        return os.getenv(secret_name.upper().replace('-', '_'))


def get_catagories_with_gpt(text, taxonomy, openai_client):
    """
    Use GPT to classify a book query into taxonomy categories.

    Args:
        text (str): User query or book description.
        taxonomy (list): Taxonomy nodes for context.
        openai_client (OpenAI): Instance du client OpenAI configuré.

    Returns:
        list or dict: Parsed GPT response as JSON.
    """
    prompt = f"""
        Tu es un classificateur de requêtes spécialisé dans la recherche de livres. 
        Analyse la requête ci-dessous et renvoie uniquement un objet JSON (aucun texte hors JSON) 
        qui contient les catégories pertinentes de la taxonomie ainsi que les mots-clés extraits.
        Par la suite, transforme la taxonomie trouvée en une description simple, claire et fluide en français, destinée à un lecteur non spécialiste. 
        Exprime-toi avec des phrases complètes et évite tout jargon technique.

        ### Taxonomie :
        {json.dumps(taxonomy, ensure_ascii=False, indent=2)}

        ### Champs disponibles pour les mots-clés :
        - titre : titre du livre
        - auteur : nom(s) d’auteur(s)
        - resume : résumé ou description
        - editeur : éditeur
        - langue : langue
        - categorie : catégorie ou domaine
        - parution : date de publication
        - pages : nombre de pages

        ### Requête utilisateur :
        {text}

        ### Instructions spéciales pour les mots-clés :
        - Pour chaque champ pertinent, fournis une liste de mots-clés synonymes et variantes
        - Inclus les variantes orthographiques, les synonymes, les termes connexes
        - Exemples : "romantique" → ["romantique", "sentimental", "romance", "amoureux", "passion"]
        - Exemples : "science-fiction" → ["science-fiction", "sci-fi", "SF", "anticipation", "futuriste"]
        - Exemples : "policier" → ["policier", "polar", "thriller", "enquête", "crime", "detective"]

        ### Format de réponse attendu (strictement au format JSON) :
        {{
        "Taxonomie": {{structure taxonomique filtrée}},
        "Mots-clés": {{
            "titre": ["mot_clé_1", "synonyme_1", "variante_1"],
            "auteur": ["nom_auteur", "variante_nom"],
            "resume": ["concept_1", "synonyme_1", "terme_connexe"],
            "editeur": ["nom_editeur"],
            "langue": ["français", "french"],
            "categorie": ["genre_1", "synonyme_genre", "variante_genre"],
            "parution": ["année", "période"],
            "pages": ["nombre_pages"]
        }},
        "Description": "Texte descriptif en français, clair et fluide."
        }}
        
        ### Exemples de synonymes par domaine :
        - Romance : romantique, sentimental, amoureux, passion, coeur, amour
        - Thriller : suspense, polar, policier, enquête, crime, mystère
        - Fantasy : fantastique, merveilleux, magie, épique, heroic-fantasy
        - Science-fiction : sci-fi, SF, anticipation, futuriste, technologique
        - Historique : période, époque, siècle, chronique, passé
        - Jeunesse : enfant, ado, adolescent, young adult, junior

        ### Exemple de style attendu pour la description :
        "Les livres sont ..."

        - N'inclus que les champs pertinents pour la requête.
        - Si une information est absente, omets simplement le champ.
        - Assure-toi que chaque liste de mots-clés contient au moins 2-3 variantes quand c'est pertinent.
        """

    try:
        # Call OpenAI GPT model with the constructed prompt
        response = openai_client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        # Extract the text output from the response
        gpt_response = response.output_text
        # Remove possible code block wrappers from GPT output
        gpt_response = gpt_response.replace("```json", "").replace("```", "").strip()
        # Parse the JSON response
        return json.loads(gpt_response)
    except Exception as e:
        # Raise a runtime error if anything goes wrong
        raise RuntimeError(f"Erreur : {str(e)}")

