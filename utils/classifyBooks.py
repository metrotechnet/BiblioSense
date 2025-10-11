import pandas as pd
from openai import OpenAI
import json
import os
import time
from config import  get_secret

# Configure your OpenAI API key
#
    
BOOK_DATABASE = "./dbase/prenumerique_montreal_complet.json"
OUTPUT_FILE = "book_dbase_montreal.json"
TAXONOMY_FILE = "./dbase/classification_books.json"

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

# Global variables
openai_client = None
taxonomy = None
livres_df = None

def init():
    """
    Initialize all required components: OpenAI client, taxonomy, and books data.
    """
    global openai_client, taxonomy, livres_df
    
    print("🔧 Initializing BiblioSense Classification System...")
    
    # Initialize OpenAI client
    print("   📡 Initializing OpenAI client...")
    openai_client = init_openai_client()
    
    # Load taxonomy from file
    print("   📚 Loading taxonomy...")
    try:
        with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
            taxonomy = json.load(f)
        print(f"   ✅ Taxonomy loaded: {len(taxonomy)} categories")
    except Exception as e:
        print(f"   ❌ Error loading taxonomy: {e}")
        raise
    
    # Load books data
    print("   📖 Loading books database...")
    try:
        livres_df = pd.read_json(BOOK_DATABASE, encoding="utf-8")
        print(f"   ✅ Books loaded: {len(livres_df)} books")
    except Exception as e:
        print(f"   ❌ Error loading books database: {e}")
        raise
    
    print("✅ Initialization completed successfully!")
    return openai_client, taxonomy, livres_df

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
    # try:
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
        # Affiche la réponse brute pour debug
        # print("Réponse GPT brute:", gpt_response)
    try:
        import re
        corrected = re.sub(r'}\s*{', '}, {', gpt_response)
        corrected = re.sub(r']\s*\[', '], [', corrected)
        return json.loads(gpt_response)
    except Exception as e:
        print(f"Exception caught: {e}")
        result = None  # or set a default value, or skip, or log, etc.
        pass       
    # except Exception as e:
    #     raise RuntimeError(f"Erreur : {str(e)}")

def classify_books(start_index=0, end_index=None):
    """
    Classify books from the database using GPT.
    
    Args:
        start_index (int): Index to start classification from
        end_index (int): Index to end classification at (None for all remaining)
    """
    global livres_df, taxonomy, openai_client, OUTPUT_FILE
    
    # Check if system is initialized
    if livres_df is None or taxonomy is None or openai_client is None:
        print("❌ System not initialized. Please call init() first.")
        return 0, 1
    
    if end_index is None:
        end_index = len(livres_df)
    
    print(f"🚀 Starting book classification from index {start_index} to {end_index}")
    print(f"📚 Total books to process: {end_index - start_index}")
    
    classified_count = 0
    error_count = 0
    
    # Iterate over each book and classify
    for idx, row in livres_df.iterrows():
        if idx < start_index:
            continue
        if idx >= end_index:
            break
            
        book_id = f"book_{idx}"

        # Convert row to dictionary
        book_dict = row.to_dict()

        # Prepare book data structure
        book_data = {"id": book_id, "label": row['titre'], "type": "book"}
        book_data.update(book_dict)
        
        try:
            # Classify the book using GPT
            gpt_response = classify_with_gpt(book_dict, taxonomy, book_dict["langue"])
            if not gpt_response:
                print(f"❌ Erreur de classification pour le livre {book_id}: réponse vide")
                error_count += 1
                continue
                
            # Add classification and description to book data
            book_data["classification"] = json.dumps(gpt_response["classification"], ensure_ascii=False)
            book_data["description"] = gpt_response["description"]
            
            # Write book data as a JSON line in the output file
            with open(OUTPUT_FILE, "a", encoding="utf-8") as jf:
                jf.write(json.dumps(book_data, ensure_ascii=False) + ",\n")
            
            classified_count += 1
            print(f"✅ Livre {book_id} classifié: {book_dict['titre']}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la classification du livre {book_id}: {e}")
            error_count += 1
            continue

    print(f"📊 Classification terminée:")
    print(f"   - Livres classifiés: {classified_count}")
    print(f"   - Erreurs: {error_count}")
    
    return classified_count, error_count

