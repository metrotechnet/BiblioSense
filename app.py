from flask import Flask, jsonify, render_template, request
import pandas as pd
from openai import OpenAI
import json
from waitress import serve
import os
import time
from gpt_services import get_catagories_with_gpt,  get_secret

# -------------------- Global Data Storage --------------------

# Global variables to store loaded data
taxonomy_data = None
books_data = None
openai_client = None

# -------------------- Configuration --------------------

# Paths to JSON files for taxonomy and book data
BOOK_DATABASE_FILE = "dbase/book_dbase.json"
TAXONOMY_FILE = "dbase/classification_books.json"

# Configuration de base
DEFAULT_SECRET_ID = "openai-api-key"
DEFAULT_CREDENTIALS_PATH = "../bibliosense-467520-789ce439ce99.json"
PROJECT_ID = "bibliosense-467520"  # valeur par défaut

# -------------------- Initialization Functions --------------------

def init_data():
    """
    Initialize and load taxonomy and book data from JSON files.
    This function should be called once at application startup.
    """
    global taxonomy_data, books_data
    
    try:
        # Load taxonomy data
        with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
            taxonomy_data = json.load(f)
        print(f"✅ Taxonomy data loaded from {TAXONOMY_FILE}")
        
        # Load book data
        with open(BOOK_DATABASE_FILE, "r", encoding="utf-8") as f:
            books_data = json.load(f)
        print(f"✅ Book data loaded from {BOOK_DATABASE_FILE} ({len(books_data)} books)")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise

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

# -------------------- Flask Application Factory --------------------

def create_app():
    """
    Application factory pattern for Flask app creation.
    """
    app = Flask(__name__)
    
    # Initialize data and services
    init_data()
    init_openai_client()
    
    # -------------------- Flask Routes --------------------

    @app.route("/")
    def index():
        """
        Render the main graph visualization page.
        """
        return render_template("index.html")

    @app.route("/books")
    def books_data_route():
        """
        Return the book graph data (nodes and edges) as JSON for the frontend.
        """
        global books_data
        return {"book_list": books_data}

    @app.route("/filter", methods=["POST"])
    def filter_categories():
        """
        Filter books based on a user query using GPT classification.

        Receives JSON with a 'query' field.
        Uses GPT to classify the query into taxonomy categories and keywords.
        Filters books by taxonomy and keywords, scores matches, and returns sorted results with a description.
        """
        # Start timing
        start_time = time.time()
        
        global taxonomy_data, books_data, openai_client
        
        data = request.get_json()
        text = data.get("query", "")
        
        print(f"🔍 Processing query: '{text}'")

        try:
            # Get categories and keywords from GPT (sequential calls since second depends on first)
            gpt_start = time.time()
            categories = get_catagories_with_gpt(text, taxonomy_data, openai_client)
            total_gpt_time = time.time() - gpt_start
            print(f"⏱️  GPT categories classification: {total_gpt_time:.2f}s")
            print(f"Categories from GPT: {categories}")
            

            # Book filtering logic
            filter_start = time.time()
            filteredNodes = []
            
            # Single pass through books with optimized scoring
            scored_books = []
            for book in books_data:
                taxonomy_score = 0
                keyword_score = 0
                
                # Parse book taxonomy once
                try:
                    book_taxonomy = json.loads(book.get("classification", "{}"))
                except (json.JSONDecodeError, TypeError):
                    book_taxonomy = {}
                
                # Check taxonomy matches using pre-processed lookup
                for taxo_key, taxo_classes in categories["Taxonomie"].items():
                    if taxo_key in book_taxonomy:
                        for sub_key, sub_values_set in taxo_classes.items():
                            if sub_key in book_taxonomy[taxo_key]:
                                book_values = book_taxonomy[taxo_key][sub_key]
                                if isinstance(book_values, list):
                                    # Use set intersection for faster matching
                                    matches = set(sub_values_set).intersection(set(book_values))
                                    taxonomy_score += len(matches)
                                elif book_values in sub_values_set:
                                    taxonomy_score += 1
                
                # Check keyword matches with pre-lowercased keywords
                for keyword_key, keyword_value_lower in categories["Mots-clés"].items():
                    book_field = book.get(keyword_key, "")
                    if book_field and keyword_value_lower.lower() in book_field.lower():
                        keyword_score += 1
                
                # Calculate total score with keyword priority
                # Keywords get 10x weight to appear at top of results
                total_score = (keyword_score * 10) + taxonomy_score
                
                # Only add books with positive scores
                if total_score > 0:
                    book_copy = book.copy()  # Avoid modifying original data
                    book_copy["score"] = total_score
                    book_copy["keyword_matches"] = keyword_score
                    book_copy["taxonomy_matches"] = taxonomy_score
                    scored_books.append(book_copy)
            
            # Sort by descending score (keywords will be at top due to higher weight)
            filteredNodes = sorted(scored_books, key=lambda x: x["score"], reverse=True)
            
            filter_time = time.time() - filter_start
            print(f"⏱️  Book filtering: {filter_time:.2f}s")

            # Calculate total time
            total_time = time.time() - start_time
            
            print(f"📊 Performance Summary:")
            print(f"   - Total GPT time: {total_gpt_time:.2f}s ({(total_gpt_time/total_time)*100:.1f}%)")
            print(f"   - Book filtering: {filter_time:.2f}s ({(filter_time/total_time)*100:.1f}%)")
            print(f"   - Total request time: {total_time:.2f}s")
            print(f"   - Books found: {len(filteredNodes)}")
            
            # Log keyword vs taxonomy matches
            keyword_matches = sum(1 for book in filteredNodes if book.get("keyword_matches", 0) > 0)
            taxonomy_only = len(filteredNodes) - keyword_matches
            print(f"   - Keyword matches: {keyword_matches} (priority)")
            print(f"   - Taxonomy only: {taxonomy_only}")

            # If no books found
            if not filteredNodes:
                return jsonify({
                    "book_list": [], 
                    "description": "Aucun livre trouvé pour cette requête."
                })

            # Return filtered books and description with performance metrics
            return jsonify({
                "book_list": filteredNodes, 
                "description": categories["Description"]
            })

        except json.JSONDecodeError as e:
            total_time = time.time() - start_time
            print(f"❌ JSON Decode Error: {e} (after {total_time:.2f}s)")
            categories_labels = []
        except Exception as e:
            total_time = time.time() - start_time
            print(f"❌ Error in GPT call: {e} (after {total_time:.2f}s)")
            categories_labels = []

        return jsonify(categories_labels)
    
    return app

# -------------------- Main Entry Point --------------------

if __name__ == "__main__":
    print("Starting BiblioSense app...")
    
    # Create the Flask app using the factory pattern
    app = create_app()
    
    # Get port from environment variable for Cloud Run compatibility
    port = int(os.environ.get('PORT', 8080))
    
    # Detect environment
    is_local = os.environ.get('PORT') is None  # No PORT env var = local development
    
    if is_local:
        print("🔧 Running in LOCAL development mode")
        # Use Flask's development server with debug mode but without reloader
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    else:
        print("🚀 Running in PRODUCTION mode (Cloud Run)")
        # Use Waitress for production
        serve(app, host='0.0.0.0', port=port)
