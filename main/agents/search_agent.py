# Dependencies
from main.web import Browser
from main.llm import BaseLLM
from main.agents.base_agent import BaseAgent
from typing import List
from main.web.browser import to_bmp

# Declare search browser agent class
class SearchAgent(BaseAgent):
    # Initialize object
    def __init__(
        self, 
        browser:Browser, 
        llm:BaseLLM,
        max_search_chars:int=400,
        censor:bool=True,
        ):
        # Initialize from superclass
        super(SearchAgent, self).__init__(browser=browser, llm=llm, censor=censor)
        # Initialize variables
        self.browser = browser
        self.llm = llm
        self.max_search_chars = max_search_chars
        self.censor = censor
    
    # Basic web search function
    def process_web_search(self, phrases:List[str], query_chars:int=60) -> str:
        # Create query from given phrases
        query = ""
        for p in phrases:
            max_reached = False
            for s in p.split():
                if len(query) + len(s) > query_chars:
                    max_reached = True
                    break
                else:
                    query += s + " "
            if max_reached:
                break
        # Search for given query
        results = self.browser.search_web(query=query)
        result_string = ""
        # Append results to string
        for r in results:
            # TODO - Check for profanity here
            result_string += f"{r}, "
            # Check if max has been exceeded
            if len(result_string) > self.max_search_chars:
                break
        # Return final result string
        return result_string