#!/bin/bash

# BiblioSense Cloud Run Deployment Script
# Make sure you have gcloud CLI installed and authenticated

# Configuration variables
PROJECT_ID="your-gcp-project-id"
SERVICE_NAME="bibliosense"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Building and deploying BiblioSense to Google Cloud Run..."

# Build the container image
echo "Building container image..."
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10

echo "Deployment complete!"
echo "Your service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
