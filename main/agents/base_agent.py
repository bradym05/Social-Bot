# Dependencies
from main.web import Browser
from main.llm import BaseLLM
from typing import List
from better_profanity import profanity

# Declare base browser agent class
class BaseAgent:
    # Initialize object
    def __init__(
        self, 
        browser:Browser, 
        llm:BaseLLM,
        censor:bool=True
        ):
        # Initialize variables
        self.browser = browser
        self.llm = llm
        self.max_search_chars = max_search_chars
        self.censor = censor