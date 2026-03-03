# Dependencies
from main.llm import BaseLLM
from typing import List

CHAIN_OF_THOUGHT = """
    For each post you see, you give the percentage of your interest in it, and you write a comment related to the post, in alignment with your instructions.\n
    1. You find key details in the post\n
    2. You determine your interest\n
    3. Make an original comment based on other comments and the post\n
    4. You output your percent interest and comment in this format:\n
        Interest: [YOUR % OF INTEREST] \n
        Comment: [YOUR COMMENT]\n
    """

# Declare social media LLM class
class SocialMediaLLM(BaseLLM):
    """
    LLM for use on Instagram
    
    Attributes
    ----------
    role : str | None
        What the user does/who they are.
    name : str | None
        Username or any other name.
    platform_usage : str | None
        Why the user is using Instagram.
    interests : List[str] | None
        What the user is interested in. This list will be used
        to generate search queries and decide what posts to interact
        with.
    goals : List[str] | None
        What the user hopes to get out of using Instagram.
    grammar_instructions : str | None
        Style/formatting instructions for the LLM.
    sample_responses : str | None
        Examples of how the LLM should respond. These should
        be formatted correctly if you want them to be effective.
    slang : List[str] | None
        A list of words with definitions. The word is marked by
        "*", followed by ":", followed by the definition. For
        example: "*lol: Laughing out loud"
    filtered_words : List[str] | None
        Words to be removed from responses (case insensitive)
    max_tokens : int | None
        LLM max tokens for both models. Defaults to 128.
    
    """
    # Initialize
    def __init__(
        self, 
        role:str="",
        name:str="",
        platform_usage:str="",
        interests:List[str]=[],
        goals:List[str]=[],
        grammar_instructions:str="",
        sample_responses:str="",
        slang:List=[],
        filtered_words:List[str]=[],
        max_tokens:int=128
        ):

        self.interests = interests
        # Build instructions
        chat_context = f"You are the {role}, {name}. You are using Instagram to {platform_usage}\n"
        img_instructions = f"You perfectly describe key details of social media posts. You are using Instagram to {platform_usage}\n"
        # Check for interests
        if len(interests) > 0:
            # Append interests in list format
            interest_list = "Your interests are:\n"
            for interest in interests:
                interest_list += f"- {interest}\n"
            # Append to instructions
            chat_context += interest_list
        # Check for goals
        if len(goals) > 0:
            chat_context += "Your goals are:\n"
            # Append goals in list format
            for goal in goals:
                chat_context += f"- {goal}\n"
        # Check for slang
        if len(slang) > 0:
            chat_context += "Your slang (slang marked by *) and their meanings (unmarked) are:\n"
            for pair in slang:
                chat_context += f"- {pair}\n"
        # Append other instructions if given
        chat_instructions = CHAIN_OF_THOUGHT
        chat_instructions += f"IMPORTANT COMMENT RULES: {grammar_instructions}\n" if len(grammar_instructions) > 0 else ""
        chat_instructions += f"Here are some samples:\n{sample_responses}" if len(sample_responses) > 0 else ""
        # Initialize from superclass
        super(SocialMediaLLM, self).__init__(
            chat_context=chat_context,
            chat_instructions=chat_instructions, 
            img_instructions=img_instructions,
            max_tokens=max_tokens,
            filtered_words=filtered_words
            )