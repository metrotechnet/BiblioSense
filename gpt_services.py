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

        ### Format de réponse attendu (strictement au format JSON) :
        {{
        "Taxonomie": {{structure taxonomique filtrée}},
        "Mots-clés": {{
            "titre": "mot_clé_1",
            "auteur": "mot_clé_2",
            "resume": "mot_clé_3",
            "editeur": "mot_clé_4",
            "langue": "mot_clé_5",
            "categorie": "mot_clé_6",
            "parution": "mot_clé_7",
            "pages": "mot_clé_8"
        }}
        }}
        - N'inclus que les champs pertinents pour la requête.
        - Si une information est absente, omets simplement le champ.
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


def taxonomy_to_description_with_gpt(categories, openai_client):
    """
    Use GPT to convert a taxonomy structure into a plain French description.

    Args:
        categories (dict): Taxonomy returned by GPT, with categories and keywords.
        openai_client (OpenAI): Instance du client OpenAI configuré.

    Returns:
        str: Human-readable French description.
    """
    try:
        # Build prompt for GPT
        prompt = f"""
        Tu es un assistant spécialisé en vulgarisation. 
        Transforme la taxonomie ci-dessous en une description simple, claire et fluide en français, destinée à un lecteur non spécialiste. 
        Exprime-toi avec des phrases complètes et évite tout jargon technique.

        ### Taxonomie :
        {json.dumps(categories, ensure_ascii=False, indent=2)}

        ### Exemple de style attendu :
        "Les livres sont classés dans les catégories suivantes : Fiction, Non-fiction et Philosophie. 
        Les mots-clés utiles pour la recherche incluent le titre, l'auteur et la langue."

        ### Contraintes :
        - Fournis uniquement le texte final, sans JSON, balises ou annotations.
        - Ta réponse doit être concise et agréable à lire.
        """

        # Call GPT to generate the description
        response = openai_client.responses.create(
            model="gpt-3.5-turbo",
            input=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        # Extract the text response
        description = response.output_text.strip()
        return description

    except Exception as e:
        print(f"Erreur lors de la génération de la description avec GPT : {e}")
        return "Une erreur est survenue lors de la génération de la description."
