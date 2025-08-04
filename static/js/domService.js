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
        //Disable search-input
        const searchInput = document.getElementById("search-input");    
        if (searchInput) searchInput.disabled = true;
        //disable reset-btn
        const resetBtn = document.getElementById("reset-btn");
        if (resetBtn) resetBtn.disabled = true;


    },

    /**
     * Restore the search button content and enable it.
     */
    stopSpinner() {

        const btn = document.getElementById("search-btn");
        if (!btn) return;
        btn.disabled = false;
        btn.innerHTML = originalBtnHTML;
        //enable search-input
        const searchInput = document.getElementById("search-input");
        if (searchInput) searchInput.disabled = false;
        //enable reset-btn
        const resetBtn = document.getElementById("reset-btn");
        if (resetBtn) resetBtn.disabled = false;
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
     * @param {object} paginationInfo - Optional pagination information with range and total_count.
     */
    renderBookList(books, message = "",containerId = "book-list", paginationInfo = null) {
        const container = document.getElementById(containerId);
        if (!container) return;
       // Ensure the container is visible before scrolling
         document.getElementById("list-container").scrollTop = 0;

        // Show error if no books found
        if (!books || books.length === 0) {
            this.showError("Aucun livre trouvé.", containerId);
            return;
        }

        // Stop any previous rendering process
        this.stopRenderingProcess();

        /**
         * Process books in chunks to avoid blocking the interface.
         * @param {object} handle - Reference to domService for method calls.
         */
 

        // Clear container and create main content area
        container.innerHTML = "";
                // If a message is provided, display it
        if (message) {
            container.innerHTML = `<div class="alert alert-success" role="alert">${message}</div>`;
        } 
        const contentArea = document.createElement("div");
        contentArea.id = containerId + "-content";
        container.appendChild(contentArea);

        // Set rendering flag to true
        this._isRendering = true;
        this._renderingTimeoutId = null;

        let index = 0;
        const processChunk = (handle) => {
            // Check if rendering should be stopped
            if (!handle._isRendering) {
                console.log("Rendering process interrupted");
                return;
            }

            const chunkSize = 10; // Number of items to process per chunk
            const fragment = document.createDocumentFragment(); // Use a fragment for better performance

            // Process a chunk of books
            for (let i = 0; i < chunkSize && index < books.length; i++, index++) {
                // Check again if rendering should be stopped (in case of interruption during processing)
                if (!handle._isRendering) {
                    console.log("Rendering process interrupted during chunk processing");
                    return;
                }
                
                const book = books[index];
                if (!book) continue; // Skip if book is undefined
                const item = handle.createBookListItem(book);
                fragment.appendChild(item);
            }

            contentArea.appendChild(fragment);

            if (index < books.length && handle._isRendering) {
                console.log("Rendering chunk " + Math.ceil(100 * index / books.length)+ "% complete");
                // Schedule the next chunk
                handle._renderingTimeoutId = setTimeout(() => processChunk(handle), 100);
            } else {
                // Rendering complete or stopped
                handle._isRendering = false;
                handle._renderingTimeoutId = null;
                if (index >= books.length) {
                    console.log("Rendering process completed");
                    // Add pagination after rendering is complete
                    if (paginationInfo) {
                        handle.addPagination(container, paginationInfo);
                    }
                }
            }
        };

        // Start processing the first chunk
        processChunk(this);
    },

    /**
     * Stop the current rendering process.
     */
    stopRenderingProcess() {
        if (this._isRendering) {
            this._isRendering = false;
            if (this._renderingTimeoutId) {
                clearTimeout(this._renderingTimeoutId);
                this._renderingTimeoutId = null;
            }
            console.log("Rendering process stopped externally");
        }
    },

    /**
     * Add pagination controls to the container.
     * @param {HTMLElement} container - The container element.
     * @param {object} paginationInfo - Pagination information with range, total_count, and source.
     */
    addPagination(container, paginationInfo) {
        const { range, total_count, source = 'all' } = paginationInfo;
        
        if (!range || !total_count ) return;

        const { start, end, count } = range;
       
        const itemsPerPage = count;
        const currentPage = Math.floor(start / itemsPerPage) + 1;
        const totalPages = Math.ceil(total_count / itemsPerPage);

        // Create pagination container
        const paginationContainer = document.createElement("div");
        paginationContainer.className = "pagination-container";
        paginationContainer.style.marginTop = "20px";
        paginationContainer.style.textAlign = "center";
        paginationContainer.style.padding = "20px";
        paginationContainer.style.borderTop = "1px solid #ddd";

        // Create pagination info
        const paginationInfo_div = document.createElement("div");
        paginationInfo_div.className = "pagination-info";
        paginationInfo_div.style.marginBottom = "15px";
        paginationInfo_div.style.color = "#666";
        paginationInfo_div.innerHTML = `
            Affichage des livres ${start + 1} à ${Math.min(end + 1, total_count)} sur ${total_count} 
            (Page ${currentPage} sur ${totalPages})
        `;

        // Create pagination controls
        const paginationControls = document.createElement("nav");
        paginationControls.setAttribute("aria-label", "Navigation des pages");
        
        const paginationList = document.createElement("ul");
        paginationList.className = "pagination justify-content-center";
        paginationList.style.marginBottom = "0";

        // Previous button
        if (currentPage > 1) {
            const prevItem = this.createPaginationItem("Précédent", currentPage - 1, itemsPerPage, source, false);
            paginationList.appendChild(prevItem);
        }

        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        // First page if not in range
        if (startPage > 1) {
            paginationList.appendChild(this.createPaginationItem("1", 1, itemsPerPage, source, false));
            if (startPage > 2) {
                const ellipsis = document.createElement("li");
                ellipsis.className = "page-item disabled";
                ellipsis.innerHTML = '<span class="page-link">...</span>';
                paginationList.appendChild(ellipsis);
            }
        }

        // Page range
        for (let page = startPage; page <= endPage; page++) {
            const isActive = page === currentPage;
            paginationList.appendChild(this.createPaginationItem(page.toString(), page, itemsPerPage, source, isActive));
        }

        // Last page if not in range
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsis = document.createElement("li");
                ellipsis.className = "page-item disabled";
                ellipsis.innerHTML = '<span class="page-link">...</span>';
                paginationList.appendChild(ellipsis);
            }
            paginationList.appendChild(this.createPaginationItem(totalPages.toString(), totalPages, itemsPerPage, source, false));
        }

        // Next button
        if (currentPage < totalPages) {
            const nextItem = this.createPaginationItem("Suivant", currentPage + 1, itemsPerPage, source, false);
            paginationList.appendChild(nextItem);
        }

        paginationControls.appendChild(paginationList);
        paginationContainer.appendChild(paginationInfo_div);
        paginationContainer.appendChild(paginationControls);
        container.appendChild(paginationContainer);
    },

    /**
     * Create a pagination item (button).
     * @param {string} text - The text to display on the button.
     * @param {number} page - The page number.
     * @param {number} itemsPerPage - Number of items per page.
     * @param {string} source - Data source ('all' or 'filtered').
     * @param {boolean} isActive - Whether this is the current page.
     * @returns {HTMLElement} - The pagination item element.
     */
    createPaginationItem(text, page, itemsPerPage, source, isActive) {
        const listItem = document.createElement("li");
        listItem.className = `page-item ${isActive ? 'active' : ''}`;

        const link = document.createElement("a");
        link.className = "page-link";
        link.href = "#";
        link.textContent = text;
        link.style.cursor = "pointer";

        if (!isActive) {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                this.loadPage(page, itemsPerPage, source);
            });
        }

        listItem.appendChild(link);
        return listItem;
    },

    /**
     * Load a specific page of books.
     * @param {number} page - The page number to load.
     * @param {number} itemsPerPage - Number of items per page.
     * @param {string} source - Data source ('all' or 'filtered').
     */
    loadPage(page, itemsPerPage, source) {
        const start = (page - 1) * itemsPerPage;
        const end = start + itemsPerPage - 1;
        
        console.log(`Loading page ${page}: items ${start}-${end} from ${source}`);
        
        // Show loading spinner
        this.startSpinner();
        
        // Construct URL with source parameter
        const url = `/books/${start}/${end}?source=${source}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.stopSpinner();
                if (data.error) {
                    this.showError(data.error);
                } else {
                    const paginationInfo = {
                        range: data.range,
                        total_count: data.total_count,
                        source: data.source
                    };
                    this.renderBookList(data.book_list,"","book-list", paginationInfo);
                }
            })
            .catch(error => {
                this.stopSpinner();
                console.error('Error loading page:', error);
                this.showError("Erreur lors du chargement de la page.");
            });
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
        if (book.couverture ) {
            // Create image on load only if the cover URL is valid
            const img = document.createElement("img");
            img.src = book.couverture;
            img.alt = "Couverture";
            img.style.maxWidth = "100px";
            img.style.display = "none"; // Hide initially until loaded
            // Handle image loading
            img.onload = () => {
                img.style.display = "block";
                img.style.maxHeight = "150px"; // Set a max height for the image
            }
            // Handle image loading error - fallback to placeholder
            img.onerror = () => {
                img.style.display = "none";
                const placeholder = this.createBookPlaceholder(book);
                leftCol.appendChild(placeholder);
            };
            
            leftCol.appendChild(img);
        }
        else {
            // If no cover image, create a placeholder
            const placeholder = this.createBookPlaceholder(book);
            leftCol.appendChild(placeholder);
        }
        setTimeout(() => {
             // Author if available (placed after cover/placeholder)
            if (book.auteur) {
                const author = document.createElement("p");
                author.innerHTML = `<strong>Auteur :</strong> ${book.auteur}`;
                leftCol.appendChild(author);
            }

            // Description if available (placed after author)
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

        }, 100);

 

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
