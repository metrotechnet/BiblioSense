# BiblioSense

A Flask-based intelligent book recommendation system that uses OpenAI GPT for smart categorization and filtering of French-language books from multiple digital library sources.

## Features

- **AI-powered book categorization** using OpenAI GPT-4o-mini
- **Multi-source data integration** from OpenLibrary and Prêt numérique
- **Interactive web interface** with dynamic book placeholders and covers
- **Advanced filtering and search** with keyword prioritization
- **Performance monitoring** with request timing metrics
- **Data deduplication** with intelligent duplicate detection
- **Progressive data saving** for reliable large-scale data collection
- **RESTful API** for book data and filtering
- **Google Cloud integration** with Secret Manager for secure API key management

## Local Development

### Prerequisites

- Python 3.11+
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/metrotechnet/BiblioSense.git
cd BiblioSense
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:

**Option A: Environment Variable (for local development)**
```bash
# Create a .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

**Option B: Google Secret Manager (for production)**
```bash
# Store in Google Secret Manager
gcloud secrets create openai-api-key --data-file=- <<< "your_openai_api_key_here"
```

5. Initialize the data (optional - populate with sample data):
```bash
# Run data collection scripts if needed
python utils/fetchOpenLibrary.py  # For OpenLibrary books
python utils/fetchPretnumerique.py  # For Prêt numérique books
python pretnumerique/fusionner_json.py  # Merge and deduplicate JSON files
```

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:8080`

## Google Cloud Run Deployment

### Prerequisites

- Google Cloud CLI installed and authenticated
- Docker installed (for local testing)
- Google Cloud project with billing enabled
- Container Registry API enabled

### Quick Deployment

1. Update the project ID in `deploy-gcp.ps1` (Windows) or `deploy-gcp.sh` (Linux/Mac)

2. Set your OpenAI API key as an environment variable:
```powershell
# Windows PowerShell
$env:OPENAI_API_KEY = "your_openai_api_key_here"
```

```bash
# Linux/Mac
export OPENAI_API_KEY="your_openai_api_key_here"
```

3. Run the deployment script:
```powershell
# Windows
.\deploy-gcp.ps1
```

```bash
# Linux/Mac
chmod +x deploy-gcp.sh
./deploy-gcp.sh
```

### Manual Deployment Steps

1. Build and push the container:
```bash
# Set your project ID
export PROJECT_ID=your-gcp-project-id

# Build the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/bibliosense

# Deploy to Cloud Run
gcloud run deploy bibliosense \
  --image gcr.io/$PROJECT_ID/bibliosense \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

### CI/CD with Cloud Build

For automated deployments, you can use the included `cloudbuild.yaml`:

```bash
gcloud builds submit --config cloudbuild.yaml
```

## API Endpoints

- `GET /` - Main web interface with logo and enhanced UI
- `GET /books` - Get all books data
- `POST /filter` - Filter books using AI categorization with performance metrics

### Filter API Usage

```bash
curl -X POST https://your-service-url/filter \
  -H "Content-Type: application/json" \
  -d '{"query": "livres de science-fiction en français"}'
```

### Response Format

```json
{
  "books": [...],
  "timing": {
    "total_time": 1.234,
    "gpt_time": 0.856,
    "filter_time": 0.378
  },
  "performance": {
    "books_processed": 1500,
    "matches_found": 42
  }
}
```

## Project Structure

```
BiblioSense/
├── app.py                      # Main Flask application with factory pattern
├── gpt_services.py            # GPT services and Google Secret Manager integration
├── requirements.txt           # Python dependencies
├── Dockerfile                # Container configuration for Cloud Run
├── .dockerignore             # Docker ignore rules
├── cloudbuild.yaml           # Cloud Build configuration
├── dbase/                    # Database and data files
│   ├── book_dbase.json       # Main book database
│   ├── classification_books.json  # Book classifications
│   ├── livres_pretnumerique.json  # Prêt numérique books
│   └── prenumerique_complet.json  # Merged and deduplicated data
├── pretnumerique/            # Prêt numérique data collection
│   ├── fusionner_json.py     # JSON merger with deduplication
│   ├── Biographie_romancée.json
│   ├── fantasy.json
│   ├── Science_fiction.json
│   └── ... (20 category files)
├── static/                   # Static web assets
│   ├── css/
│   │   └── bibliosense.css   # Custom styles
│   ├── js/
│   │   ├── bibliosense.js    # Main application logic
│   │   ├── dataService.js    # API communication
│   │   └── domService.js     # DOM manipulation with book placeholders
│   └── images/
│       ├── BiblioSense_logo.png  # Application logo
│       └── placeholder.png   # Book cover placeholder
├── templates/
│   └── index.html            # Main HTML template with logo
└── utils/                    # Utility scripts
    ├── classifyBooks.py      # Book classification utilities
    ├── crawler.py           # Data crawling utilities
    ├── fetchOpenLibrary.py  # OpenLibrary data fetcher with progressive saving
    ├── fetchPretnumerique.py # Prêt numérique scraper
    └── requirements.txt     # Utility-specific dependencies
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required. Your OpenAI API key (stored in Google Secret Manager for production)
- `PORT` - Optional. Port to run the application (default: 8080)
- `GOOGLE_CLOUD_PROJECT` - Optional. Google Cloud project ID for Secret Manager

### Cloud Run Settings

- Memory: 1GB
- CPU: 1 vCPU
- Timeout: 300 seconds
- Max instances: 10
- Secret Manager integration for secure API key storage

### Data Sources

- **OpenLibrary API**: French-language books with progressive saving
- **Prêt numérique**: 20+ fiction categories with automated scraping
- **Smart deduplication**: Removes duplicates while preserving best data quality

## Data Collection Scripts

### OpenLibrary Fetcher (`utils/fetchOpenLibrary.py`)
- Fetches French books from OpenLibrary API
- Progressive saving to prevent data loss
- Robust error handling and retry logic
- Resume capability for interrupted processes

### Prêt numérique Scraper (`utils/fetchPretnumerique.py`)
- Automated scraping of 20 fiction categories
- Selenium-based web scraping with Chrome WebDriver
- Cookie consent handling and pagination
- Comprehensive book metadata extraction

### JSON Merger (`pretnumerique/fusionner_json.py`)
- Merges all category JSON files into one
- Intelligent duplicate detection and removal
- Detailed statistics and reporting
- Data quality validation and cleaning

## Performance Optimizations

- **Flask Factory Pattern**: Modular application structure
- **Algorithmic Improvements**: Single-pass filtering with keyword prioritization
- **Performance Monitoring**: Request timing and GPT call metrics
- **Chunked DOM Rendering**: Non-blocking UI updates for large book lists
- **Smart Book Placeholders**: Dynamic placeholders with title and author when covers unavailable
- **Caching**: Efficient data loading and processing

## Technical Highlights

- **Google Cloud Integration**: Secret Manager, Cloud Run deployment
- **OpenAI GPT-3.5-turbo**: Advanced book categorization and filtering
- **Multi-source Data**: OpenLibrary + Prêt numérique integration
- **Progressive Data Collection**: Reliable large-scale data acquisition
- **Intelligent Deduplication**: Quality-preserving duplicate removal
- **Modern Frontend**: Bootstrap 5, responsive design with logo integration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test locally with `python app.py`
5. Run data collection scripts if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenLibrary API for book metadata
- Prêt numérique Quebec for French-language digital books
- OpenAI for GPT-based categorization
- Google Cloud Platform for hosting and secret management