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
        dataService.fetchBooks("all");
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
