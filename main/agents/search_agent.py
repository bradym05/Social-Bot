# Dependencies
from main.web import Browser
from main.llm import BaseLLM
from main.agents.base_agent import BaseAgent
from typing import List

# Declare search browser agent class
class SearchAgent(BaseAgent):
    # Initialize object
    def __init__(
        self, 
        browser:Browser, 
        llm:BaseLLM,
        max_search_chars:int=150,
        censor:bool=True
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
        print(query)
        result_dictionary = self.browser.search_web(query=query)
        headings = result_dictionary.keys()
        result_string = ""
        # Check if anything was found
        if len(headings) > 0:
            # Append headings to string
            for h in headings:
                # Check if characters are less than maximum
                if len(h) + len(result_string) < self.max_search_chars:
                    # TODO - Check for profanity here
                    result_string += f"{h}, "
                else:
                    break
            # Update result string for better understanding
            result_string = "Related Article Headings: " + result_string
        # Return final result string
        return result_string