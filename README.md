# # BiblioSense

A Flask-based intelligent book recommendation system that uses OpenAI GPT for smart categorization and filtering.

## Features

- AI-powered book categorization using OpenAI GPT
- Interactive web interface for book discovery
- Advanced filtering and search capabilities
- RESTful API for book data and filtering

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

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the application:
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

- `GET /` - Main web interface
- `GET /books` - Get all books data
- `POST /filter` - Filter books using AI categorization

### Filter API Usage

```bash
curl -X POST https://your-service-url/filter \
  -H "Content-Type: application/json" \
  -d '{"query": "science fiction books"}'
```

## Project Structure

```
BiblioSense/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .dockerignore         # Docker ignore rules
├── cloudbuild.yaml       # Cloud Build configuration
├── deploy-gcp.ps1        # Windows deployment script
├── deploy-gcp.sh         # Linux/Mac deployment script
├── dbase/               # Database files
├── static/              # Static web assets
├── templates/           # HTML templates
└── utils/               # Utility scripts
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required. Your OpenAI API key
- `PORT` - Optional. Port to run the application (default: 8080)

### Cloud Run Settings

- Memory: 1GB
- CPU: 1 vCPU
- Timeout: 300 seconds
- Max instances: 10

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is licensed under the MIT License.