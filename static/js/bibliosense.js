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
        // Initialize cookie validation first
        const cookiesValid = domService.initializeCookieValidation();
        
        if (!cookiesValid) {
            console.warn('Cookie validation failed, but continuing with limited functionality');
        }
        
        // Show welcome instructions by default (already in HTML)
        showWelcomeInstructions();
    } catch (error) {
        console.error('Error during application initialization:', error);
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
                // Hide welcome instructions and show book list
                hideWelcomeInstructions();
                
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
                // Stop spinner after search is complete    
                domService.stopSpinner();
                // Clear the search input field
                searchInput.value = "";
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
    const welcomeDiv = document.getElementById("welcome-instructions");
    const bookList = document.getElementById("book-list");
    
    if (welcomeDiv) {
        welcomeDiv.style.display = "block";
    }
    if (bookList) {
        bookList.style.display = "none";
    }
}

/**
 * Hide welcome instructions and show book list.
 */
function hideWelcomeInstructions() {
    const welcomeDiv = document.getElementById("welcome-instructions");
    const bookList = document.getElementById("book-list");
    
    if (welcomeDiv) {
        welcomeDiv.style.display = "none";
    }
    if (bookList) {
        bookList.style.display = "block";
    }
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
