// static/js/bibliosense.js
/**
 * bibliosense.js
 * Handles book search, result display, and list reset functionality.
 *
 * @file bibliosense.js
 * @author Denis Boulanger
 * @date 2025-07-30
 * @version 1.0
 * @description
 *   - Fetches book data from the backend and displays it in a list.
 *   - Allows users to search for books and view results.
 *   - Provides a reset button to show all books again.
 *   - Uses Fetch API for server communication and updates the DOM dynamically.
 * @requires Bootstrap for UI styling.
 *
 * @todo Add unit tests for search and rendering logic.
 * @todo Improve accessibility of book list items.
 * @todo Add dark mode toggle.
 */

// Wait for the DOM to be fully loaded before running scripts
document.addEventListener("DOMContentLoaded", async function () {
    try {
        // Show welcome instructions instead of loading books immediately
        showWelcomeInstructions();
    } catch (error) {
        domService.showError("Erreur lors du chargement de l'application. Veuillez réessayer plus tard.");
    }

    // Get references to UI elements
    const searchBtn = document.getElementById("search-btn");
    const searchInput = document.getElementById("search-input");
    const resetBtn = document.getElementById("reset-btn");

    // Set up search button and input event listeners
    if (searchBtn && searchInput) {
        searchBtn.addEventListener("click", async () => {
            const query = searchInput.value.trim();
            if (!query) return;

            try {
                // Start spinner to indicate loading state
                domService.startSpinner();

                // Perform the search using the data service
                const result = await dataService.searchBooks(query);

                // Stop spinner after search is complete    
                domService.stopSpinner();
                // Clear the search input field
                searchInput.value = "";


                // Show a message with the number of results found
                const message = (result.description || "") + " (" + result.total_books + " documents trouvés)";
                // Fetch filtered books to update the list
                dataService.fetchBooks("filtered", message);

            } catch (error) {
                domService.showError("Erreur lors de la recherche. Veuillez réessayer.");
            }
        });

        // Allow pressing Enter in the search input to trigger search
        searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") searchBtn.click();
        });
    }

    // Set up reset button event listener
    if (resetBtn) {
        resetBtn.addEventListener("click", resetBookList);
    }
});

/**
 * Resets the book list to show all books.
 * Clears the search input and description area, then fetches and displays all books.
 */
function resetBookList() {
    const searchInput = document.getElementById("search-input");
    if (searchInput) searchInput.value = "";

    dataService.fetchBooks("all");
}

/**
 * Show welcome instructions when the page loads for the first time.
 */
function showWelcomeInstructions() {
    const container = document.getElementById("book-list");
    if (!container) return;

    container.innerHTML = `
        <div class="welcome-instructions" style="text-align: center; padding: 20px 20px; color: #555;">
            <div style="font-size: 2rem; color: #007bff; margin-bottom: 20px;">
                <i class="bi bi-book"></i>
            </div>
            <h3 style="color: #333; margin-bottom: 20px;">Bienvenue sur BiblioSense !</h3>
            <p style="font-size: 1.1rem; margin-bottom: 15px; line-height: 1.6;">
                Votre assistant intelligent pour découvrir des livres que vous allez adorer.
            </p>
            <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #007bff;">
                <h4 style="color: #007bff; margin-bottom: 15px;">
                    <i class="bi bi-lightbulb"></i> Comment utiliser BiblioSense :
                </h4>
                <div style="text-align: left; max-width: 500px; margin: 0 auto;">
                    <p style="margin-bottom: 10px;">
                        <strong>✨ Décrivez vos goûts :</strong> Entrez un sujet, un auteur ou un titre que vous aimez
                    </p>
                    <p style="margin-bottom: 10px;">
                        <strong>🤖 L'IA analyse :</strong> Notre assistant comprend vos préférences
                    </p>
                    <p style="margin-bottom: 10px;">
                        <strong>📚 Découvrez :</strong> Recevez des recommandations personnalisées
                    </p>
                </div>
            </div>
            <div style="margin-top: 30px;">
                <p style="color: #666; font-style: italic;">
                    Commencez par faire une recherche ci-dessus pour découvrir des livres recommandés !
                </p>
            </div>
        </div>
    `;
}

// Handle window resize to update book display format
let resizeTimeout;
window.addEventListener("resize", () => {
    // Debounce resize events to avoid excessive re-rendering
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // Get current book list
        const bookListContainer = document.getElementById("book-list");
        if (bookListContainer && bookListContainer.children.length > 0) {
            // Store current books data if available
            const currentBooks = window.currentBooksData;
            if (currentBooks) {
                // Re-render books with appropriate format for current screen size
                domService.renderBookList(currentBooks, "", "book-list");
            }
        }
    }, 250); // Wait 250ms after resize stops
});
