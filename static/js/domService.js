// domService.js

// Store the original HTML of the search button for later restoration
let originalBtnHTML = "";

// domService provides utility functions for DOM manipulation related to book lists and UI feedback
const domService = {
    /**
     * Display an error message inside a specified container.
     * @param {string} message - The error message to display.
     * @param {string} containerId - The ID of the container element.
     */
    showError(message, containerId = "book-list") {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = `<div class="alert alert-danger" role="alert">${message}</div>`;
    },

    /**
     * Display a success message inside a specified container.
     * @param {string} message - The success message to display.
     * @param {string} containerId - The ID of the container element.
     */
    showSuccess(message, containerId = "book-list") {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = `<div class="alert alert-success" role="alert">${message}</div>`;
    },

    /**
     * Replace the search button content with a spinner and disable it.
     */
    startSpinner() {
        const btn = document.getElementById("search-btn");
        originalBtnHTML = btn.innerHTML;
        if (!btn) return;
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`;
    },

    /**
     * Restore the search button content and enable it.
     */
    stopSpinner() {
        const btn = document.getElementById("search-btn");
        if (!btn) return;
        btn.disabled = false;
        btn.innerHTML = originalBtnHTML;
    },

    /**
     * Clear the contents of a specified container.
     * @param {string} containerId - The ID of the container element.
     */
    clearContainer(containerId = "book-list") {
        const container = document.getElementById(containerId);
        if (container) container.innerHTML = "";
    },

    /**
     * Render a list of books in the specified container, processing in chunks for performance.
     * @param {Array} books - Array of book objects to render.
     * @param {string} containerId - The ID of the container element.
     */
    renderBookList(books, containerId = "book-list") {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Show error if no books found
        if (!books || books.length === 0) {
            this.showError("Aucun livre trouvé.", containerId);
            return;
        }

        /**
         * Process books in chunks to avoid blocking the interface.
         * @param {object} handle - Reference to domService for method calls.
         */
        // Ensure the container is visible before scrolling
        container.style.left = "0";
        container.scrollTop = 0;


        let index = 0;
        function processChunk(handle) {
            const chunkSize = 10; // Number of items to process per chunk
            const fragment = document.createDocumentFragment(); // Use a fragment for better performance

            // Process a chunk of books
            for (let i = 0; i < chunkSize && index < books.length; i++, index++) {
                const book = books[index];
                if (!book) continue; // Skip if book is undefined
                const item = handle.createBookListItem(book);
                fragment.appendChild(item);
            }

            container.appendChild(fragment);

            if (index < books.length) {
                // Schedule the next chunk
                setTimeout(() => processChunk(handle), 0);
            } 
        }

        // Start processing the first chunk
        processChunk(this);
    },

    /**
     * Create a DOM element representing a single book item.
     * @param {object} book - The book object to render.
     * @returns {HTMLElement} - The DOM element for the book.
     */
    createBookListItem(book) {
        const item = document.createElement("div");
        item.className = "book-list-item";
        item.style.display = "flex";
        item.style.gap = "20px";
        item.style.alignItems = "flex-start";
        item.style.border = "1px solid #ddd";
        item.style.padding = "10px";
        item.style.marginBottom = "10px";
        item.style.borderRadius = "8px";
        item.style.backgroundColor = "#f9f9f9";
        item.style.boxShadow = "0 2px 4px rgba(0,0,0,0.1)";

        // Left column for title, cover, author, and description
        const leftCol = document.createElement("div");
        leftCol.style.flex = "1";

        // Book title
        const title = document.createElement("h3");
        title.textContent = book.titre || book.label || "Titre inconnu";
        leftCol.appendChild(title);

        // Book cover image if available
        if (book.couverture && book.couverture.startsWith("http")) {
            const img = document.createElement("img");
            img.src = book.couverture;
            img.alt = "Couverture";
            img.style.maxWidth = "100px";
            img.style.display = "block";
            img.style.padding = "5px";
            leftCol.appendChild(img);
        }
        //Otherwise use a book placeholder with title and author
        else {  
            const placeholder = this.createBookPlaceholder(book);
            leftCol.appendChild(placeholder);
        }


        // Author if available
        if (book.auteur) {
            const author = document.createElement("p");
            author.innerHTML = `<strong>Auteur :</strong> ${book.auteur}`;
            leftCol.appendChild(author);
        }

        // Description if available
        if (book.description) {
            const description = document.createElement("p");
            description.innerHTML = `<strong>Description :</strong> ${book.description}`;
            leftCol.appendChild(description);
        }

        item.appendChild(leftCol);

        // Right column for additional fields
        const rightCol = document.createElement("div");
        rightCol.style.flex = "2";

        // List of fields to display in the right column
        const fields = [
            { key: "categorie", label: "Catégorie" },
            { key: "resume", label: "Résumé" },
            { key: "editeur", label: "Éditeur" },
            { key: "parution", label: "Parution" },
            { key: "pages", label: "Pages" },
            { key: "langue", label: "Langue" },
            { key: "lien", label: "Lien" }
        ];

        // Render each field if available
        fields.forEach(field => {
            if (book[field.key]) {
                const p = document.createElement("p");
                if (field.key === "lien") {
                    // Special handling for link field
                    const link = document.createElement("a");
                    link.href = book[field.key];
                    link.textContent = "Voir sur pretnumerique.ca";
                    link.target = "_blank";
                    link.className = "btn btn-primary";
                    rightCol.appendChild(link);
                } else {
                    p.innerHTML = `<strong>${field.label} :</strong> ${book[field.key]}`;
                    rightCol.appendChild(p);
                }
            }
        });

        item.appendChild(rightCol);

        return item;
    },

    /**
     * Create a book placeholder element with title and author name.
     * @param {object} book - The book object.
     * @returns {HTMLElement} - The placeholder element.
     */
    createBookPlaceholder(book) {
        // Calculate height based on content
        const hasAuthor = book.auteur && book.auteur.trim() !== "";
        const baseHeight = 100; // Base height for icon and title
        const authorHeight = hasAuthor ? 25 : 0; // Additional height for author
        const totalHeight = baseHeight + authorHeight + 20; // Add some padding
        
        const placeholder = document.createElement("div");
        placeholder.style.width = "100px";
        placeholder.style.height = `${totalHeight}px`;
        placeholder.style.backgroundColor = "#f5f5f5";
        placeholder.style.border = "2px solid #ddd";
        placeholder.style.borderRadius = "4px";
        placeholder.style.display = "flex";
        placeholder.style.flexDirection = "column";
        placeholder.style.justifyContent = "center";
        placeholder.style.alignItems = "center";
        placeholder.style.padding = "8px";
        placeholder.style.margin = "5px";
        placeholder.style.textAlign = "center";
        placeholder.style.fontSize = "10px";
        placeholder.style.color = "#666";
        placeholder.style.fontFamily = "Arial, sans-serif";
        placeholder.style.lineHeight = "1.2";
        placeholder.style.wordWrap = "break-word";
        placeholder.style.overflow = "hidden";

        // Book icon (simple representation)
        const bookIcon = document.createElement("div");
        bookIcon.style.width = "30px";
        bookIcon.style.height = "40px";
        bookIcon.style.backgroundColor = "#e0e0e0";
        bookIcon.style.border = "1px solid #ccc";
        bookIcon.style.borderRadius = "2px";
        bookIcon.style.marginBottom = "8px";
        bookIcon.style.position = "relative";
        
        // Add a simple spine line to the book icon
        const spine = document.createElement("div");
        spine.style.position = "absolute";
        spine.style.left = "3px";
        spine.style.top = "5px";
        spine.style.bottom = "5px";
        spine.style.width = "1px";
        spine.style.backgroundColor = "#bbb";
        bookIcon.appendChild(spine);
        
        placeholder.appendChild(bookIcon);

        // Title (truncated if too long)
        const title = book.titre || book.label || "Titre inconnu";
        const titleDiv = document.createElement("div");
        titleDiv.style.fontWeight = "bold";
        titleDiv.style.marginBottom = "4px";
        titleDiv.style.maxHeight = "45px";
        titleDiv.style.overflow = "hidden";
        titleDiv.textContent = title.length > 25 ? title.substring(0, 25) + "..." : title;
        placeholder.appendChild(titleDiv);

        // Author (truncated if too long)
        if (hasAuthor) {
            const authorDiv = document.createElement("div");
            authorDiv.style.fontSize = "9px";
            authorDiv.style.fontStyle = "italic";
            authorDiv.style.maxHeight = "20px";
            authorDiv.style.overflow = "hidden";
            const author = book.auteur;
            authorDiv.textContent = author.length > 20 ? author.substring(0, 20) + "..." : author;
            placeholder.appendChild(authorDiv);
        }

        return placeholder;
    }
};
