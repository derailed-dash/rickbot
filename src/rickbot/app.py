# app.py

""" A Rick Sanchez (Rick and Morty) Rickbot, rendered using Streamlit. """
import streamlit as st
from limits import storage, parse
from limits.strategies import MovingWindowRateLimiter

from config import get_config, logger, APP_NAME
from create_auth_secrets import create_secrets_toml
from personality import personalities, get_avatar
from chat import render_chat # Import the new chat renderer

# --- Page Configuration ---
# This must be the first Streamlit command in your script.
rickbot_avatar = get_avatar("rickbot-trans")

st.set_page_config(
    page_title=APP_NAME,
    page_icon=rickbot_avatar, # Default icon
    layout="centered",
)

@st.cache_resource
def get_rate_limiter():
    """ Simple in-memory storage for rate limiting. """
    limits_mem_store = storage.MemoryStorage()
    limiter = MovingWindowRateLimiter(limits_mem_store)
    limit = parse(f"{config.rate_limit}/minute")
    return limiter, limit

# --- One-time Application Setup ---
config = get_config()
rate_limiter, rate_limit = get_rate_limiter()

# Initialize session state for personality if it doesn't exist.
if "current_personality" not in st.session_state:
    st.session_state.current_personality = "Rick"

# Get the current personality object to display the correct header.
# This will update if the personality is changed in the sidebar causing a rerun.
current_personality = personalities[st.session_state.current_personality]

def authenticated_flow():
    """ Defines the logic to run after successful authentication or if auth is not required. """
    render_chat(
        config=config,
        rate_limiter=rate_limiter,
        rate_limit=rate_limit
    )

# --- Authentication and Page Rendering ---
if config.auth_required:
    try:
        create_secrets_toml(config.project_id)
    except ValueError as e:
        logger.error(f"Failed to setup auth: {e}", exc_info=True)
        st.error(f"⚠️ Could not initialize the application. Please check your configuration. Error: {e}")
        st.stop()
    
    if not st.user.is_logged_in:
        header_col1, header_col2 = st.columns([0.3, 0.7])
        header_col1.image(rickbot_avatar, width=140)
        header_col2.title(f"{current_personality.title}")
        
        st.divider()
        st.markdown("Rickbot is a chat application. Chat with Rick, ask your questions, and feel free to upload content as part of your discussion. Rickbot also offers multiple other personalities to interact with.")
        st.markdown(":eyes: We do not store any user data, prompts or responses. Read our [Privacy Policy](/privacy_policy).")        
        st.divider()
        st.markdown(":lock: Please login to use Rickbot. Any Google account will do. Login helps us prevent abuse and maintain a stable, accessible experience for everyone.")
        if st.button("Log in with Google", use_container_width=True):
            st.login()
    else:
        authenticated_flow()
else:
    authenticated_flow()
