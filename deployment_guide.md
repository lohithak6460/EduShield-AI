# 🚀 EduShield AI Production Deployment Guide

This guide describes how to deploy the EduShield AI platform (Streamlit dashboard and FastMCP server) in a production-ready cloud environment, specifically using **Docker** and **Google Cloud Run**.

---

## 🏗️ Architecture Overview

In production, the platform is hosted as a containerized web application. The Streamlit dashboard and the MCP database server run within the same container, or communicate securely across services using Cloud Run.

```
                  ┌──────────────────────────────────────────────┐
                  │              Google Cloud Run                │
                  │  ┌──────────────────┐  ┌──────────────────┐  │
◀── HTTPS (TLS) ──┼──┤  Streamlit Web   ├──┤  FastMCP Server  │  │
   (Port 8080)    │  │    Dashboard     │  │  (Stdio/SSE RPC) │  │
                  │  └────────┬─────────┘  └────────┬─────────┘  │
                  └───────────┼─────────────────────┼────────────┘
                              ▼                     ▼
                     ┌──────────────────┐  ┌──────────────────┐
                     │ Secret Manager   │  │   Cloud SQL /    │
                     │ (GEMINI_API_KEY) │  │  Firestore DB    │
                     └──────────────────┘  └──────────────────┘
```

---

## 🐳 Docker Deployment

### 1. Create a `Dockerfile`
Create a `Dockerfile` in the root of the project directory to build the deployment container:

```dockerfile
# Use a lightweight python base image
FROM python:3.11-slim

# Install system dependencies (including graphviz for diagrams)
RUN apt-get update && apt-get install -y \
    build-essential \
    graphviz \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Expose standard Streamlit port
EXPOSE 8080

# Configure Streamlit environment variables
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV PYTHONUTF8=1

# Command to run Streamlit
CMD ["streamlit", "run", "app.py"]
```

### 2. Build and Test Locally
Build the Docker image locally:
```bash
docker build -t edushield-ai:latest .
```

Run the container locally:
```bash
docker run -p 8080:8080 -e GEMINI_API_KEY="your_api_key_here" edushield-ai:latest
```

---

## ☁️ Deploying to Google Cloud Run

Google Cloud Run is the recommended hosting platform as it provides serverless scaling, TLS certificates out-of-the-box, and secure API key injection via Secret Manager.

### Step 1: Enable Google Cloud Services
Verify you have the Google Cloud SDK installed and run:
```bash
# Set your active GCP Project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com containerregistry.googleapis.com secretmanager.googleapis.com
```

### Step 2: Store the Gemini API Key securely
Create a secret to store your Gemini API key:
```bash
gcloud secrets create GEMINI_API_KEY --replication-policy="automatic"
echo -n "YOUR_ACTUAL_GEMINI_KEY" | gcloud secrets versions add GEMINI_API_KEY --data-file=-
```

### Step 3: Build and Push Image to Container Registry
Build the container using Google Cloud Build and push it to GCR:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/edushield-ai:latest
```

### Step 4: Deploy Container to Cloud Run
Deploy the container, linking the Secret Manager API Key:
```bash
gcloud run deploy edushield-ai \
    --image gcr.io/YOUR_PROJECT_ID/edushield-ai:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest
```

Once the deployment completes, gcloud will output the service URL (e.g., `https://edushield-ai-xxxxxx.a.run.app`) where your production dashboard is live!

---

## 📈 Scalability and Performance

To scale the platform for thousands of students:
1. **Model Cache:** Enable `context_cache_config` on the Google ADK runner to prevent re-reading identical long instructions on consecutive runs.
2. **Concurrent Sessions:** Replace `InMemorySessionService` with the `adk-redis` or `DatabaseSessionService` backed by MongoDB or Cloud Firestore to store student sessions persistently across multiple container instances.
3. **CPU Allocation:** In Cloud Run, allocate at least `2 vCPU` and `4GiB Memory` to handle data operations, Streamlit frontend processes, and concurrent agent execution loops.
