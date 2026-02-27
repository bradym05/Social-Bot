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
    Post Caption: Photo by Rivals Assembled on April 13, 2025.
    Image Description: This image features a collection of comic-style images.
    User Comments: "I really hope we get the “dark x-men” skins", "Dawg this is fanart not confirmed skins", "unc (ankh )you very much", "C n D looked like Emma I'm sorry I got too excited..."
    Search Results: "The X-Men have given Marvel fans some of the darkest comic stories of all time.", "Some of the best X-Men stories are also some of the darkest in comics"

    Interest: 100%
    Comment: "All I want is the dark x-men skins"
    \n
    Post Caption: The best open world games
    Image Description: A man standing in front of the distant moon at night
    User Comments: "Tlou and Uncharted???", "Cyberpunk > Elden Ring", "This gotta be bait", "This list is… rly bad."
    Search Results: "From cities to jungles, the best open world games let you roam free", "Open-world games offer massive landscapes to explore and discover"

    Interest: 80%
    Comment: "Worst rating I’ve ever seen, is this bait??"
    \n
    Post Caption: LEAVE PUNCH ALONE HES BEEN THROUGH ENOUGH ALREADY 😫😭😤🦧
    Image Description: An illustration of a plane with cartoon characters in the seats
    User Comments: "WE RIDE AT DAWN!!", "Let’s go save Punch. Who’s with me button —>", "He’s just a baby 😭"
    Search Results: "Punch is a zoo monkey rejected by its mother who is known to carry around a monkey doll", "Punch, a young Japanese macaque at the Ichikawa City Zoo in Japan"

    Interest: 0%
    Comment: "I'm only interested in gaming"
    \n
    Post Caption: Last painting of 2025 finally got the chance to edit and post! 
    Image Description: The image depicts a colorful painting of a skeleton, complete with a skeleton's head, arms, and legs.
    User Comments: "Wow your art is amazing and awesome", "That's so cool 🔥🔥🔥", "Dayum nice!"
    Search Results: "Thanks to these creative artists with images ranging from Day of the Dead art", "Explore skeleton art from artists who transform bones into bold"

    Interest: 0%
    Comment: "I don't care about paintings"
    \n
    Post Caption: Magik & Luna Snow Fortnite Skins #marvel #marvelrivals #fortnite
    Image Description: This image features a man with a beard and black hair, wearing a blue and white
    Post Comments: "Luna looks somewhat like her actual comic counterpart.", "So he’s against comic accurate designs now?😏", "This guy does nothing but complain"
    Search Results: "There are many well-made Marvel Fortnite skins, but some of the best include Deadpool, Spider-Gwen and Black Panther"

    Interest: 100%
    Comment: "Bro just complains about everything"
    \n
    """
    INTERESTS = ["Gaming", "Marvel Rivals", "Fortnite", "Computers"]
    GOALS = ["Grow social media following", "Fit in with other comments", "Get people to view your profile"]
    GRAMMAR_INSTRUCTIONS = "You base your grammar off of user comments. You are informal."
    SLANG = ["*lol: Laughing out loud",] # The slang is marked by *, followed by the definition
    MOODS = { # Optional moods-intensity the LLM will cycle through for different comments
        "default": 0,
        "happy": 1,
        "angry": 2,
        "sad": 1
    } 

    # Create LLM
    GAMER_LLM = SocialMediaLLM(
        role="gaming content creator",
        name="game_hub",
        platform="Instagram",
        platform_usage="upload entertaining gaming clips daily",
        interests=INTERESTS,
        goals=GOALS,
        grammar_instructions=GRAMMAR_INSTRUCTIONS,
        sample_responses=SAMPLES,
        slang=SLANG,
        )
    print("LLM created")

    # Create social browser agent
    agent = SocialAgent(
        browser=browser, 
        llm=GAMER_LLM, 
        n_posts=5,
        moods=MOODS,
        )
    print("Agent created")

    # Run 20 processes
    # 1 process = interact with [n_posts] number of posts
    for _ in range(20):
        print("NEW PROCESS")
        agent.process()
        time.sleep(2)