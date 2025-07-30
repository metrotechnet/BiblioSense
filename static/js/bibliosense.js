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
        // Fetch and display the initial list of books
        const books = await dataService.fetchBooks();
        domService.renderBookList(books.book_list);
    } catch (error) {
        domService.showError("Erreur lors du chargement des livres. Veuillez réessayer plus tard.");
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
                domService.startSpinner();
                const result = await dataService.searchBooks(query);
                domService.stopSpinner();
                searchInput.value = "";
                domService.clearContainer();

                if (!result || !result.book_list || result.book_list.length === 0) {
                    domService.showError("Aucun résultat trouvé.");
                    return;
                }

                // Show a message with the number of results found
                const message = (result.description || "") + " (" + (result.book_list ? result.book_list.length : 0) + " documents trouvés)";
                domService.showSuccess(message);

                // Display the search results
                domService.renderBookList(result.book_list);

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

    domService.clearContainer();

    dataService.fetchBooks()
        .then(data => {
            if (data && data.book_list) {
                domService.renderBookList(data.book_list);
            } else {
                domService.showError("Aucun livre disponible.");
            }
        })
        .catch(error => {
            console.error("Error resetting book list:", error);
            domService.showError("Erreur lors de la réinitialisation de la liste des livres.");
        });
}
