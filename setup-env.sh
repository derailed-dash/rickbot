#!/bin/bash
# This script is meant to be sourced to set up your development environment.
# It configures gcloud, installs dependencies, and activates the virtualenv.
#
# Usage:
#   source ./setup-env.sh <noauth>

# --- Color and Style Definitions ---
RESET='\033[0m'
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'

echo -e "${BLUE}${BOLD}--- ☁️  Configuring Google Cloud environment ---${RESET}"

# 1. Check for .env file
if [ ! -f .env ]; then
	echo -e "${RED}❌ Error: .env file not found.${RESET}"
	echo "Please create a .env file with your project variables and run this command again."
	echo "An example .env.example file has been created for you:"
	echo -e "${YELLOW}GOOGLE_CLOUD_STAGING_PROJECT=your-staging-project-id\nGOOGLE_CLOUD_PRD_PROJECT=your-prod-project-id${RESET}" > .env.example
	return 1
fi

# 2. Source environment variables and export them
echo -e "Sourcing variables from ${BLUE}.env${RESET} file..."
set -a # automatically export all variables (allexport = on)
source .env
set +a # disable allexport mode

# 3. Authenticate with gcloud and configure project
if [ "$1" != "noauth" ]; then
    echo -e "\n🔐 Authenticating with gcloud and setting project to ${BOLD}$GCP_PROJECT...${RESET}"
    gcloud auth login --update-adc --launch-browser
    gcloud config set project "$GCP_PROJECT"
    gcloud auth application-default set-quota-project "$GCP_PROJECT"
else
    echo -e "\n${YELLOW}Skipping gcloud authentication as requested.${RESET}"
    gcloud config set project "$GCP_PROJECT"
fi

echo -e "\n${BLUE}--- Current gcloud project configuration ---${RESET}"
gcloud config list project
echo -e "${BLUE}------------------------------------------${RESET}"

# 4. Get project numbers

echo "Getting project numbers..."
export PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT --format="value(projectNumber)")
echo -e "${BOLD}PROJECT_NUMBER:${RESET} $PROJECT_NUMBER"
echo -e "${BLUE}------------------------------------------${RESET}"

# 6. Sync Python dependencies and activate venv
echo "Syncing python dependencies with uv..."
uv sync --dev

echo "Activating Python virtual environment..."
source .venv/bin/activate

echo -e "\n${GREEN}✅ Environment setup complete for ${BOLD}$TARGET_ENV${RESET}${GREEN} with project ${BOLD}$GCP_PROJECT${RESET}${GREEN}. Your shell is now configured.${RESET}"