#!/bin/bash
set -e

echo "========================================================"
echo "Deploying PulseCare Clinic System to Google Cloud Run..."
echo "========================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "[ERROR] Google Cloud SDK (gcloud) is not found in PATH."
    echo "Please install gcloud: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

REGION="us-central1"
SERVICE_NAME="pulsecare"

echo "Deploying source to Cloud Run service '$SERVICE_NAME' in region '$REGION'..."
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080

echo "========================================================"
echo "[SUCCESS] Deployment completed successfully!"
echo "========================================================"
