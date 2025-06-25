""" Creates local .streamlit/secrets.toml from secret in Google Secret Manager 
We can run this from our app code or standalone. """
import os
from functools import lru_cache
from google.cloud import secretmanager

@lru_cache
def create_secrets_toml(google_project_id: str):
    streamlit_dir = ".streamlit"
    secrets_file_path = os.path.join(streamlit_dir, "secrets.toml")
    
    if os.path.exists(secrets_file_path):
        print(".streamlit/secrets.toml already exists, skipping creation.")
        return # Nothing to do

    print("Retrieving OAuth credentials.")
    secret_name = os.environ.get("STREAMLIT_SECRETS_SECRET_NAME", "rickbot-streamlit-secrets-toml")
    secret_version = os.environ.get("STREAMLIT_SECRETS_SECRET_VERSION", "latest")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{google_project_id}/secrets/{secret_name}/versions/{secret_version}"

    try:
        response = client.access_secret_version(request={"name": name})
        secrets_content = response.payload.data.decode("UTF-8")

        os.makedirs(streamlit_dir, exist_ok=True)
        print(".streamlit/ created.")
        with open(secrets_file_path, "w") as f:
            f.write(secrets_content)
        print(f"Successfully created {secrets_file_path}")

    except Exception as e:
        raise ValueError(f"Error accessing secret '{secret_name}' from Secret Manager: {e}") from e

if __name__ == "__main__":
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    create_secrets_toml(project_id)
