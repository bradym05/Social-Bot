# Dependencies
from main.web import Browser
from main.llm import BaseLLM
from main.agents.base_agent import BaseAgent
from typing import List

# SETTINGS
MAX_HISTORY_LENGTH = 10 # Delete search history after this length
QUERY_INPUT = """
You will be given information from an instagram post.
Generate a standalone search query to find relevant information. You output your search query in this format:
    Query: [YOUR SEARCH QUERY] 

Here are some examples:
    [INPUT]
    POST CAPTION: My secret to the crispiest sourdough bread at home 🥖✨
    IMAGE DESCRIPTION: A beautifully scored sourdough loaf fresh out of the oven resting on a cooling rack
    POST COMMENTS: What hydration level did you use?, Do you bake it in a Dutch oven?, Looks amazing, recipe please!

    [YOUR OUTPUT]
    Query: "How to make crispy sourdough bread in a Dutch oven"
    
    [INPUT]
    POST CAPTION: Hidden gem in Kyoto! You have to add this to your itinerary ⛩️🍃
    IMAGE DESCRIPTION: A peaceful, moss-covered garden with a small stone bridge and tall trees
    POST COMMENTS: Is this Giouji Temple?, Going to Japan next month, saving this!, How early do you need to get there to avoid crowds?

    [YOUR OUTPUT]
    Query: "Giouji Temple Kyoto moss garden"
    
    [INPUT]
    POST CAPTION: She absolutely devoured this look on the red carpet tonight 📸🔥
    IMAGE DESCRIPTION: A celebrity wearing a vintage, dramatic sheer black dress with sharp shoulders
    POST COMMENTS: Mugler 1995 archive!!, Who is the designer?, Her stylist deserves a raise.

    [YOUR OUTPUT]
    Query: "Mugler 1995 archive sheer black dress"
    
    [INPUT]
    POST CAPTION: Finally finished the DIY archway in the living room! 🛠️🎨
    IMAGE DESCRIPTION: A time-lapse photo showing a person applying joint compound to a curved hallway entrance
    POST COMMENTS: Did you use drywall or MDF for the curve?, This is exactly what I want to do in my hallway, What brand of plaster did you use?

    [YOUR OUTPUT]
    Query: "How to build a DIY arched doorway with drywall and MDF"
"""

# Declare search browser agent class
class SearchAgent(BaseAgent):
    """
    Browser and LLM manager for searching.
    
    Attributes
    ----------
    browser : Browser
        Browser object.
    llm : BaseLLM
        LLM object.
    max_search_chars : int | None
        The maximum total length of the results returned
        from a search. Defaults to 400.
    
    """
    # Initialize object
    def __init__(
        self, 
        browser:Browser, 
        llm:BaseLLM,
        max_search_chars:int=400,
        ):
        # Initialize from superclass
        super(SearchAgent, self).__init__(browser=browser, llm=llm)
        # Initialize variables
        self.browser = browser
        self.llm = llm
        self.max_search_chars = max_search_chars
        self.search_history = []
        # Check if browser is a save browser
        if self._save:
            self.search_history = self.browser.get_data("search_history") or []

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
            result_string += f'"{r}", '
            # Check if max has been exceeded
            if len(result_string) > self.max_search_chars:
                break
        # Return final result string
        return result_string
    
    # Generate and extract a search query
    def get_query(self, messages:List[str], instructions:str=QUERY_INPUT, record:bool=False) -> str | None:
        # Initialize messages for search query
        query_messages = messages.copy()
        # Prevent repititon if search history is enabled
        if record and len(self.search_history) > 0:
            query_messages.append(f'Search History: "{'", "'.join(self.search_history)}' +"\n")

        query_messages.append("[YOUR OUTPUT]:\nQuery: [YOUR SEARCH QUERY]")
        # Generate query from post information
        search_query = self.llm.get_response(
            instructions=instructions,
            messages=query_messages,
            temperature=0.3
        )
        # Check if search query is formatted correctly
        if search_query.lower().find("query:") > -1:
            search_query = search_query.lower().split("query:")[1].replace('"', "")
            if record:
                # Update search history and save
                self.search_history.append(search_query)
                if len(self.search_history) > MAX_HISTORY_LENGTH:
                    for _ in range(len(self.search_history) - MAX_HISTORY_LENGTH):
                        self.search_history.pop(0) # remove oldest search
                if self._save:
                    self.browser.save_data("search_history", self.search_history)
            # Extract query
            return search_query
        
    # Generate search query and return results from post info
    def post_search(self, messages:List[str]):
        search_query = self.get_query(messages)
        # Check if search query is formatted correctly
        if search_query:
            # Search from found post info, in order of importance (highest to lowest)
            return self.process_web_search(
                phrases=[search_query],
                query_chars=100
                )
        else:
            return ""
