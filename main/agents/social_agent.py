# Dependencies
from main.web import Browser
from main.llm import BaseLLM
from main.agents.search_agent import SearchAgent
from typing import Dict
from main.utils.strings import truncate

import random
import time
import re

# SETTINGS
COMMENTS_START = 3 # Start after the third top comment (avoids pinned comments)""
BASE_IMAGE_INPUT = "Describe this image to me. Only describe what is in this image."
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

# Declare social media LLM browser agent class
class SocialAgent(SearchAgent):
    # Initialize object
    def __init__(
        self, 
        browser:Browser, 
        llm:BaseLLM, 
        max_search_chars:int=150,
        n_posts:int=5,
        min_comments:int=1,
        max_comments:int=10,
        max_total_comment_chars:int=300,
        max_caption_chars:int=150,
        max_description_chars:int=100,
        min_like_interest:int=50,
        min_follow_interest:int=80,
        max_follow_accounts:int=4,
        like_comment_interest:int=75,
        break_chance:int=10,
        comment_chance:float=0.8,
        min_break_length:int=300,
        max_break_length:int=3600):
        # Initialize from superclass
        super(SocialAgent, self).__init__(browser=browser, llm=llm, max_search_chars=max_search_chars)
        # Initialize variables
        self.n_posts = n_posts
        self.comment_start = (COMMENTS_START + (min_comments - 1))
        self.max_comments = max_comments
        self.max_total_comment_chars = max_total_comment_chars
        self.max_caption_chars = max_caption_chars
        self.max_description_chars = max_description_chars
        self.min_like_interest = min_like_interest
        self.min_follow_interest = min_follow_interest
        self.max_follow_accounts = max_follow_accounts
        self.like_comment_interest = like_comment_interest
        self.break_chance = max(min(break_chance, 100), 0)
        self.min_break_length = min_break_length
        self.max_break_length = max_break_length
        self.comment_chance = comment_chance
        self.post_history = []
        self._save = False
        # Check if browser is a save browser
        if getattr(self.browser, "custom_data", False):
            self._save = True
            self.post_history = self.browser.get_data("post_history") or []
    # Randomly take a break
    def random_break(self):
        # Check if random chance is within chosen chance
        break_chance = random.random()
        if break_chance <= self.break_chance/100:
            # Decide random break duration
            break_duration = random.randrange(self.min_break_length, self.max_break_length)
            # Indicate break started
            print(f"TAKING A BREAK FOR: {break_duration} seconds")
            # Exit platform
            original_url = self.browser.driver.current_url
            self.browser.driver.get("https://www.google.com")
            # Wait until break duration has passed
            time.sleep(break_duration)
            print(f"BREAK FINISHED")
            # Return to platform and wait 5 seconds extra (precaution)
            self.browser.driver.get(original_url)
            time.sleep(5)
    # Get post description from LLM
    def describe_post_image(self, post) -> str:
        # Get post image
        post_image = self.browser.get_post_image(post_anchor=post)
        # Check if post image was found
        if post_image:
            # Get image url
            image_url = post_image.get_attribute("src")
            # Validate url
            if image_url:
                # Get image description
                return "\nImage Description: " + truncate(self.llm.describe_image(image_url=image_url, message=BASE_IMAGE_INPUT), self.max_description_chars)
        # Return blank string by default
        return ""
    # Process post caption for LLM input
    def get_processed_caption(self, post) -> str:
        # Get post alt - on the explore page the alt text is the post's caption
        post_alt = self.browser.get_alt(post_anchor=post).strip()
        # Return final description
        return "\n Post Caption: " + truncate(post_alt, self.max_caption_chars)
    # Process post comments for LLM input
    def get_processed_comments(self, post) -> str:
        # Get comments
        all_comments = self.browser.get_comments(post_anchor=post)
        # Initialize variables
        comment_list = ""
        comment_count = 0
        # Ensure minimum number comments are present
        if len(all_comments) > self.comment_start:
            # Iterate over comments starting at minimum
            for comment in all_comments[self.comment_start:]:
                # Validate comment
                if len(comment) > 0:
                    # Update variables
                    comment_list += f'"{comment.strip()}", ' 
                    comment_count += 1
                    # Check if max characters or comment count has been exceeded
                    if len(comment_list) >= self.max_total_comment_chars or comment_count >= self.max_comments:
                        break
            # Check if any comments were found
            if len(comment_list) > 0:
                # Describe the current section
                comment_list = "\nUser Comments: " + comment_list
        # Return final result
        return comment_list
    # Extract interest and comment from LLM output
    def extract_values(self, output:str) -> Dict["comment":str, "interest":int]:
        # Initialize variables
        value_dict = {}
        # Iterate over lines
        for line in output.splitlines():
            # Check if line includes comment or interest
            if line.lower().find("comment") > -1:
                # Extract comment
                quotation_split = line.split(sep='"')
                if len(quotation_split) >= 3:
                    comment = quotation_split[-2]
                    if len(comment) > 0:
                        value_dict["comment"] = comment
            elif line.lower().find("interest") > -1:
                # Extract post interest
                post_interest = ""
                for char in line:
                    if char.isdigit():
                        post_interest += char
                    elif char == "%":
                        break
                # Validate post interest
                if len(post_interest) <= 3 and post_interest.isdigit():
                    value_dict["interest"] = int(post_interest)
            # Check if all values are found
            if "comment" in value_dict and "interest" in value_dict:
                break
        # Return final result
        return value_dict
    # Go through posts and process through LLM
    def process(self):
        # Get posts from browser
        selection = self.browser.feed_step()
        # Go through n selected posts
        for n in range(self.n_posts):
            # Make sure posts are available
            posts_available = len(selection)
            if posts_available > 0:
                # Get post and url
                post = selection.pop(random.randrange(0, posts_available - 1)) if posts_available - 1 > 1 else selection.pop()
                url = post.get_attribute("href")
                # Check if url has already been processed
                if url in self.post_history:
                    continue
                else:
                    # Update post history and save
                    self.post_history.append(url)
                    if self._save:
                        self.browser.save_data("post_history", self.post_history)
                    # Get post information
                    image_description = self.describe_post_image(post=post)
                    processed_description = self.get_processed_caption(post=post)
                    processed_comments = self.get_processed_comments(post=post)
                    # Initialize variables
                    messages=[
                            processed_description,
                            image_description[:100],
                            processed_comments,
                            ]
                    # Initialize messages for search query
                    query_messages = messages.copy()
                    query_messages.append("[YOUR OUTPUT]:\nQuery: [YOUR SEARCH QUERY]")
                    # Generate query from post information
                    search_query = self.llm.get_response(
                        instructions=QUERY_INPUT,
                        messages=query_messages
                    )
                    print(search_query)
                    # Check if search query is formatted correctly
                    if search_query.lower().find("query:") > -1:
                        # Extract query
                        search_query = search_query.lower().split("query:")[1].replace('"', "")
                        # Search from found post info, in order of importance (highest to lowest)
                        search_results = self.process_web_search(
                            phrases=[search_query],
                            query_chars=100
                            )
                    else:
                        search_results = ""
                    # Append search results
                    if len(search_results) > 0:
                        messages.append(f"\nSearch Results: {search_results}")
                    # Finally, add expected output format
                    messages.append("[YOUR OUTPUT]:\nInterest: [YOUR % OF INTEREST]\nComment: [YOUR COMMENT]")
                    # Get LLM output
                    output = self.llm.get_response(messages=messages)
                    print(f"-------------------- LLM INPUT --------------------\n{messages}\n-------------------- LLM OUTPUT --------------------\n{output}")
                    # Extract output values and validate
                    output_values = self.extract_values(output=output)
                    if "interest" in output_values and "comment" in output_values:
                        # Scroll to the final slide before continuing
                        self.browser.scroll_post(post_anchor=post)
                        # Initialize variables
                        interest, comment = output_values["interest"], output_values["comment"]
                        print(f"INTEREST: {interest}% | COMMENT: {comment}")
                        # Check if interest meets like interest
                        if interest >= self.min_like_interest:
                            # Like the post
                            print("LIKING POST")
                            self.browser.like_post(post_anchor=post)
                            # Wait before proceeding
                            time.sleep(1 * random.random())
                        # Comment based on random chance (and like interest)
                        comment_chance = random.random()
                        if comment_chance > 1 - self.comment_chance and interest > self.like_comment_interest:
                            # Make comment
                            print("MAKING COMMENT")
                            self.browser.comment_post(post_anchor=post, comment=comment)
                        # Follow account if interest is atleast 90%
                        if interest >= self.min_follow_interest:
                            # Follow
                            print("FOLLOWING ACCOUNT")
                            self.browser.follow_profile(post_anchor=post)
                    # Wait on post
                    time.sleep((1 + random.random()) * (2 + random.random()))
                    # Close post
                    self.browser.close_post()
                    # Wait after closing
                    time.sleep(1 + random.random())
            else:
                break
        # Randomly break after process is completed
        self.random_break()