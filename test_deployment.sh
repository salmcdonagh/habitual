#!/bin/bash

# Test deployment script
SERVICE_URL="https://habitual-api-rgv222zqha-uc.a.run.app"

echo "🧪 Testing Cloud Run deployment..."
echo "Service URL: $SERVICE_URL"
echo ""

# Test 1: Health check
echo "1️⃣ Testing health check..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" $SERVICE_URL/health)
HTTP_CODE="${HEALTH_RESPONSE: -3}"
RESPONSE_BODY="${HEALTH_RESPONSE%???}"

echo "HTTP Status: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    echo ""
    echo "🔍 Debugging info:"
    echo "Checking Cloud Run service status..."
    gcloud run services describe habitual-api --region=us-central1 --format="value(status.conditions[].message)"
fi

echo ""

# Test 2: Main page
echo "2️⃣ Testing main page..."
MAIN_RESPONSE=$(curl -s -w "%{http_code}" $SERVICE_URL/)
HTTP_CODE="${MAIN_RESPONSE: -3}"

echo "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Main page accessible!"
else
    echo "❌ Main page failed!"
fi

echo ""

# Test 3: Check logs
echo "3️⃣ Recent logs:"
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=habitual-api" \
    --limit=5 --format="table(timestamp,severity,textPayload)" 2>/dev/null || \
    echo "Run 'gcloud logs read ...' manually to see detailed logs"