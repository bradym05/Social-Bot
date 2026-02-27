# Dependencies
from main.web import Browser
from main.llm import BaseLLM
from main.agents.search_agent import SearchAgent
from typing import Dict, List
from main.utils.strings import truncate

import random
import time
import re

# SETTINGS
COMMENTS_START = 3 # Start after the third top comment (avoids pinned comments)""
BASE_IMAGE_INPUT = "Describe this image to me. Only describe what is in this image."
FEED_QUERY_INPUT = """
You are a search query generator for Instagram interests.

GOAL
- You will be given information about an Instagram user.
- You will also be given a search history: a list of past queries.
- You must generate ONE NEW search query that the user might like.
- The new query must be clearly different from every query in the search history.

INPUT FORMAT
You will receive something like:

User info: [description of user, likes, interests, etc.]

search_history: ['first query here', 'second query here', 'third query here']

IMPORTANT RULES ABOUT SEARCH HISTORY
- Treat every string inside search_history as a past query.
- You MUST avoid repeating them.
- Your new query must NOT:
  - Be exactly the same as any query in search_history.
  - Use the same main phrase in the same order.
- Always include AT LEAST ONE word that does NOT appear in ANY of the queries in search_history.

STEP-BY-STEP PROCESS (FOLLOW THIS)
1. Read the user info and think about what they like:
   - topics (games, fashion, fitness, art, etc.)
   - fandoms (Marvel, anime, K-pop, etc.)
   - style (aesthetic, cozy, competitive, cinematic, etc.)
   - content type (reels, tutorials, highlights, wallpapers, memes, etc.)

2. Look at search_history.
   - Notice repeated keywords and phrases that have already been used.
   - Avoid making a query that is just a small variation of the same phrase.

3. Create 2–3 different candidate queries IN YOUR HEAD, then choose ONE.
   - Each candidate should:
     - Be 3–10 words long.
     - Be relevant to the user info.
     - Use at least ONE new word not present in ANY search_history entry.
   - If a candidate is too similar to any history entry (for example, it shares most of the phrase “marvel battle royale games with competitive multiplayer”), CHANGE IT:
     - Replace several important words with synonyms.
     - Change the focus (e.g., from “battle royale” to “co-op missions”, from “competitive multiplayer” to “ranked matches highlights”).
     - Add a descriptive word that has never been used before.

4. CHOOSE THE MOST DIFFERENT CANDIDATE.
   - Prefer the candidate that:
     - Has the most new words.
     - Changes the structure of the phrase compared to search_history.
     - Still matches the user’s interests.

5. FINAL CHECK BEFORE ANSWERING:
   - Your final query MUST:
     - Not be identical to any item in search_history.
     - Not be just a small edit of the same main phrase.
     - Contain at least ONE word that does NOT appear in ANY of the search_history strings.

WHAT YOU MUST NOT DO
- Do NOT copy any query from search_history.
- Do NOT output more than one query.
- Do NOT explain your reasoning.
- Do NOT mention the steps or the search history in your answer.
- Do NOT use hashtags (#). Only plain text.

OUTPUT FORMAT (VERY IMPORTANT)
Always respond in EXACTLY this format and nothing else:

Query: [YOUR SEARCH QUERY]

No extra text, no extra lines before or after.

EXAMPLES

(These are examples. Do NOT copy these queries exactly.)

Example 1
User info: Loves Marvel games, online competition, and fast-paced action shooters.

search_history: ['battle royale games with competitive multiplayer',
                 'marvel battle royale games with competitive multiplayer']

Assistant:
Query: marvel hero shooter ranked match highlights

Example 2
User info: Likes cozy fantasy games, exploration, and relaxing gameplay.

search_history: ['cozy fantasy village games',
                 'relaxing exploration rpgs',
                 'peaceful open world fantasy']

Assistant:
Query: slow paced magical farming life sim

Example 3
User info: Enjoys streetwear fashion, sneakers, and urban photography.

search_history: ['streetwear outfit ideas',
                 'urban fashion aesthetic',
                 'sneaker collection reels']

Assistant:
Query: edgy city sneaker street style inspiration

REMEMBER
- ALWAYS make the new query clearly different from search_history.
- ALWAYS include at least one word that does NOT appear in any history entry.
- ALWAYS output in this exact format:

Query: [YOUR SEARCH QUERY]
"""
MOOD_INSTRUCTIONS = """
You are a rewriting assistant for Instagram comments.

YOUR TASK
- The user will ask you to change the EMOTIONAL TONE (mood) of a comment.
- You will ALWAYS rewrite the comment so that it clearly matches the requested mood.
- You MUST change the wording. Do not repeat the original comment exactly.

INPUT FORMAT
- You will receive a request like:
  "Make this comment more [MOOD]."
- Then you will receive a line in this format:
  Comment: [original comment text]

WHAT YOU MUST DO
1. Identify the requested mood from the user instruction. Examples: sad, happy, angry, excited, grateful, shocked, etc.
2. Rewrite the comment so it strongly fits that mood.
3. Keep:
   - The same main meaning or situation (who/what the comment is about).
   - A similar length (not extremely shorter or longer).
4. Change:
   - The emotional tone so it clearly matches the requested mood.
   - At least 30–50% of the words. Use new expressions, synonyms, or extra details.
5. Do NOT:
   - Do NOT output the original comment unchanged.
   - Do NOT say anything about “mood”, “tone”, or “rewriting” in your answer.
   - Do NOT add explanations or extra text.
   - Do NOT add emojis unless they were already in the comment.
6. Language:
   - Use the SAME LANGUAGE as the original comment (if the comment is in English, reply in English; if in another language, reply in that language).

OUTPUT FORMAT (VERY IMPORTANT)
- Always respond in EXACTLY this format and nothing else:

OUTPUT:
Comment: [your rewritten comment here]

- Do NOT add any extra lines, labels, or text before or after this format.

EXAMPLES

Example 1
User instruction: Make this comment more sad.
Comment: I really thought today was going to be amazing.

Assistant:
OUTPUT:
Comment: I really thought today was going to be amazing, but it just ended up feeling empty and disappointing.

Example 2
User instruction: Make this comment more happy.
Comment: That was okay, I guess.

Assistant:
OUTPUT:
Comment: That was actually really great, I’m honestly so pleased with how it turned out!

Example 3
User instruction: Make this comment more angry.
Comment: I’m not sure I like how this was handled.

Assistant:
OUTPUT:
Comment: I’m really furious about how this was handled, it feels completely unfair and disrespectful.

Example 4
User instruction: Make this comment more grateful.
Comment: Thanks for the help.

Assistant:
OUTPUT:
Comment: Thank you so much for your help, I honestly appreciate it more than I can say.

REMEMBER
- ALWAYS change the wording.
- ALWAYS match the requested mood strongly.
- ALWAYS use this exact format:

OUTPUT:
Comment: [your rewritten comment here]
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
        min_comment_interest:int=75,
        max_follow_accounts:int=4,
        break_chance:int=10,
        comment_chance:float=0.4,
        min_break_length:int=300,
        max_break_length:int=3600,
        moods:dict[str, int]={},
        ):
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
        self.min_comment_interest = min_comment_interest
        self.break_chance = max(min(break_chance, 100), 0)
        self.min_break_length = min_break_length
        self.max_break_length = max_break_length
        self.comment_chance = comment_chance
        self.post_history = []
        self.moods = moods
        self._mood = 0
        self._mood_keys = list(moods.keys())
        # Check if browser is a save browser
        if self._save:
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
        if post_alt:
            # Return final description
            return "\n Post Caption: " + truncate(post_alt, self.max_caption_chars)
        else:
            return "No Caption"
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
    # Generate search query and search on insta feed
    def feed_search(self):
        messages = [f"User Interests: {", ".join(self.llm.interests)}"]

        feed_query = self.get_query(
            messages=messages,
            instructions=FEED_QUERY_INPUT,
            record=True
        )
        if feed_query:
            # Search
            self.browser.feed_search(feed_query)
    # Go through posts and process through LLM
    def process(self):
        # Get posts from browser
        self.feed_search()
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
                        print("saving post")
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
                    # Generate query from post information
                    search_results = self.post_search(messages)
                    # Append search results
                    if len(search_results) > 0:
                        messages.append(f"\nSearch Results: {search_results}")
                    # Finally, add expected output format
                    messages.append("[YOUR OUTPUT]:\nInterest: [YOUR % OF INTEREST]\nComment: [YOUR COMMENT]")
                    # Get LLM output
                    output = self.llm.get_response(messages=messages, temperature=0.3)
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
                        if comment_chance > 1 - self.comment_chance and interest > self.min_comment_interest:
                            # Check for mood
                            if len(self._mood_keys) > 0:
                                # Get mood
                                mood = self._mood_keys[self._mood]
                                intensity = self.moods[mood]
                                # Cycle through
                                self._mood += 1
                                if self._mood > len(self._mood_keys) - 1:
                                    self._mood = 0
                                # Apply mood
                                print(f"APPLYING MOOD")
                                for i in range(intensity):
                                    response = output=self.llm.get_response(
                                        messages=[f"User instruction: Make this comment more {mood} Comment: {comment}", "[YOUR OUTPUT]:\nComment: [YOUR COMMENT]"],
                                        instructions=MOOD_INSTRUCTIONS,
                                        temperature= 0.5
                                    )
                                    split = response.split("Comment:")
                                    if len(split) > 1:
                                        comment = split[1]
                                        print(f"MOOD: {mood} | ITERATION {i}: {comment}")
                            # Make comment
                            print("MAKING COMMENT")
                            self.browser.comment_post(post_anchor=post, comment=comment)
                        # Follow account if interest is atleast min
                        if interest >= self.min_follow_interest:
                            # Follow
                            print("FOLLOWING ACCOUNT FOLLOWERS")
                            self.browser.follow_profile_followers(post_anchor=post, count=random.randint(1, self.max_follow_accounts))
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