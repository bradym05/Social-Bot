# Dependencies
from main.llm import SocialMediaLLM
from main.web import SaveBrowser
from main.agents import SocialAgent

import time

# Create browser
browser = SaveBrowser(
    credentials={
        'username':"YOUR USERNAME HERE",
        'password':"YOUR PASSWORD HERE"
    },
)
print("Browser created. Logging in...")

# First, login
loginSuccess = browser.login()
if loginSuccess:

    # Wait a few seconds for page to load
    time.sleep(5)

    # Return to the Instagram home page
    browser.driver.get("https://www.instagram.com/")

    # DEFINE LLM INSTRUCTIONS
    SAMPLES = """
    Post: Posted by @musichub, new song  released.
    Interest: 100%
    Comment: "This is great!"
    \n
    Post: Posted by @funnymemes, video of three men sharing gum. Everyone asks for gum, and a dog follows placing his paw on the gum package. The people say, "What the dog doin?"
    Interest: 5%
    Comment: "Weird"
    \n
    Post: Posted by @politics, news about the presidential debate.
    Interest: 0%
    Comment: "I don't listen to politics"
    \n
    Post: Posted by @spotifydaily, new album release from Taylor Swift.
    Interest: 80%
    Comment: "One day my music will be this good."
    \n
    """
    INTERESTS = ["Music", "Singing", "Art", "Food"]
    GOALS = ["Grow social media following", "Promote music", "Support other arts", "Make money"]
    GRAMMAR_INSTRUCTIONS = "You are respectful. You do not bring other people down. You do not swear."
    SLANG = ["*lol: Laughing out loud",] # The slang is marked by *, followed by the definition

    # Create LLM
    SINGER_LLM = SocialMediaLLM(
        role="singer",
        name="Jane Doe",
        platform="Instagram",
        platform_usage="promote your music",
        interests=INTERESTS,
        goals=GOALS,
        grammar_instructions=GRAMMAR_INSTRUCTIONS,
        sample_responses=SAMPLES,
        slang=SLANG
        )
    print("LLM created")

    # Create social browser agent
    agent = SocialAgent(browser=browser, llm=SINGER_LLM)
    print("Agent created")

    # Run until close
    while True == True:
        print("NEW PROCESS")
        agent.process()
        time.sleep(2)