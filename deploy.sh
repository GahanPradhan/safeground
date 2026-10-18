#!/usr/bin/env bash
# Deploy SafeGround to Cloud Run (source deploy via Cloud Build).
# Uses the owner's SafeGround gcloud login; the Gemini key comes from Secret Manager, never from local files.
set -euo pipefail
export CLOUDSDK_CONFIG="${CLOUDSDK_CONFIG:-$HOME/.config/gcloud-cityguard}"
G="${GCLOUD:-$HOME/google-cloud-sdk/bin/gcloud}"
PROJECT="${PROJECT:-gen-lang-client-0657024026}"
REGION="${REGION:-asia-south1}"

# The runtime service account keeps the product's first name (service accounts cannot be renamed).
"$G" run deploy safeground \
  --project "$PROJECT" --region "$REGION" --source . \
  --service-account "cityguard-run@${PROJECT}.iam.gserviceaccount.com" \
  --set-secrets "GOOGLE_API_KEY=gemini-api-key:latest" \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=FALSE,SAFEGROUND_MODEL=gemini-3.5-flash,SAFEGROUND_LLM_MODE=cached,SAFEGROUND_NEWS_SEARCH=1,SAFEGROUND_LIVE_CALLS_PER_HOUR=60,GOOGLE_CLOUD_PROJECT=${PROJECT}" \
  --memory 2Gi --cpu 1 --min-instances 0 --max-instances 1 --concurrency 40 --timeout 300 \
  --allow-unauthenticated --quiet
