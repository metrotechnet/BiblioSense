import json
import re

# Chemin du fichier JSON
FILENAME = "dbase/book_dbase.json"

# Regex pour détecter un mot collé (ex : chiffre suivi d'une majuscule, minuscule suivie d'une majuscule sans espace)
COLLISION_PATTERN = re.compile(r"([a-zéèàâêîôûç0-9])([A-ZÉÈÀÂÊÎÔÛÇ])|([0-9])([A-ZÉÈÀÂÊÎÔÛÇ])")

def detect_collisions(filename):
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)
    print("Titres avec mots collés :")
    for book in data:
        titre = book.get("titre", "")
        if COLLISION_PATTERN.search(titre):
            print(f"{book.get('id')} - {titre}")
            # Ajouter un espace entre 
            corrected_title = COLLISION_PATTERN.sub(r"\1\3 \2\4", titre)
            print(f"  -> Suggestion : {corrected_title}")
            book["titre"] = corrected_title
            book["label"] = corrected_title
    # Sauvegarder les modifications dans le fichier
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    detect_collisions(FILENAME)