def finalize_json_file():
    """
    Finalize the JSON array in the output file by removing the last comma and closing the array.
    """
    try:
        with open(OUTPUT_FILE, "rb+") as jf:
            jf.seek(-3, 2)  # Go to the last ",\n"
            jf.truncate()  # Remove the last ",\n"
            jf.write(b"\n]")  # Close the JSON array with a newline before ]
        print(f"✅ Fichier JSON finalisé: {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Erreur lors de la finalisation du fichier JSON: {e}")

def run_classification(start_index=0, end_index=None, auto_finalize=False):
    """
    Convenience function to run classification with initialization.
    
    Args:
        start_index (int): Index to start classification from
        end_index (int): Index to end classification at (None for all remaining)
        auto_finalize (bool): Whether to automatically finalize the JSON file
        
    Returns:
        tuple: (classified_count, error_count)
    """
    # Initialize if not already done
    if livres_df is None or taxonomy is None or openai_client is None:
        print("🔧 Auto-initializing system...")
        try:
            init()
        except Exception as e:
            print(f"❌ Auto-initialization failed: {e}")
            return 0, 1
    
    # Run classification
    classified_count, error_count = classify_books(start_index, end_index)
    
    # Auto-finalize if requested and there were successful classifications
    if auto_finalize and classified_count > 0:
        finalize_json_file()
    
    return classified_count, error_count

def main():
    """
    Main function to run the book classification process.
    """
    print("🚀 BiblioSense - Classification des Livres")
    print("=" * 50)
    
    # Initialize the system
    try:
        init()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Display configuration
    print(f"\n📋 Configuration:")
    print(f"📁 Base de données: {BOOK_DATABASE}")
    print(f"📄 Fichier de sortie: {OUTPUT_FILE}")
    print(f"🗂️  Fichier taxonomie: {TAXONOMY_FILE}")
    print(f"📚 Nombre total de livres: {len(livres_df)}")
    print("-" * 50)
    
    # Ask user for start index (or use default)
    try:
        start_idx = int(input("Index de départ (défaut: 0): ") or "0")
    except ValueError:
        start_idx = 0
    
    # Ask user for end index (or process all remaining)
    try:
        end_input = input(f"Index de fin (défaut: {len(livres_df)} - tous): ")
        end_idx = int(end_input) if end_input else len(livres_df)
    except ValueError:
        end_idx = len(livres_df)
    
    # Confirm before starting
    books_to_process = end_idx - start_idx
    print(f"\n📋 Configuration:")
    print(f"   - Index de départ: {start_idx}")
    print(f"   - Index de fin: {end_idx}")
    print(f"   - Livres à traiter: {books_to_process}")
    
    if books_to_process <= 0:
        print("❌ Aucun livre à traiter avec cette configuration.")
        return
    
    confirm = input("\nContinuer? (y/N): ").lower().strip()
    if confirm not in ['y', 'yes', 'oui']:
        print("❌ Classification annulée.")
        return
    
    # Start classification
    start_time = time.time()
    classified_count, error_count = classify_books(start_idx, end_idx)
    end_time = time.time()
    
    # Display results
    duration = end_time - start_time
    print(f"\n🎉 Classification terminée!")
    print(f"   - Durée: {duration:.2f} secondes")
    print(f"   - Vitesse: {classified_count/duration:.2f} livres/seconde")
    
    # Ask if user wants to finalize the JSON file
    if classified_count > 0:
        finalize_confirm = input("\nFinaliser le fichier JSON? (y/N): ").lower().strip()
        if finalize_confirm in ['y', 'yes', 'oui']:
            finalize_json_file()

if __name__ == "__main__":
    main()
