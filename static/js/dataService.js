// dataService.js

// The dataService object provides methods to interact with the backend API for book data.
const dataService = {
    // Fetches all books from the server.
    async fetchBooks() {
        try {
            // Send a GET request to the /books endpoint.
            const response = await fetch("/books");
            // Check if the response is successful.
            if (!response.ok) {
                throw new Error(`Failed to fetch books: ${response.status} ${response.statusText}`);
            }
            // Parse and return the JSON data from the response.
            return await response.json();
        } catch (error) {
            // Log and rethrow any errors encountered during the fetch.
            console.error("Error fetching book data:", error);
            throw error;
        }
    },

    // Searches for books matching the given query.
    async searchBooks(query) {
        try {
            // Send a POST request to the /filter endpoint with the search query in the request body.
            const response = await fetch('/filter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            // Check if the response is successful.
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            // Parse and return the JSON data from the response.
            return await response.json();
        } catch (error) {
            // Log and rethrow any errors encountered during the search.
            console.error("Error searching books:", error);
            throw error;
        }
    }
};
