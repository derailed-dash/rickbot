""" A Rick Sanchez (Rick and Morty) Rickbot, rendered using Streamlit. """

from typing import Any
from limits import storage, parse
from limits.strategies import MovingWindowRateLimiter
import streamlit as st

from config import get_config, SCRIPT_DIR
from agent import load_client, get_rick_bot_response, initialise_model_config
from create_auth_secrets import create_secrets_toml
from personality import personalities

APP_NAME = "Rickbot"
USER_AVATAR = str(SCRIPT_DIR / "media/morty.png")

# --- Page Configuration ---
st.set_page_config(
    page_title=APP_NAME,
    page_icon=personalities["Rick"].avatar,
    layout="centered",
)

@st.cache_resource # Cache across all sessions
def get_rate_limiter():
    """
    Use a simple in-memory storage for rate limiting. 
    For a shared limit, an external store like Redis/Memorystore would be needed.
    """
    limits_mem_store = storage.MemoryStorage()
    limiter = MovingWindowRateLimiter(limits_mem_store)
    limit = parse(f"{config.rate_limit}/minute")
    return limiter, limit

# --- One-time Application Setup  ---
config = get_config(APP_NAME)
logger = config.logger
rate_limiter, rate_limit = get_rate_limiter()

if "current_personality" not in st.session_state:
    st.session_state.current_personality = "Rick"

current_personality = personalities[st.session_state.current_personality]

# --- Title and Introduction ---
header_col1, header_col2 = st.columns([0.3, 0.7])
header_col1.image(current_personality.avatar, width=140)
header_col2.title(f"I'm {current_personality.name} Bot. {current_personality.title}")

def show_page():
    st.caption(current_personality.welcome)
    
    # --- Session State Initialization ---
    # For maintaining the conversation history.
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # --- Sidebar for Configuration ---
    with st.sidebar:
        if config.auth_required and st.user.is_logged_in:
            st.caption(f"Welcome, {st.user.name}")
            st.button("Log out", on_click=st.logout)

        # --- Personality Selection ---
        personality_names = list(personalities.keys())
        selected_personality = st.selectbox(
            "Choose your bot personality:", personality_names, index=personality_names.index(current_personality.name)
        )

        if selected_personality != current_personality.name:
            st.session_state.current_personality = selected_personality
            st.session_state.messages = [] # Reset messages on personality change
            st.rerun()
            
        st.info(current_personality.overview)
        
        # --- File Uploader ---
        uploaded_file = st.file_uploader(
            "Upload a file.",
            type=["png", "jpg", "jpeg", "pdf", "mp3", "mp4", "mov", "webm"]
        )
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
            
        st.info(
            """
            ### Info
            * Created by Dazbo.
            * I do not store any user data, prompts or responses. Read our [Privacy Policy](/privacy_policy).
            * Check out the [GitHub repo](https://github.com/derailed-dash/rickbot/).
            * View the [Rickbot blog post](https://medium.com/google-cloud/creating-a-rick-morty-chatbot-with-google-cloud-and-the-gen-ai-sdk-e8108e83dbee).
            """
        )
        
    # --- Main Chat Interface ---

    # Initialize the AI client
    try:
        client = load_client(config.project_id, config.region)
        model_config = initialise_model_config(current_personality)
    except Exception as e:
        logger.error(f"Failed to initialize AI client: {e}", exc_info=True)
        st.error(f"⚠️ Could not initialize the application. Please check your configuration. Error: {e}")
        st.stop()

    # Display previous messages from history
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else current_personality.avatar
        with st.chat_message(message["role"], avatar=avatar):
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
    if prompt := st.chat_input(current_personality.prompt_question):
        get_rick_response(client, model_config, prompt, uploaded_file)

def get_rick_response(client, model_conf, prompt, uploaded_file):        
    # Create the user message object, including any attachments
    user_message: dict[str, Any] = {"role": "user", "content": prompt}
    if uploaded_file:
        user_message["attachment"] = {
            "data": uploaded_file.getvalue(),
            "mime_type": uploaded_file.type or "",
        }
    st.session_state.messages.append(user_message)

    # Display the user's message and attachment in the chat
    with st.chat_message("user", avatar=USER_AVATAR):
        if uploaded_file:
            mime_type = uploaded_file.type or ""
            if "image" in mime_type:
                st.image(uploaded_file)
            elif "video" in mime_type:
                st.video(uploaded_file)
        st.markdown(prompt)

    # --- Rate Limiting Check ---
    if not rate_limiter.hit(rate_limit, "request_lim"): # Return False when limit exceeded
        st.warning("Whoa, slow down there, Morty! You Morties are asking waaaay too many questions. Give me a minute.")
        return
    
    # Generate and display Rick's response
    with st.status("Thinking...", expanded=True) as bot_status:
        with st.chat_message("assistant", avatar=current_personality.avatar):
            try:
                response_stream = get_rick_bot_response(
                    client=client,
                    chat_history=st.session_state.messages,
                    model_config=model_conf)
                # Render the response as it comes in
                full_response = st.write_stream(response_stream)
                bot_status.update(label="Done.", state="complete")
                
                # Add the full bot response to the session state for context in the next turn
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                logger.error(e.__cause__)
                st.error(f"Ugh, great. I think I'm too drunk to respond. Are you even connected right now? Error: {type(e.__cause__)}")

# Login with Google OAuth
if config.auth_required:
    # If we want to create the secrets.toml in the app code...
    try:
        create_secrets_toml(config.project_id)
    except ValueError as e:
        logger.error(f"Failed to setup auth: {e}", exc_info=True)
        st.error(f"⚠️ Could not initialize the application. Please check your configuration. Error: {e}")
        st.stop()
    
    if not st.user.is_logged_in:
        _, mid, _ = st.columns([0.2, 0.6, 0.2])
        with mid:
            st.divider()
            st.markdown("#### :lock: Please login to use Rickbot. Any Google account will do.")
            if st.button("Log in with Google", use_container_width=True):
                st.login()
            st.divider()
            st.markdown(":eyes: Read our [Privacy Policy](/privacy_policy)")
    else:
        show_page()
else:
    show_page()
