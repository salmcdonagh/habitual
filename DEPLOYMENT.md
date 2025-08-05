# 🚀 Habitual - Google Cloud Deployment Guide

This guide will help you deploy the Habitual habit tracker to Google Cloud with Firebase authentication, Firestore database, and Cloud Run hosting.

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Firebase project** (can be the same as your GCP project)
4. **Docker** (for local testing)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   Cloud Run      │────│   Firestore     │
│   (Firebase     │    │   (Flask API)    │    │   (Multi-user   │
│   Auth + SDK)   │    │   + CORS         │    │   Database)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌──────────────────┐
                    │ Firebase Auth    │
                    │ (Google, Email)  │
                    └──────────────────┘
```

## 🔧 Step 1: Set Up Firebase Project

### 1.1 Create Firebase Project
```bash
# Go to https://console.firebase.google.com/
# Click "Add project"
# Use your existing GCP project or create new one
```

### 1.2 Enable Authentication
```bash
# In Firebase Console:
# Authentication > Sign-in method
# Enable "Google" provider
# Enable "Email/Password" provider (optional)
```

### 1.3 Create Firestore Database
```bash
# In Firebase Console:
# Firestore Database > Create database
# Choose "Start in production mode"
# Select region (same as your Cloud Run region)
```

### 1.4 Get Firebase Configuration
```bash
# Project Settings > General > Your apps
# Add web app, copy the config object
```

## 🔑 Step 2: Configure Firebase

### 2.1 Update Firebase Config
Edit `static/js/app.js` and replace the firebaseConfig object:

```javascript
const firebaseConfig = {
    apiKey: "your-actual-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "123456789",
    appId: "your-app-id"
};
```

### 2.2 Set Up Service Account
```bash
# Create service account for backend
gcloud iam service-accounts create habitual-backend \
    --display-name="Habitual Backend Service"

# Grant Firestore access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:habitual-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# For local development, create and download key
gcloud iam service-accounts keys create habitual-key.json \
    --iam-account=habitual-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable for local development
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/habitual-key.json"
```

### 2.3 Deploy Firestore Security Rules
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and init
firebase login
firebase init firestore

# Deploy rules
firebase deploy --only firestore:rules
```

## 🚀 Step 3: Deploy to Cloud Run

### 3.1 Quick Deploy
```bash
# Replace with your project ID
./deploy.sh your-project-id us-central1
```

### 3.2 Manual Deploy Steps
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com

# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/habitual-api
gcloud run deploy habitual-api \
    --image gcr.io/YOUR_PROJECT_ID/habitual-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --max-instances 10
```

## 🔧 Step 4: Configure CORS and Domain

### 4.1 Update CORS Origins
Edit `app/__init__.py` and update the CORS configuration:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5001", 
            "https://your-service-url.run.app"  # Add your actual Cloud Run URL
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 4.2 Update Firebase Auth Domain
In Firebase Console:
- Authentication > Settings > Authorized domains
- Add your Cloud Run domain

## 🧪 Step 5: Test the Deployment

### 5.1 Health Check
```bash
curl https://your-service-url.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "habitual-api", 
  "version": "1.0.0"
}
```

### 5.2 Test Authentication Flow
1. Visit your Cloud Run URL
2. Click "Sign In" 
3. Complete Google OAuth flow
4. Verify habit data syncs between devices

### 5.3 Test API Endpoints
```bash
# Get auth token from browser dev tools after signing in
TOKEN="your-firebase-id-token"

# Test authenticated endpoints
curl -H "Authorization: Bearer $TOKEN" \
     https://your-service-url.run.app/api/profile

curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"habitData":{"counter":5}}' \
     https://your-service-url.run.app/api/sync
```

## 💳 Step 6: Add Stripe Integration (Optional)

### 6.1 Set Up Stripe
```bash
# Get Stripe keys from https://dashboard.stripe.com/
# Add environment variables to Cloud Run
gcloud run services update habitual-api \
    --region=us-central1 \
    --set-env-vars="STRIPE_PUBLISHABLE_KEY=pk_test_...,STRIPE_SECRET_KEY=sk_test_..."
```

### 6.2 Create Payment Controller
Add to `app/controllers/payment_controller.py`:

```python
import stripe
from flask import Blueprint, request, jsonify
from app.middleware.auth import require_auth

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/api/create-checkout-session', methods=['POST'])
@require_auth
def create_checkout_session():
    # Implementation for Stripe checkout
    pass
```

## 🔍 Monitoring and Logs

### View Logs
```bash
gcloud logs tail projects/YOUR_PROJECT_ID/logs/run.googleapis.com%2Fstderr \
    --filter="resource.labels.service_name=habitual-api"
```

### Monitor Performance
- Cloud Run metrics in GCP Console
- Firebase Authentication usage
- Firestore read/write operations

## 🔒 Security Checklist

- [ ] Firebase security rules deployed
- [ ] Service account has minimal permissions
- [ ] CORS properly configured
- [ ] Environment secrets not in code
- [ ] HTTPS enforced (automatic with Cloud Run)
- [ ] Authentication required for sensitive endpoints

## 💰 Cost Optimization

**Expected monthly costs for 1000 users:**
- Cloud Run: ~$15/month
- Firestore: ~$10/month  
- Firebase Auth: ~$2.50/month
- **Total: ~$27.50/month**

**Free tier limits:**
- Cloud Run: 2M requests, 360K GB-seconds
- Firestore: 1GB storage, 50K reads/day
- Firebase Auth: 50K MAU

## 🎯 Next Steps

1. **Custom Domain**: Set up custom domain with Cloud Run
2. **Monitoring**: Set up alerting for errors/performance
3. **Backup**: Enable Firestore automated backups
4. **CDN**: Consider Cloud CDN for static assets
5. **Mobile App**: Use same Firebase project for mobile apps

## 🆘 Troubleshooting

### Common Issues

**CORS Errors**
- Check origins in `app/__init__.py`
- Add domain to Firebase authorized domains

**Authentication Failures**
- Verify Firebase config in `app.js`
- Check service account permissions

**Firestore Permission Denied**
- Review security rules in `firestore.rules`
- Check user authentication state

**Build Failures**
- Verify Dockerfile syntax
- Check all dependencies in requirements.txt