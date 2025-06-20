import logging
import os
from functools import lru_cache
import streamlit as st
from agent import load_client, get_rick_bot_response

# --- Page Configuration ---
st.set_page_config(
    page_title="RickBot",
    page_icon="🤖",
    layout="centered",
)

APP_NAME = "rickbot"

@st.cache_resource
@lru_cache
def initialise_logger(app_name: str, log_level: str):
    retrieved_logger = logging.getLogger(app_name) 
    log_level_num = getattr(logging, log_level, logging.INFO) # default to INFO if bad var
    retrieved_logger.setLevel(log_level_num)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d:%(name)s - %(levelname)s: %(message)s',
                                  datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    
    # Important to prevent duplicate log entries
    if retrieved_logger.hasHandlers():
        retrieved_logger.handlers.clear()

    retrieved_logger.addHandler(handler) # Attach the StreamHandler

    retrieved_logger.info("Logger initialised.")
    retrieved_logger.debug("DEBUG level logging enabled.")
        
    return retrieved_logger

@st.cache_resource
def retrieve_env_vars():
    """ Retrieve env vars. They could be existing env vars, defined in .env, or defined in .streamlit/config.tom """
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', None)
    region = os.environ.get('GOOGLE_CLOUD_REGION', None)
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper() # default to INFO if not set

    if not project_id:
        st.error(
            "🚨 Configuration Error: Cannot determine Project ID."
        )
        st.stop()
        
    if not region:
        st.error(
            "⚠️ Could not determine Google Cloud Region. Using 'global'. "
        )
        region = "global"
        
    return project_id, region, log_level

gcp_project_id, gcp_region, logging_level = retrieve_env_vars()
logger = initialise_logger(APP_NAME, logging_level)
logger.debug(f"{gcp_project_id=}")
logger.debug(f"{gcp_region=}")

# --- Title and Introduction ---
st.title("Wubba Lubba Dub Dub! Chat with RickBot")
st.caption("Ask me something. Or don't. Whatever.")

# --- Session State Initialization ---
# This is crucial for maintaining the conversation history.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("Configuration")
    st.info("This chatbot impersonates Rick Sanchez. It may be cynical and sarcastic. Viewer discretion is advised.")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- Main Chat Interface ---

# Initialize the AI client
try:
    client = load_client(gcp_project_id, gcp_region)
except Exception as e:
    st.error(f"Could not initialize the application. Please check your configuration. Error: {e}")
    st.stop()

# Display previous messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new user input
if prompt := st.chat_input("What do you want?"):
    # Add user message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display bot response
    with st.chat_message("assistant"):
        # The stream object from the generator
        response_stream = get_rick_bot_response(
            client=client,
            chat_history=st.session_state.messages)
        # Use st.write_stream to render the response as it comes in
        full_response = st.write_stream(response_stream)

    # Add the full bot response to the session state for context in the next turn
    st.session_state.messages.append({"role": "assistant", "content": full_response})
