// dataService.js

// The dataService object provides methods to interact with the backend API for book data.
const dataService = {
    // Fetches all books from the server.
    async fetchBooks(source = "all", message = "") {
        try {
            // Send a GET request to the /books endpoint with the source parameter.
            const response = await fetch(`/books/0/100?source=${source}`)
                        .then(response => response.json())
                        .then(data => {
                            const paginationInfo = {
                                range: data.range,        // {start: 0, end: 19, count: 20}
                                total_count: data.total_count,  // 150
                                source: data.source       // 'filtered' ou 'all'
                            };
                            domService.renderBookList(data.book_list, message, "book-list", paginationInfo);
                        });

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
            // Parse the response JSON.
            const result = await response.json();
            console.log("Search result:", result);
            return result;

        } catch (error) {
            // Log and rethrow any errors encountered during the search.
            console.error("Error searching books:", error);
            throw error;
        }
    },
//get and print session info
    async getSessionInfo() {
        try {
            // Send a GET request to the /session_info endpoint.
            const response = await fetch('/session_info');
            // Check if the response is successful.
            if (!response.ok) {
                throw new Error(`Server error: ${response.status} ${response.statusText}`);
            }
            // Parse the response JSON.
            const sessionInfo = await response.json();
            console.log("Session info:", sessionInfo);
            return sessionInfo;

        } catch (error) {
            // Log and rethrow any errors encountered while fetching session info.
            console.error("Error fetching session info:", error);
            throw error;
        }
    }

};
