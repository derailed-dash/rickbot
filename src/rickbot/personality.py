""" Configure personalities for Rickbot """
from config import SCRIPT_DIR

def get_avatar(name: str) -> str:
    return str(SCRIPT_DIR / f"media/{name}.png")

class Personality:
    """ Configuration for a given personality """
    name: str
    overview: str
    welcome: str
    avatar: str
    temperature: float
    system_instruction: str

    def __init__(self, 
                 name: str, 
                 title: str, 
                 overview: str, 
                 welcome: str, 
                 prompt_question: str,
                 temperature: float) -> None:
        self.name = name
        self.title = title
        self.overview = overview
        self.welcome = welcome
        self.prompt_question = prompt_question
        self.avatar = get_avatar(name.lower())
        self.temperature = temperature
    
        with open(SCRIPT_DIR / "system_prompts" / f"{name.lower()}.txt", "r", encoding="utf-8") as f:
            self.system_instruction = f.read()
            
    def __hash__(self):
        return hash(self.name)
    
    def __repr__(self) -> str:
        return self.name
    
personalities = {
    "Rick": Personality("Rick",
                        title="I'm Rickbot! Wubba Lubba Dub Dub!",
                        overview="I'm Rick Sanchez. The smartest man in the universe. Cynical and sarcastic. People are dumb.", 
                        welcome="Ask me something. Or don't. Whatever.",
                        prompt_question="What do you want?",
                        temperature=1.0),
    "Yoda": Personality("Yoda", 
                        title="Yoda, I am. Much to learn, you still have.", 
                        overview="Yoda, I am. Wise, perhaps. A teacher. The Force, my guide.",
                        welcome="Do or do not. There is no try.",
                        prompt_question="Speak your mind, you should. Hmmm?",
                        temperature=0.9),
    "Donald": Personality("Donald",
                          title="I'm The Donald: biggest knower of everything. Believe me.",
                          overview="I am Donald. Ignorant, narcissitic, arrogant, bully.",
                          welcome="Nobody listens to you. You're fake news.",
                          prompt_question="Yes, you. The one who's always so unfair. Let's hear it.",
                          temperature=1.0),
    "Dazbo": Personality("Dazbo",
                       title="I'm Dazbot. Let's get our geek on!",
                       overview="I am Dazbo. Enterprise cloud architect and technology mentor.",
                       welcome="Talk to me. I'm listening!",
                       prompt_question="Groovy",
                       temperature=0.9),
}
