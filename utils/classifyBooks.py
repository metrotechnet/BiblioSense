import pandas as pd
from openai import OpenAI
import json
import os
# Configure your OpenAI API key
# OpenAI API key depuis les variables d'environnement
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY n'est pas définie dans les variables d'environnement")
    
BOOK_DATABASE_FILE = "dbase/livres_pretnumerique.json"
OUTPUT_FILE = "book_dbase.json"
TAXONOMY_FILE = "dbase/classification_books.json"

openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
            model="gpt-4o",
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
