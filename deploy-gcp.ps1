# BiblioSense Cloud Run Deployment Script for Windows PowerShell
# Make sure you have gcloud CLI installed and authenticated

# Configuration variables
$PROJECT_ID = "your-gcp-project-id"
$SERVICE_NAME = "bibliosense"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "Building and deploying BiblioSense to Google Cloud Run..." -ForegroundColor Green

# Build the container image
Write-Host "Building container image..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_NAME `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment complete!" -ForegroundColor Green
    
    # Donner les permissions pour accéder au Secret Manager
    Write-Host "Configuration des permissions Secret Manager..." -ForegroundColor Yellow
    $SERVICE_ACCOUNT = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(spec.template.spec.serviceAccountName)'
    if (-not $SERVICE_ACCOUNT) {
        $SERVICE_ACCOUNT = "$(gcloud config get-value project)-compute@developer.gserviceaccount.com"
    }
    
    gcloud projects add-iam-policy-binding $(gcloud config get-value project) `
      --member="serviceAccount:$SERVICE_ACCOUNT" `
      --role="roles/secretmanager.secretAccessor"
    
    Write-Host "Your service URL:" -ForegroundColor Cyan
    gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
} else {
    Write-Host "Deployment failed!" -ForegroundColor Red
}
