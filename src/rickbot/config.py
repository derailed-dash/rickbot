""" Configuration for the Rickbot """
import logging
import os
from dataclasses import dataclass
import streamlit as st

@dataclass
class Config:
    """Holds application configuration."""
    project_id: str
    region: str
    logger: logging.Logger
    auth_required: bool # Whether we require logon
    rate_limit: int # How many model requests we can make

@st.cache_resource
def get_config(app_name: str) -> Config:
    """
    Retrieves environment variables, initializes the logger, and returns a configuration object.
    This function is cached and runs only once per session.
    """
    # --- Logger Initialization ---
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    app_logger = logging.getLogger(app_name)
    log_level_num = getattr(logging, log_level, logging.INFO)
    app_logger.setLevel(log_level_num)
    
    # Add a handler only if one doesn't exist to prevent duplicate logs
    if not app_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d:%(name)s - %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)
    
    app_logger.info("Logger initialised.")
    app_logger.debug("DEBUG level logging enabled.")    

    # --- Environment Variable Retrieval and Validation ---
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    region = os.environ.get('GOOGLE_CLOUD_REGION')
    auth_required = os.environ.get("AUTH_REQUIRED", "True").lower() == "true"
    limit = int(os.environ.get("RATE_LIMIT", "20"))
    
    if not project_id:
        app_logger.error("Configuration Error: GOOGLE_CLOUD_PROJECT not set.")
        st.error("🚨 Configuration Error: Cannot determine Project ID.")
        st.stop()

    if not region:
        app_logger.warning("Could not determine Google Cloud Region. Using 'global'.")
        st.warning("⚠️ Could not determine Google Cloud Region. Using 'global'.")
        region = "global"

    app_logger.info(f"Using Google Cloud Project: {project_id}")
    app_logger.info(f"Using Google Cloud Region: {region}")
    app_logger.info(f"Auth required: {auth_required}")
    app_logger.info(f"Rate limit: {limit}")

    return Config(project_id=project_id, 
                  region=region, 
                  logger=app_logger, 
                  auth_required=auth_required,
                  rate_limit=limit)
