import pandas as pd
from openai import OpenAI
import json
import os
import time
from utils.config import  get_secret

# Configure your OpenAI API key
#
    
BOOK_DATABASE_FILE = "../dbase/prenumerique_complet.json"
OUTPUT_FILE = "book_dbase.json"
TAXONOMY_FILE = "../dbase/classification_books.json"

# Configuration de base
DEFAULT_SECRET_ID = "openai-api-key"
DEFAULT_CREDENTIALS_PATH = "../bibliosense-467520-789ce439ce99.json"
PROJECT_ID = "bibliosense-467520"  # valeur par défaut
def init_openai_client():
    """
    Initialize OpenAI client with API key from Secret Manager or environment variables.
    """
    global openai_client
    
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

openai_client = init_openai_client()
# Load taxonomy from file
with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
    taxonomy = json.load(f)

# Load books data
livres_df = pd.read_json(BOOK_DATABASE_FILE, encoding="utf-8")

def classify_with_gpt(bookinfo, taxonomy, language):
    """
    Classifies a book using GPT based on the provided taxonomy and language.
    Returns a dictionary with 'description' and 'classification'.
    """
    prompt = f"""
        Tu es un classificateur de livres.
        Voici la taxonomie des livres :
        {json.dumps(taxonomy, ensure_ascii=False, indent=2)}

        Classe le livre suivant dans ces catégories.
        Rédige une phrase de description dans la langue spécifiée pour chaque livre.
        Le livre est en {language}.
        Voici les informations du livre :
        {json.dumps(bookinfo, ensure_ascii=False, indent=2)}

        Format de réponse attendu :
        Réponds uniquement avec un objet JSON structuré comme suit :
        {{
            "description": "Description du livre",
            "classification": même structure que la taxonomie, avec les catégories et sous-catégories présentes dans la taxonomie. Pour chaque catégorie, indique la valeur correspondante ou null si non applicable.
        }}

        Additional Guidelines:
        - La clé "classification" doit reprendre exactement la même structure (catégories, sous-catégories, clés) que la taxonomie fournie.
        - Retourne uniquement l'objet JSON structuré — sans explications, commentaires ou formatage Markdown.
        - Ne retourne aucune explication — seulement le JSON résultant.
        - Si une catégorie ou sous-catégorie ne s'applique pas, indique sa valeur comme null.
        """
    try:
        # Call OpenAI API for classification
        response = openai_client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        gpt_response = response.output_text
        # Remove possible code block wrappers
        gpt_response = gpt_response.replace("```json", "").replace("```", "").strip()
        return json.loads(gpt_response)
    except Exception as e:
        raise RuntimeError(f"Erreur : {str(e)}")

# Prepare to write results to output file
# Clear output file and start JSON array
with open(OUTPUT_FILE, "w", encoding="utf-8") as jf:
    jf.write("[\n")  # Start of JSON array

# Iterate over each book and classify
for idx, row in livres_df.iterrows():
    book_id = f"book_{idx}"

    # Convert row to dictionary
    book_dict = row.to_dict()

    # Prepare book data structure
    book_data = {"id": book_id, "label": row['titre'], "type": "book"}
    book_data.update(book_dict)
    # Classify the book using GPT
    gpt_response = classify_with_gpt(book_dict, taxonomy, book_dict["langue"])
    if not gpt_response:
        print(f"Erreur de classification pour le livre {book_id}: réponse vide")
        continue
    # Add classification and description to book data
    book_data["classification"] = json.dumps(gpt_response["classification"], ensure_ascii=False)
    book_data["description"] = gpt_response["description"]
    # Write book data as a JSON line in the output file
    with open(OUTPUT_FILE, "a", encoding="utf-8") as jf:
        jf.write(json.dumps(book_data, ensure_ascii=False) + ",\n")
    print(f" Livre {book_id} classifié: {book_dict['titre']}")

# Finalize the JSON array in the output file
with open(OUTPUT_FILE, "rb+") as jf:
    jf.seek(-3, 2)  # Go to the last ",\n"
    jf.truncate()  # Remove the last ",\n"
    jf.write(b"\n]")  # Close the JSON array with a newline before ]
jf.close()
print(f"Classification terminée. {len(livres_df)} livres classifiés.")
