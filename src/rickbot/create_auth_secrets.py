""" Creates local .streamlit/secrets.toml from secret in Google Secret Manager 
We can run this from our app code or standalone. """
import os
import streamlit as st

from utils import retrieve_secret
from config import logger

@st.cache_resource
def create_secrets_toml(google_project_id: str):
    streamlit_dir = ".streamlit"
    secrets_file_path = os.path.join(streamlit_dir, "secrets.toml")
    
    if os.path.exists(secrets_file_path):
        logger.info(".streamlit/secrets.toml already exists, skipping creation.")
        return # Nothing to do

    logger.info("Retrieving OAuth credentials.")
    try:
        secret_name = "rickbot-streamlit-secrets-toml"
        secret = retrieve_secret(google_project_id, secret_name)

        os.makedirs(streamlit_dir, exist_ok=True)
        logger.info(".streamlit/ created.")
        with open(secrets_file_path, "w") as f:
            f.write(secret)
        logger.info(f"Successfully created {secrets_file_path}")

    except Exception as e:
        raise ValueError(f"Error accessing secret '{secret_name}' from Secret Manager: {e}") from e

if __name__ == "__main__":
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    create_secrets_toml(project_id) # type: ignore
