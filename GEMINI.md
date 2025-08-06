# Project: Rickbot

## Project Overview

This project is "Rickbot," a multi-personality chatbot built with Python. The core framework is Streamlit, which provides the user interface. The chatbot's intelligence is powered by the Google Gemini SDK (`google-genai`), specifically using the `gemini-2.5-flash` model. The application is designed to be deployed as a containerized service on Google Cloud Run.

A key feature of Rickbot is its ability to adopt different personalities (e.g., Rick Sanchez, Yoda). These personalities are defined in a YAML file and influence the bot's title, avatar, and system instructions, which are fed to the Gemini model. The application also supports grounding with Google Search to answer questions outside its immediate knowledge base.

## Building and Running

### Dependencies

Project dependencies are managed in `pyproject.toml` and can be installed using `uv`:

```bash
# Create the virtual environment
uv venv .venv

# Install dependencies
uv sync
```

### Local Development

To run the application locally for development, execute the following command from the project's root directory after installing dependencies:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the Streamlit app
cd src/rickbot
uv run streamlit run app.py --browser.serverAddress=localhost
```

### Docker

The project includes a `Dockerfile` in `src/rickbot/` for containerizing the application. The `README.md` provides detailed instructions for building the Docker image and running it locally, including how to pass necessary environment variables and mount Google Cloud credentials.

### Deployment

The application is designed for automated deployment to Google Cloud Run using Google Cloud Build. The CI/CD pipeline is defined in `deploy/cloudbuild.yaml`. This pipeline builds the Docker image, pushes it to Google Artifact Registry, and then deploys it as a Cloud Run service.

## Development Conventions

-   **Configuration (`src/rickbot/config.py`):** Application configuration is managed via environment variables (e.g., `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_REGION`, `AUTH_REQUIRED`, `RATE_LIMIT`). A `Config` dataclass holds these values, and the `get_config()` function is cached with `@st.cache_resource` to avoid reloading on every interaction.

-   **Application Entrypoint (`src/rickbot/app.py`):** This is the main Streamlit application file. It handles page configuration, optional user authentication, rate limiting, and calls the main chat rendering logic.

-   **Chat Interface (`src/rickbot/chat.py`):** This module is responsible for rendering the entire chat UI using Streamlit components. It manages the chat history in `st.session_state`, handles user input and file uploads, and displays the streaming response from the agent.

-   **Agent Logic (`src/rickbot/agent.py`):** This file contains the core logic for interacting with the Gemini model. It initializes the Vertex AI client, configures the model with system instructions and tools (like Google Search), and formats the chat history for the `generate_content_stream` API call.

-   **Personalities (`src/rickbot/personality.py`):** This is a central feature. Personalities are defined in `src/rickbot/data/personalities.yaml`. The `Personality` dataclass loads the configuration for each character, including their name, title, and avatar. System prompts are loaded from corresponding text files in `src/rickbot/data/system_prompts/` or, if not found, are retrieved from Google Secret Manager (e.g., `dazbo-system-prompt`).
