""" A Rick Sanchez (Rick and Morty) Rickbot, rendered using Streamlit. """

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import streamlit as st
from agent import load_client, get_rick_bot_response, initialise_model_config

APP_NAME = "Rickbot"
SCRIPT_DIR = Path(__file__).parent
AVATARS = {
    "assistant": str(SCRIPT_DIR / "media/rick.png"),
    "user": str(SCRIPT_DIR / "media/morty.png")
}

# --- Page Configuration ---
st.set_page_config(
    page_title=APP_NAME,
    page_icon=AVATARS["assistant"],
    layout="centered",
)

@dataclass
class Config:
    """Holds application configuration."""
    project_id: str
    region: str
    logger: logging.Logger

@st.cache_resource
def get_config() -> Config:
    """
    Retrieves environment variables, initializes the logger, and returns a configuration object.
    This function is cached and runs only once per session.
    """
    # --- Logger Initialization ---
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    app_logger = logging.getLogger(APP_NAME)
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

    return Config(project_id=project_id, region=region, logger=app_logger)
        
# --- One-time Application Setup  ---
config = get_config()
logger = config.logger

# --- Title and Introduction ---
st.title(f"Wubba Lubba Dub Dub! I'm {APP_NAME}.")

def do_rick():
    st.caption("Ask me something. Or don't. Whatever.")

    # --- Session State Initialization ---
    # For maintaining the conversation history.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- Sidebar for Configuration ---
    with st.sidebar:
        st.caption(f"Welcome, {st.user.name}")
        st.button("Log out", on_click=st.logout)
        st.divider()
        
        _, col2, _ = st.columns([1,2,1])
        with col2:
            st.image(AVATARS["assistant"], width=160)
        
        st.info("I'm Rick Sanchez. The smartest man in the universe. I may be cynical and sarcastic. User discretion is advised.")
        
        # --- File Uploader ---
        uploaded_file = st.file_uploader(
            "Upload a file if you want. I'll probably just make fun of it.",
            type=["png", "jpg", "jpeg", "pdf", "mp3", "mp4", "mov", "webm"]
        )
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
            
        st.info(
            """
            ### Info
            * Created by Dazbo.
            * I do not store any user data, prompts or responses.
            * Check out the [GitHub repo](https://github.com/derailed-dash/rickbot/).
            * View the [Rickbot blog post](https://medium.com/google-cloud/creating-a-rick-morty-chatbot-with-google-cloud-and-the-gen-ai-sdk-e8108e83dbee).
            """
        )
        
    # --- Main Chat Interface ---

    # Initialize the AI client
    try:
        client = load_client(config.project_id, config.region)
        model_config = initialise_model_config()
    except Exception as e:
        logger.error(f"Failed to initialize AI client: {e}", exc_info=True)
        st.error(f"⚠️ Could not initialize the application. Please check your configuration. Error: {e}")
        st.stop()

    # Display previous messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=AVATARS[message["role"]]):
            # Render any attachments first
            if "attachment" in message and message["attachment"]:
                attachment = message["attachment"]
                if "image" in attachment["mime_type"]:
                    st.image(attachment["data"])
                elif "video" in attachment["mime_type"]:
                    st.video(attachment["data"])
                # You could add more handlers here for PDFs, etc.
            
            st.markdown(message["content"])

    # Handle new user input
    if prompt := st.chat_input("What do you want?"):
        # Create the user message object, including any attachments
        user_message: dict[str, Any] = {"role": "user", "content": prompt}
        if uploaded_file:
            user_message["attachment"] = {
                "data": uploaded_file.getvalue(),
                "mime_type": uploaded_file.type or "",
            }
        st.session_state.messages.append(user_message)

        # Display the user's message and attachment in the chat
        with st.chat_message("user", avatar=AVATARS.get("user")):
            if uploaded_file:
                mime_type = uploaded_file.type or ""
                if "image" in mime_type:
                    st.image(uploaded_file)
                elif "video" in mime_type:
                    st.video(uploaded_file)
            st.markdown(prompt)

        # Generate and display Rick's response
        with st.status("Thinking...", expanded=True) as bot_status:
            with st.chat_message("assistant", avatar=AVATARS["assistant"]):
                try:
                    response_stream = get_rick_bot_response(
                        client=client,
                        chat_history=st.session_state.messages,
                        model_config=model_config)
                    # Render the response as it comes in
                    full_response = st.write_stream(response_stream)
                    bot_status.update(label="Done.", state="complete")
                    
                    # Add the full bot response to the session state for context in the next turn
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    logger.error(e.__cause__)
                    st.error(f"Ugh, great. I think I'm too drunk to respond. Are you even connected right now? Error: {type(e.__cause__)}")

# Login with Google OAuth
if not st.user.is_logged_in:
    login_left, login_right = st.columns([0.25, 0.75])
    if login_left.button("Log in with Google", ):
        st.login()
    login_right.markdown(":sunglasses: Please login to use Rickbot. Any Google account will do.")
else:
    do_rick()
