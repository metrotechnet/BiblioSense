from flask import Flask, jsonify, render_template, request
import pandas as pd
from openai import OpenAI
import json
from waitress import serve
import os

# -------------------- Configuration --------------------

# Initialize Flask app
app = Flask(__name__)

# -------------------- File Paths --------------------

# Paths to JSON files for taxonomy and book data
BOOK_DATABASE_FILE = "dbase/book_dbase.json"
TAXONOMY_FILE = "dbase/classification_books.json"

# -------------------- GPT Category Classification --------------------

# OpenAI API key depuis les variables d'environnement
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY n'est pas définie dans les variables d'environnement")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_catagories_with_gpt(text, taxonomy):
    """
    Use GPT to classify a book query into taxonomy categories.

    Args:
        text (str): User query or book description.
        taxonomy (list): Taxonomy nodes for context.

    Returns:
        list or dict: Parsed GPT response as JSON.
    """
    prompt = f"""
        Tu es un classificateur de requêtes pour la recherche de livres. Ton rôle est d'analyser une requête utilisateur et de la classer dans les catégories de la taxonomie fournie.

        Voici la taxonomie des livres :
        {json.dumps(taxonomy, ensure_ascii=False, indent=2)}

        Voici les mots-clés disponibles pour la recherche :
        - titre : le titre du livre.
        - auteur : le nom ou les noms des auteurs.
        - resume : le résumé ou la description du livre.
        - editeur : le nom de l'éditeur.
        - langue : la langue dans laquelle le livre est écrit.
        - categorie : la catégorie ou le domaine du livre.
        - parution : la date de publication ou d'édition.
        - pages : le nombre de pages du livre.

        Analyse la requête suivante et retourne uniquement un objet JSON contenant les catégories pertinentes et les mots-clés associés.

        Requête utilisateur : {text}

        Format de réponse attendu :
        {{
            "Taxonomie": {{
                "Catégories": meme structure de la taxonomie filtrée
            }},
            "Mots-clés": {{
                "titre": "mot_clé_1",
                "auteur": "mot_clé_2"
                // Autres mots-clés selon la taxonomie
            }}
        }}
        """
    try:
        # Call OpenAI GPT model with the constructed prompt
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
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

def taxonomy_to_description_with_gpt(categories):
    """
    Use GPT to convert a taxonomy structure into a plain French description.

    Args:
        categories (dict): Taxonomy returned by GPT, with categories and keywords.

    Returns:
        str: Human-readable French description.
    """
    try:
        # Build prompt for GPT
        prompt = f"""
        Tu es un assistant intelligent. Ton rôle est de transformer une taxonomie structurée en une description simple et lisible en français.

        Voici la taxonomie structurée :
        {json.dumps(categories, ensure_ascii=False, indent=2)}

        Transforme cette taxonomie en une description claire et concise en français. Utilise des phrases complètes et évite les termes techniques.

        Exemple de description attendue :
        "Les livres sont classés dans les catégories suivantes : Fiction, Non-fiction, et Philosophie. Les mots-clés pertinents pour la recherche incluent le titre, l'auteur, et la langue."

        Fournis uniquement la description en texte clair, sans aucun format JSON ou annotation supplémentaire.
        """

        # Call GPT to generate the description
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
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

# -------------------- Flask Routes --------------------

@app.route("/")
def index():
    """
    Render the main graph visualization page.
    """
    return render_template("index.html")

@app.route("/books")
def books_data():
    """
    Return the book graph data (nodes and edges) as JSON for the frontend.
    """
    # Read book data from book_dbase.json
    with open(BOOK_DATABASE_FILE, "r", encoding="utf-8") as f:
        books_data = json.load(f)

    return {"book_list": books_data}

@app.route("/filter", methods=["POST"])
def filter_categories():
    """
    Filter books based on a user query using GPT classification.

    Receives JSON with a 'query' field.
    Uses GPT to classify the query into taxonomy categories and keywords.
    Filters books by taxonomy and keywords, scores matches, and returns sorted results with a description.
    """
    data = request.get_json()
    text = data.get("query", "")

    # Load taxonomy
    with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    # Load book nodes and links
    with open(BOOK_DATABASE_FILE, "r", encoding="utf-8") as f:
        books_data = json.load(f)

    try:
        # Get categories and keywords from GPT (dict or list structure)
        categories = get_catagories_with_gpt(text, taxonomy)
        print(f"Categories from GPT: {categories}")
        filteredNodes = []
        description = taxonomy_to_description_with_gpt(categories["Taxonomie"])
        print(f"Description from GPT: {description}")

        # Compare each book's taxonomy with GPT result and score matches
        for book in books_data:
            book["score"] = 0
            book_taxonomy = json.loads(book.get("classification", {}))
            for taxo_key, taxo_class in categories["Taxonomie"].items():
                for sub_key, sub_values in taxo_class.items():
                    for val in sub_values:
                        if taxo_key in book_taxonomy and sub_key in book_taxonomy[taxo_key]:
                            if val in book_taxonomy[taxo_key][sub_key]:
                                if book["score"] == 0:
                                    filteredNodes.append(book)
                                book["score"] += 1

        # Search for keyword matches in books
        for book in books_data:
            for keyword_key, keyword_value in categories["Mots-clés"].items():
                if keyword_value.lower() in book.get(keyword_key, "").lower():
                    if book["score"] == 0:
                        filteredNodes.append(book)
                    book["score"] += 1

        # Keep only books with score > 0
        filteredNodes = [book for book in filteredNodes if book.get("score", 0) > 0]
        # Sort by descending score
        filteredNodes.sort(key=lambda x: x.get("score", 0), reverse=True)

        # If no books found
        if not filteredNodes:
            return jsonify({"book_list": [], "description": "Aucun livre trouvé pour cette requête."})

        # Return filtered books and description
        return jsonify({"book_list": filteredNodes, "description": description})

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        categories_labels = []
    except Exception as e:
        print(f"Error in GPT call: {e}")
        categories_labels = []

    return jsonify(categories_labels)

# -------------------- Main Entry Point --------------------

if __name__ == "__main__":
    # Run the Flask app in debug mode (for development)
    app.run(debug=True)
    # For production, use waitress (uncomment below)
    # serve(app, host='0.0.0.0', port=8000)
