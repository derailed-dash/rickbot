"""
This module contains the chat interface for the Ricbot Streamlit application.
"""
from typing import Any
import streamlit as st

from config import logger, SCRIPT_DIR
from agent import load_client, get_rick_bot_response, initialise_model_config
from personality import personalities

USER_AVATAR = str(SCRIPT_DIR / "media/morty.png")

def get_rick_response(client, model_conf, prompt, uploaded_file, rate_limiter, rate_limit, current_personality):
    """
    Handles user input, rate limiting, and generating the bot's response.
    """
    # --- Rate Limiting Check ---
    # Perform this check *before* modifying session state or displaying the user's prompt
    if not rate_limiter.hit(rate_limit, "request_lim"):
        st.warning("Whoa, slow down there, Morty! You Morties are asking waaaay too many questions. Give me a minute.")
        st.stop() # Stop execution to prevent the message from being processed

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
                st.image(uploaded_file.getvalue())
            elif "video" in mime_type:
                st.video(uploaded_file.getvalue())
        st.markdown(prompt)

    # Generate and display Rick's response
    with st.status("Thinking...", expanded=True) as bot_status:
        with st.chat_message("assistant", avatar=current_personality.avatar):
            try:
                response_stream = get_rick_bot_response(
                    client=client,
                    chat_history=st.session_state.messages,
                    model_config=model_conf)
                
                full_response = st.write_stream(response_stream)
                bot_status.update(label="Done.", state="complete")
                
                # Add the full bot response to the session state for context in the next turn
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                logger.error(e.__cause__)
                st.error(f"Ugh, great. I think I'm too drunk to respond. Are you even connected right now? Error: {type(e.__cause__)}")

def render_chat(config, rate_limiter, rate_limit):
    """
    Renders the main chat interface, including sidebar and chat history.
    """
    current_personality = personalities[st.session_state.current_personality]
    # --- Title and Introduction ---
    header_col1, header_col2 = st.columns([0.3, 0.7])
    header_col1.image(current_personality.avatar, width=140)
    header_col2.title(f"{current_personality.title}")
    st.caption(current_personality.welcome)
    
    # --- Session State Initialization ---
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
            if "attachment" in message and message["attachment"]:
                attachment = message["attachment"]
                if "image" in attachment["mime_type"]:
                    st.image(attachment["data"])
                elif "video" in attachment["mime_type"]:
                    st.video(attachment["data"])
            st.markdown(message["content"])

    # Handle new user input
    if prompt := st.chat_input(current_personality.prompt_question):
        get_rick_response(client, model_config, prompt, uploaded_file, rate_limiter, rate_limit, current_personality)
    