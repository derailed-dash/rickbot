"""A Rick Sanchez (Rick and Morty) Rickbot agent,
built using Google Gen AI SDK and Gemini."""

from functools import lru_cache
from google import genai
from google.genai.types import Content, GenerateContentConfig, GoogleSearch, Tool, Part

from personality import Personality

MODEL = "gemini-2.5-flash"


@lru_cache
def load_client(gcp_project_id, gcp_region):
    """Initializes and caches a Vertex AI client for the session.

    Args:
        gcp_project_id (str): The Google Cloud project ID.
        gcp_region (str): The Google Cloud region (e.g., 'us-central1').

    Returns:
        genai.Client: An authenticated Vertex AI client instance.

    Raises:
        Exception: If the client fails to initialize.
    """

    try:
        client = genai.Client(
            vertexai=True,
            project=gcp_project_id,
            location=gcp_region,
        )
        return client
    except Exception as e:
        raise Exception("Error initialising Vertex Client.") from e


@lru_cache
def initialise_model_config(personality: Personality) -> GenerateContentConfig:
    """Creates the configuration for the Gemini model. Sets up the system prompt that instructs the model to act as
    Rick. Also configures the model's generation parameters and
    enables the Google Search tool for answering questions outside its
    knowledge base.

    Returns:
        GenerateContentConfig: The configuration object for the model.
    """

    system_instruction = personality.system_instruction

    # Create tool to enable grounding with Google Search
    tools = [
        Tool(google_search=GoogleSearch()),
    ]

    generate_content_config = GenerateContentConfig(
        temperature=personality.temperature,
        top_p=1,
        max_output_tokens=16384,
        tools=tools,
        system_instruction=[Part.from_text(text=system_instruction)],
    )

    return generate_content_config


def get_rick_bot_response(
    client, chat_history: list[dict], model_config: GenerateContentConfig
):
    """
    Generates a streaming response from RickBot model.

    This function takes the conversation history, formats it into the
    structure expected by the Gemini API, and then streams the model's
    response.

    Args:
        client (genai.Client): The authenticated Vertex AI client.
        chat_history (list[dict]): A list of previous messages, where each
            message is a dict with "role" and "content" keys.
        model_config (GenerateContentConfig): The configuration for the
            generative model, including the system prompt and tools.

    Yields:
        str: A stream of response text chunks from the AI model.
    """

    contents = []
    for message in chat_history:
        role = "model" if message["role"] == "assistant" else message["role"]

        if role not in (
            "user",
            "model",
        ):  # Skip any roles that are not 'user' or 'model'
            continue

        parts_for_current_message = [Part.from_text(text=message["content"])]

        # If there's an attachment, add it as a data part
        if "attachment" in message and message["attachment"]:
            attachment = message["attachment"]
            parts_for_current_message.append(
                Part.from_bytes(
                    data=attachment["data"], mime_type=attachment["mime_type"]
                )
            )

        contents.append(Content(role=role, parts=parts_for_current_message))

    try:
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=contents,
            config=model_config,
        ):
            if (
                chunk.candidates
                and chunk.candidates[0].content
                and chunk.candidates[0].content.parts
            ):
                yield chunk.text
    except Exception as e:
        raise Exception("Error in generation") from e
