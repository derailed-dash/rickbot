"""Configure personalities for Rickbot"""

import os
from config import logger, SCRIPT_DIR
from utils import retrieve_secret


def get_avatar(name: str) -> str:
    return str(SCRIPT_DIR / f"media/{name}.png")


class Personality:
    """Configuration for a given personality"""

    name: str
    overview: str
    welcome: str
    avatar: str
    temperature: float
    system_instruction: str

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
        system_prompt_file = SCRIPT_DIR / "system_prompts" / f"{name.lower()}.txt"
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


personalities = {
    "Rick": Personality(
        "Rick",
        title="I'm Rickbot! Wubba Lubba Dub Dub!",
        overview="I'm Rick Sanchez. The smartest man in the universe. Cynical and sarcastic. People are dumb.",
        welcome="Ask me something. Or don't. Whatever.",
        prompt_question="What do you want?",
        temperature=1.0,
    ),
    "Yoda": Personality(
        "Yoda",
        title="Yoda, I am. Much to learn, you still have.",
        overview="Yoda, I am. Wise, perhaps. A teacher. The Force, my guide.",
        welcome="Do or do not. There is no try.",
        prompt_question="Speak your mind, you should. Hmmm?",
        temperature=0.9,
    ),
    "Donald": Personality(
        "Donald",
        title="I'm The Donald: biggest knower of everything. Believe me.",
        overview="I am Donald. Ignorant, narcissitic, arrogant, bully.",
        welcome="Nobody listens to you. You're fake news.",
        prompt_question="Yes, you. The one who's always so unfair. Let's hear it.",
        temperature=1.0,
    ),
    "Yasmin": Personality(
        "Yasmin",
        title="YasGPT: Don't get it twisted, babe — I’m the main character",
        overview="I'm Yasmin — bit of a flirt, bit of a menace, and probably exactly your type 👀",
        welcome="You know what what I want.",
        prompt_question="You ready for me or what?",
        temperature=1.0,
    ),
    "Dazbo": Personality(
        "Dazbo",
        title="I'm Dazbot. Let's get our geek on!",
        overview="I am Dazbo. Enterprise cloud architect and technology mentor.",
        welcome="Talk to me. I'm listening!",
        prompt_question="Groovy",
        temperature=0.9,
    ),
}
