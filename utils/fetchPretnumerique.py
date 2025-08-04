from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager
import json

# -------- Configuration --------
# Base URL pattern for pretnumerique.ca with fiction categories
BASE_URL_PATTERN = "https://quebec.pretnumerique.ca/resources?availability=_unselected&category={}&category_standard=thema&sort_by=issued_on_desc"

# Category codes and corresponding output files
CATEGORIES = [
    ("FC", "Biographie_romancée.json"),
    ("FM", "fantasy.json"), 
    ("FB", "Fiction_générale_et_littéraire.json"),
    ("FY", "Fiction_particularités.json"),
    ("FN", "Mythe_et_légende_romancés.json"),
    ("FS", "Roman_abordant_la_vie_familiale.json"),
    ("FQ", "Roman_abordant_un_mode_de_vie.json"),
    ("FJ", "Roman_d_aventures.json"),
    ("FK", "Roman_d_épouvante_et_de_surnaturel.json"),
    ("FP", "Roman_érotique.json"),
    ("FV", "Roman_historique.json"),
    ("FU", "Roman_humoristique.json"),
    ("FF", "Roman_policier.json"),
    ("FW", "Roman_religieux_et_spirituel.json"),
    ("FR", "Roman_sentimental.json"),
    ("FD", "Roman_spéculatif.json"),
    ("FX", "Roman_thèmes_narratifs.json"),
    ("FT", "Sagas_familiales.json"),
    ("FL", "Science_fiction.json"),
    ("FH", "Thriller.json"),
]

# Generate BASE_URL and OUTPUT_FILE lists
BASE_URL = [BASE_URL_PATTERN.format(cat) for cat, _ in CATEGORIES]
OUTPUT_FILE = [filename for _, filename in CATEGORIES]
DELAY = 2  # Wait time for page loading (in seconds)

# -------- Selenium Setup --------
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Uncomment to run browser in headless mode

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_category(base_url, output_file):
    """Scrape books from a specific category URL and save to output file."""
    print(f"\n=== Scraping category: {output_file} ===")
    print(f"URL: {base_url}")
    
    driver.get(base_url)

    # Handle cookie consent pop-up if present
    try:
        consent_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accepter') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'j\'accepte') or contains(., 'OK') or contains(., 'ok') or contains(., 'Ok') or contains(., 'd\'accord') or contains(., 'D\'accord')]"))
        )
        consent_btn.click()
        time.sleep(DELAY)
    except Exception:
        pass  # No pop-up detected

    # Wait for initial page load
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-details"))
        )
        time.sleep(DELAY)
    except Exception as e:
        print(f"Erreur lors du chargement de la page: {e}")
        return []

    books_data = []
    book_index = 0
    page_index = 1

    # Clear JSON file before writing
    with open(output_file, "w", encoding="utf-8") as jf:
        jf.write("[\n")  # Start of JSON array

    while True:
        # Extract all book links from the current page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        book_links = [f"https://quebec.pretnumerique.ca{a['href']}" for a in soup.select(".details-content__actions a") if a.get("href")]
        
        if not book_links:
            print(f"Aucun livre trouvé sur la page {page_index}")
            break
            
        for link in book_links:
            try:
                book_details = extract_book_details(link)
                books_data.append(book_details)
                # Append book details to JSON file in array format
                with open(output_file, "a", encoding="utf-8") as jf:
                    jf.write(json.dumps(book_details, ensure_ascii=False) + ",\n")

                book_index += 1
                print(f" Page {page_index} Extrait {book_index}: {book_details['titre']}")
                driver.back()
                time.sleep(DELAY)

            except Exception as e:
                print(f"Erreur extraction {link}: {e}")

        # Look for the "Next page" button and navigate if available
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".next a"))
            )
            # Scroll to the button before clicking
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(5)
            next_button.click()
            time.sleep(DELAY)
            page_index += 1

        except Exception as e:
            print(f"Pas de page suivante ou erreur: {e}")
            break

    # Finalize the JSON file
    if books_data:
        # Remove the last comma and close the JSON array
        with open(output_file, "rb+") as jf:
            jf.seek(-3, 2)  # Go to the last ",\n"
            jf.truncate()  # Remove the last ",\n"
            jf.write(b"\n]")  # Close the JSON array with a newline before ]
    else:
        # If no books were found, write an empty JSON array
        with open(output_file, "w", encoding="utf-8") as jf:
            jf.write("[]")

    print(f"Catégorie terminée: {len(books_data)} livres enregistrés dans {output_file}")
    return books_data

def extract_cover_url(soup):
    """Extracts the cover image URL from the .display-cover-img div using BeautifulSoup."""
    cover_url = ""
    cover_div = soup.find("div", class_="display-cover-img")
    if cover_div:
        img = cover_div.find("img")
        if img and img.get("src"):
            cover_url = img["src"]
    return cover_url

def extract_metadata(soup, div, metadataName):
    """Extracts the value of the first span with itemprop=metadataName using BeautifulSoup."""
    span = soup.find(div, itemprop=metadataName)
    if span:
        return span.get_text(strip=True)
    return "Inconnu"

def extract_book_details(book_link):
    """Opens a book detail page and extracts its information."""
    driver.get(book_link)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".main-body"))
    )
    time.sleep(DELAY)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = soup.select_one(".header__title").get_text(strip=True) if soup.select_one(".header__title") else ""
    author = soup.select_one(".contributors").get_text(strip=True) if soup.select_one(".contributors") else ""
    summary = soup.select_one("#summary-expandable p").get_text(strip=True) if soup.select_one("#summary-expandable p") else ""
    
    editor = extract_metadata(soup, "span", "publisher")
    category = extract_metadata(soup, "span", "genre")
    parution = extract_metadata(soup, "dd", "datePublished")
    pages = extract_metadata(soup, "dd", "numberOfPages")
    langue = extract_metadata(soup, "span", "inLanguage")

    cover_url = extract_cover_url(soup)
    return {
        "titre": title,
        "auteur": author,
        "resume": summary,
        "lien": book_link,
        "categorie": category,
        "editeur": editor,
        "parution": parution,
        "pages": pages,
        "langue": langue,
        "couverture": cover_url
    }

# -------- Main execution --------
if __name__ == "__main__":
    total_books = 0
    
    try:
        # Iterate through all categories
        for i, (base_url, output_file) in enumerate(zip(BASE_URL, OUTPUT_FILE)):
            print(f"\n{'='*60}")
            print(f"Processing category {i+1}/{len(BASE_URL)}: {output_file}")
            print(f"{'='*60}")
            
            try:
                category_books = scrape_category(base_url, output_file)
                total_books += len(category_books)
                print(f"✓ Completed: {len(category_books)} books saved to {output_file}")
                
                # Short break between categories
                if i < len(BASE_URL) - 1:  # Don't sleep after the last category
                    print("Waiting 5 seconds before next category...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"✗ Error processing category {output_file}: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
    finally:
        driver.quit()
        print(f"\n{'='*60}")
        print(f"🎉 Extraction complete!")
        print(f"📚 Total books extracted: {total_books}")
        print(f"📁 Files created: {len(OUTPUT_FILE)}")
        print(f"{'='*60}")
