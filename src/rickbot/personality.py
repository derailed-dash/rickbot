"""Configure personalities for Rickbot"""

import os
import yaml  # pyyaml
from config import logger, SCRIPT_DIR
from utils import retrieve_secret


def get_avatar(name: str) -> str:
    return str(SCRIPT_DIR / f"media/{name}.png")


class Personality:
    """Configuration for a given personality"""

    def __init__(
        self,
        name: str,
        title: str,
        overview: str,
        welcome: str,
        prompt_question: str,
        temperature: float,
    ) -> None:
        self.name = name
        self.title = title
        self.overview = overview
        self.welcome = welcome
        self.prompt_question = prompt_question
        self.avatar = get_avatar(name.lower())
        self.temperature = temperature

        # Retrieve the prompt from the system_prompts folder
        # If the prompt doesn't exist, try retrieving from Secret Manager
        system_prompt_file = SCRIPT_DIR / "data/system_prompts" / f"{name.lower()}.txt"
        if os.path.exists(system_prompt_file):
            with open(system_prompt_file, "r", encoding="utf-8") as f:
                self.system_instruction = f.read()
        else:
            logger.info(
                f"Unable to find {system_prompt_file}. Attempting to retrieve from Secret Manager."
            )
            try:
                google_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
                secret_name = f"{name.lower()}-system-prompt"
                self.system_instruction = retrieve_secret(google_project, secret_name)  # type: ignore
                logger.info("Successfully retrieved.")
            except Exception as e:
                logger.warning(
                    f"Unable to retrieve '{secret_name}' from Secret Manager."
                )
                raise ValueError(
                    f"{system_prompt_file} not found and could not access '{secret_name}' from Secret Manager: {e}"
                ) from e

    def __hash__(self):
        return hash(self.name)

    def __repr__(self) -> str:
        return self.name


def load_personalities(yaml_file: str) -> dict[str, Personality]:
    """Load personalities from a YAML file."""
    peeps: dict[str, Personality] = {}
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        for personality_data in data:
            personality = Personality(**personality_data)
            peeps[personality.name] = personality
    return peeps


# Load personalities from the YAML file
personalities = load_personalities(str(SCRIPT_DIR / "data/personalities.yaml"))
