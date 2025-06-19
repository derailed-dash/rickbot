import streamlit as st
from agent import load_client, get_rick_bot_response, retrieve_env_vars, initialise_logger

# --- Page Configuration ---
st.set_page_config(
    page_title="RickBot",
    page_icon="🤖",
    layout="centered",
)

APP_NAME = "rickbot"

gcp_project_id, gcp_region, logging_level = retrieve_env_vars()
logger = initialise_logger(APP_NAME, logging_level)
# Leverage st.cache_resource so that we only show these once
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
            chat_history=st.session_state.messages[:-1], # Send history, excluding the new user prompt
            user_prompt=prompt
        )
        # Use st.write_stream to render the response as it comes in
        full_response = st.write_stream(response_stream)

    # Add the full bot response to the session state for context in the next turn
    st.session_state.messages.append({"role": "assistant", "content": full_response})