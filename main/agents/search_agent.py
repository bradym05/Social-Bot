# Dependencies
from main.web import Browser
from main.llm import BaseLLM
from main.agents.base_agent import BaseAgent
from typing import List

# SETTINGS
QUERY_INPUT = """
You will be given information from an instagram post.\n
Generate a standalone search query to find relevant information. You output your search query in this format:\n
    Query: [YOUR SEARCH QUERY] \n

Here are some examples:
    [INPUT]
    POST CAPTION: The best open world games
    IMAGE DESCRIPTION: A man standing in front of the distant moon at night
    POST COMMENTS: Tlou and Uncharted???, Cyberpunk > Elden Ring, This gotta be bait, This list is… rly fuckin bad.

    [YOUR OUTPUT]
    Query: "What is the best open world game"
    \n
    [INPUT]
    POST CAPTION: LEAVE JOE ALONE HES BEEN THROUGH ENOUGH ALREADY 😫😭😤🦧
    IMAGE DESCRIPTION: An illustration of a plane with cartoon characters in the seats
    POST COMMENTS: WE RIDE AT DAWN!!, Let’s go save Joe. Who’s with me button —>, He’s just a baby 😭

    [YOUR OUTPUT]
    Query: "Who is Joe from the plane?"
    \n
    [INPUT]
    POST CAPTION: That’s enchanted with stick drift II 😭
    IMAGE DESCRIPTION: A picture of a console wrapped in plastic with a controller on top
    POST COMMENTS: Only a monster could do this, I do this everyday at work, When you find some good ass armor but it has curse of binding on it

    [YOUR OUTPUT]
    Query: "What is stick drift on consoles"
    \n
    [INPUT]
    POST CAPTION: 40 video games releasing in 2026 🎮
    IMAGE DESCRIPTION: A picture of a grid of game logos
    POST COMMENTS: Fable oh how I've missed you 😍, And I got money for none of em, Fable?!?!?!😍, You’re forgetting subnautica 2

    [YOUR OUTPUT]
    Query: "What is the game Fable about"
    \n
"""

# Declare search browser agent class
class SearchAgent(BaseAgent):
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
    
    # Generate search query and return results from post info
    def post_search(self, messages:List[str]):
        # Initialize messages for search query
        query_messages = messages.copy()
        query_messages.append("[YOUR OUTPUT]:\nQuery: [YOUR SEARCH QUERY]")
        # Generate query from post information
        search_query = self.llm.get_response(
            instructions=QUERY_INPUT,
            messages=query_messages
        )
        # Check if search query is formatted correctly
        if search_query.lower().find("query:") > -1:
            # Extract query
            search_query = search_query.lower().split("query:")[1].replace('"', "")
            # Search from found post info, in order of importance (highest to lowest)
            return self.process_web_search(
                phrases=[search_query],
                query_chars=100
                )
        else:
            return ""
        