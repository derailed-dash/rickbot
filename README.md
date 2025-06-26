# Rickbot

## Repo Metadata

Author: Darren Lester

## Repo Overview

_Rickbot_ is a chatbot that behaves like Rick Sanchez from Rick and Morty.

It has been created using Google Gemini, and is grounded with Google Search. The application demo is deployed to Google Cloud Run.

See the companion article [here](https://medium.com/google-cloud/creating-a-rick-morty-chatbot-with-google-cloud-and-the-gen-ai-sdk-e8108e83dbee).

## Repo Structure

```text
project/
├── deploy/
|   └── cloudbuild.yaml     # Cloud Build config 
|
├── src/
|   └── rickbot/
|       |   ├── .streamlit/        # For Streamlit configuration
|       |   ├── media/             # E.g. avatar images - names in lower case
|       |   ├── pages/             # Pages - e.g. privacy policy
|       |   └── system_prompts/    # names in lower case
|       |
|       ├── app.py
|       ├── agent.py
|       ├── config.py
|       ├── create_auth_secrets.py # Dynamicly create secrets.toml
|       ├── personality.py         # Definition of personalities
|       ├── requirements.txt    
|       ├── .dockerignore          # Exclude files from container image
|       └── Dockerfile
|
├── .env
├── .gitattributes
├── .gitignore
└── README.md            # Project guidance
```

## Deployment Guidance

### Per-Environment Setup

```bash
# Setup Python environment and install dependencies
uv venv .venv
uv sync
```

### Every Session

For local dev, run the following from your project's root folder:

```bash
# Authenticate yourself to gcloud
# And also setup ADC so any locally running application can access Google APIs
# Note that credentials will be saved to 
# ~/.config/gcloud/application_default_credentials.json
gcloud auth login --update-adc 

# Set these manually...
export GOOGLE_CLOUD_PROJECT="<Your Google Cloud Project ID>"
export GOOGLE_CLOUD_REGION="<your region>"
export MY_ORG="<enter your org domain>"
export DOMAIN_NAME="<enter application domain name>"
# Etc

# Or load from .env, or .env.dev, or whatever
source .env

export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")

# Make sure we're on the right project...
gcloud config set project $GOOGLE_CLOUD_PROJECT
gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT
gcloud config list project

# Once your venv has been created
source .venv/bin/activate
```

### One-Time Google Cloud Setup

```bash
# Enable APIs
gcloud services enable \
  serviceusage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  logging.googleapis.com \
  storage-component.googleapis.com \
  aiplatform.googleapis.com \
  iap.googleapis.com

# Create the rickbot service account
gcloud iam service-accounts create $RICKBOT_SA

# To allow the SA to run Cloud run services
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:$RICKBOT_SA_EMAIL" \
  --role="roles/run.admin"

# To provide access to Gemini AI services
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:$RICKBOT_SA_EMAIL" \
  --role="roles/aiplatform.user"

# To provide access to Google Secret Manager
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:$RICKBOT_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

# Allow Compute Engine default service account to build with Cloud Build
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
    --role="roles/cloudbuild.builds.builder"

# Grant the required role to the principal
# that will attach the service account to other resources.
# Here we assume your developer account is a member of the gcp-devops group.
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="group:gcp-devops@$MY_ORG" \
  --role="roles/iam.serviceAccountUser"

# Allow service account impersonation
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="group:gcp-devops@$MY_ORG" \
  --role=roles/iam.serviceAccountTokenCreator

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
   --member="group:gcp-devops@$MY_ORG" \
   --role roles/run.admin  

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="group:gcp-devops@$MY_ORG" \
  --role="roles/iap.admin"
```

### Running and Testing the Application Locally

#### Running Streamlit App

```bash
# Local streamlit app
# Run from your project/src/rickbot directory
uv run -- streamlit run app.py --browser.serverAddress=localhost
```

#### Running in a Local Container

```bash
# Get a unique version to tag our image
export VERSION=$(git rev-parse --short HEAD)

# To build as a container image
docker build -t $SERVICE_NAME:$VERSION .

# To run as a local container
# We need to pass environment variables to the container
# and the Google Application Default Credentials (ADC)
docker run --rm -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT -e GOOGLE_CLOUD_REGION=$GOOGLE_CLOUD_REGION \
  -e LOG_LEVEL=$LOG_LEVEL \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/.config/gcloud/application_default_credentials.json" \
  --mount type=bind,source=${HOME}/.config/gcloud,target=/app/.config/gcloud \
   $SERVICE_NAME:$VERSION
```

### Running in Google Cloud

#### Build and Push to Google Artifact Registry:

```bash
# One time setup - create a GAR repo
gcloud artifacts repositories create "$REPO" \
  --location="$GOOGLE_CLOUD_REGION" --repository-format=Docker

# Allow authentication to the repo
gcloud auth configure-docker "$GOOGLE_CLOUD_REGION-docker.pkg.dev"

# Every time we want to build a new version and push to GAR
# This will take a couple of minutes
export VERSION=$(git rev-parse --short HEAD)
gcloud builds submit \
  --tag "$GOOGLE_CLOUD_REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$REPO/$SERVICE_NAME:$VERSION"
```

#### Deploy to Cloud Run

Public service with no authentication:

```bash
# Deploy to Cloud Run - this takes a couple of minutes
# Set max-instances to 1 to minimise cost
gcloud run deploy "$SERVICE_NAME" \
  --port=8080 \
  --image="$GOOGLE_CLOUD_REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$REPO/$SERVICE_NAME:$VERSION" \
  --service-account=$RICKBOT_SA_EMAIL \
  --max-instances=1 \
  --allow-unauthenticated \
  --region=$GOOGLE_CLOUD_REGION \
  --platform=managed  \
  --project=$GOOGLE_CLOUD_PROJECT \
  --ingress all \
  --cpu-boost \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_REGION=$GOOGLE_CLOUD_REGION,LOG_LEVEL=$LOG_LEVEL,AUTH_REQUIRED=$AUTH_REQUIRED,RATE_LIMIT=$RATE_LIMIT

APP_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $GOOGLE_CLOUD_REGION --format="value(status.address.url)")
echo $APP_URL
```

#### Setup Custom Domain

```bash
# If not already done, verify your domain ownership with Google
gcloud domains verify $DOMAIN
# Check it
gcloud domains list-user-verified

# Create a mapping to your domain
gcloud beta run domain-mappings create \
  --region $GOOGLE_CLOUD_REGION \
  --service $SERVICE_NAME \
  --domain $SERVICE_NAME.$DOMAIN
```

### CI/CD

CI/CD is achieved using Google Cloud Build, with the configuration in `deploy/cloudbuild.yaml`. 