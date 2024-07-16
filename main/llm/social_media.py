# Dependencies
from main.llm import BaseLLM
from typing import List

# Declare social media LLM class
class SocialMediaLLM(BaseLLM):
    # Initialize
    def __init__(
        self, 
        role:str="Basketball Player",
        name:str="Lebron James",
        platform:str="Instagram",
        platform_usage:str="cure boredom",
        interests:List[str]=["Basketball", "Rap Music", "Family"],
        goals:List[str]=["Make funny comments", "Promote career"],
        grammar_instructions:str="",
        sample_responses:str="",
        chain_of_thought:str="",
        slang:List=[],
        max_tokens:int=128
        ):
        # Build instructions
        chat_instructions = f"You are the {role}, {name}. You are using {platform} to {platform_usage}\n"
        img_instructions = f"You perfectly describe key details of social media posts. You are using {platform} to {platform_usage}\n"
        # Check for interests
        if len(interests) > 0:
            # Append interests in list format
            interest_list = "Your interests are:\n"
            for interest in interests:
                interest_list += f"- {interest}\n"
            # Append to instructions
            chat_instructions += interest_list
            img_instructions += "You use your interests to pick out important features\n"
            img_instructions += interest_list
        # Check for goals
        if len(goals) > 0:
            chat_instructions += "Your goals are:\n"
            # Append goals in list format
            for goal in goals:
                chat_instructions += f"- {goal}\n"
        # Check for slang
        if len(slang) > 0:
            chat_instructions += "Your slang (slang marked by *) and their meanings (unmarked) are:\n"
            for pair in slang:
                chat_instructions += f"- {pair}\n"
        # Append other instructions if given
        chat_instructions += chain_of_thought if len(chain_of_thought) > 0 else ""
        chat_instructions += f"IMPORTANT COMMENT RULES: {grammar_instructions}\n" if len(grammar_instructions) > 0 else ""
        chat_instructions += f"Here are some samples:\n{sample_responses}" if len(sample_responses) > 0 else ""
        # Initialize from superclass
        super(SocialMediaLLM, self).__init__(
            chat_instructions=chat_instructions, 
            img_instructions=img_instructions,
            max_tokens=max_tokens,
            )