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
BASE_URL = "https://quebec.pretnumerique.ca/resources?availability=_unselected&category_standard=thema&sort_by=issued_on_desc&view=details"
OUTPUT_FILE = "livres_pretnumerique.json"
DELAY = 2  # Wait time for page loading (in seconds)

# -------- Selenium Setup --------
# options.add_argument("--headless")  # Uncomment to run browser in headless mode
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(BASE_URL)

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
WebDriverWait(driver, 20).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-details"))
)
time.sleep(DELAY)

books_data = []

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

# -------- Main scraping loop --------
book_index = 0
page_index = 1

# Clear JSON file before writing
with open(OUTPUT_FILE, "w", encoding="utf-8") as jf:
    jf.write("[\n")  # Start of JSON array

while True:
    # Extract all book links from the current page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    book_links = [f"https://quebec.pretnumerique.ca{a['href']}" for a in soup.select(".details-content__actions a") if a.get("href")]
    
    for link in book_links:
        try:
            book_details = extract_book_details(link)
            books_data.append(book_details)
            # Append book details to JSON file in array format
            with open(OUTPUT_FILE, "a", encoding="utf-8") as jf:
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
        print(f"Erreur lors de la navigation vers la page suivante: {e}")
        break

# Finalize the JSON file
if books_data:
    # Remove the last comma and close the JSON array
    with open(OUTPUT_FILE, "rb+") as jf:
        jf.seek(-3, 2)  # Go to the last ",\n"
        jf.truncate()  # Remove the last ",\n"
        jf.write(b"\n]")  # Close the JSON array with a newline before ]
    jf.close()
else:
    # If no books were found, write an empty JSON array
    with open(OUTPUT_FILE, "w", encoding="utf-8") as jf:
        jf.write("[]")

driver.quit()
print(f"Extraction terminée. {len(books_data)} livres enregistrés dans {OUTPUT_FILE}")
