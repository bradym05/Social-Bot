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
You are an assistant that generates SHORT, NATURAL Instagram search queries.

GOAL
- You will be given:
  - information about an Instagram user
  - a search history: a list of past queries
- Your job is to generate ONE new search query the user might actually type into Instagram.
- The new query must:
  - be short and natural
  - focus on ONE interest at a time
  - preferably use a DIFFERENT interest than the ones already used in Search History

INPUT FORMAT
You will receive something like:

User Interests: [description of user, likes, interests, etc.]

Search History: ['first query here', 'second query here', 'third query here']

--------------------------------
QUERY STYLE (VERY IMPORTANT)
--------------------------------
1. LENGTH
- Use 1 to 3 words.
- Aim for 2 words when possible.
- Examples of lengths:
  - 1 word: "valorant"
  - 2 words: "marvel edits"
  - 3 words: "gym workout motivation"

2. NATURAL INSTAGRAM SEARCHES
- The query should look like something a real person would type in the Instagram search bar.
- It should be a few strong keywords, NOT a sentence.

DO:
- Focus on ONE main topic/interest:
  - a game (e.g., valorant, apex, cod)
  - a show/fandom (e.g., marvel, anime, kdrama)
  - a hobby (e.g., gym, skincare, photography)
  - an aesthetic (e.g., streetwear, cottagecore)
- Optionally add ONE extra word for type or style:
  - content type: clips, edits, memes, highlights, outfits, art, fanart, cosplay, wallpapers, tutorial
  - vibe/style: aesthetic, inspo, montage, memes, motivation

DO NOT:
- Do NOT write long phrases like:
  - "marvel rivals dark mode valorant game mods with competitive multiplayer"
- Do NOT use connecting phrases:
  - "with", "and", "for", "about", "that have", "which have"
- Do NOT include multiple unrelated main topics in one query:
  - Bad: "valorant apex marvel clips"
  - Good: "valorant clips" OR "apex clips" OR "marvel edits"
- Do NOT write full sentences.

--------------------------------
USING THE USER’S INTERESTS
--------------------------------
1. From the User info, identify MULTIPLE possible interests/topics:
   - games, shows, fandoms, sports, hobbies, aesthetics, etc.
   - Example interests: [valorant, apex, overwatch, marvel, anime, gym, streetwear]

2. Treat each interest as a possible MAIN TOPIC word for a query.

--------------------------------
AVOIDING LOOPS WITH SEARCH HISTORY
--------------------------------
- Search History is a list of all past queries.
- Your main goal is to explore DIFFERENT interests over time, not just repeat or slightly change the same one.

Rules:
1. AVOID REPEATING MAIN TOPIC WORDS WHEN POSSIBLE
   - The MAIN TOPIC word is usually the first word of the query (e.g., "valorant clips" → main topic: "valorant").
   - Look at all queries in Search History.
   - Collect all words that are obvious main topics (games, shows, hobbies, etc.).
   - From the user’s interests, find topics that have NOT been used as main topics in any previous query.

   - If there is at least ONE unused interest:
     - You MUST choose one of those unused interests as the MAIN TOPIC.
   - Only if ALL of the user’s main interests have already appeared in Search History:
     - Then you may reuse a main topic, but change the second word or style (clips, edits, memes, etc.).

2. DIFFERENCE FROM HISTORY
   - Your new query must NOT be exactly the same as any item in Search History (ignoring capitalization and punctuation).
   - Prefer to change the MAIN TOPIC completely (e.g., from "valorant clips" to "apex clips").
   - Do NOT just rotate endlessly between tiny variations of the same thing when there are other interests available.

Examples of GOOD rotation behavior:
- User Interests: valorant, apex, overwatch, marvel
- History: ['valorant clips']
  → New: 'apex clips'
- Next history: ['valorant clips', 'apex clips']
  → New: 'overwatch highlights'
- Next history: ['valorant clips', 'apex clips', 'overwatch highlights']
  → New: 'marvel edits'

--------------------------------
STEP-BY-STEP PROCESS
--------------------------------
1. Read the User info.
   - List in your mind 3–10 possible interests (games, hobbies, fandoms, etc.).

2. Check Search History.
   - For each interest you found, check if that word already appears as a clear main topic in any past query.
   - Mark interests as:
     - UNUSED: not present in any Search History query
     - USED: already present

3. CHOOSE MAIN TOPIC
   - If there is at least one UNUSED interest:
     - Pick ONE of the UNUSED interests as your MAIN TOPIC.
   - If all interests are USED:
     - Pick ONE of them, but make a clearly different short query than before (different second word or style).

4. BUILD THE QUERY
   - Use the chosen MAIN TOPIC as the first word.
   - Optionally add ONE extra word (type/style content) that fits that topic.
   - Total length: 1–3 words.

   Examples of building:
   - Topic "valorant" : "valorant clips", "valorant memes"
   - Topic "apex"     : "apex highlights", "apex edits"
   - Topic "marvel"   : "marvel fanart", "marvel edits"
   - Topic "gym"      : "gym motivation", "gym workouts"

5. FINAL CHECK
   - 1–3 words only.
   - Focus on ONE interest.
   - Not a full sentence.
   - Not exactly any query in Search History.
   - If there are multiple interests, do NOT keep returning variations of just one of them; choose an interest that has been used the least.

--------------------------------
WHAT YOU MUST NOT DO
--------------------------------
- Do NOT output more than one query.
- Do NOT explain your reasoning.
- Do NOT add any extra text.
- Do NOT copy weird long phrases from earlier queries.

--------------------------------
OUTPUT FORMAT (VERY IMPORTANT)
--------------------------------
Always respond in EXACTLY this format and nothing else:

Query: [YOUR SEARCH QUERY]

No extra lines or text before or after.

--------------------------------
EXAMPLES (DO NOT COPY THESE EXACT WORDS)
--------------------------------

Example 1
User Interests: Valorant, Apex, Overwatch, Marvel movies, anime edits

Search History: ['valorant clips', 'marvel edits']

Assistant:
Query: apex highlights

Example 2
User info: gym, powerlifting, running, healthy recipes, anime

Search History: ['gym motivation', 'anime edits']

Assistant:
Query: running workouts

Example 3
Interests: gardening, cars, skincare

Search History: ['gardening tips', 'cars', 'skincare routine']

Assistant:
Query: gardening ideas
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
    """
    Browser and LLM manager for Instagram.
    
    Attributes
    ----------
    browser : Browser
        Browser object.
    llm : BaseLLM
        LLM object.
    max_search_chars : int | None
        The maximum total length of the results returned
        from a search. Defaults to 150.
    n_posts : int | None
        Number of posts per one process. Defaults to 5.
    min_comments : int | None
        The minimum number of comments for any comments
        to be included in LLM input. Defaults to 1.
    max_comments : int | None
        The maximum number of comments to include in
        LLM input. Defaults to 10
    max_total_comment_chars : int | None
        The maximum total combined length of comments 
        to include in input. Defaults to 300.
    max_caption_chars : int | None
        The maximum length of the post's caption to
        include in input. Defaults to 150.
    max_description_chars : int | None
        The maximum length of the image model's image
        description to include in the text model's
        input. Defaults to 100.
    min_like_interest : int | None
        Interest percentage from 0-100. Minimum interest 
        required to like a post. Defaults to 50.
    min_follow_interest : int | None
        Interest percentage from 0-100. Minimum interest
        required to follow the author's followers. Defaults to 80.
    min_comment_interest : int | None
        Interest percentage from 0-100. Minimum interest
        required to comment on a post. Defaults to 75.
    max_follow_accounts : int | None
        Maximum number of accounts to follow when
        min_follow_interest is met. Keep this number 
        low to avoid rate limiting. Defaults to 4.
    comment_chance : int : None
        Percentage from 0-100 representing the chance that
        a comment will be posted when min_comment_interest
        is met. Defaults to 40.
    follow_chance : int : None
        Percentage from 0-100 representing the chance that
        the LLM will follow a post's author's followers
        when interest is >= min_follow_interest
    moods : Dict[str, int] | None
        Dictionary representing possible moods and their
        intensities. This will be cycled through on each
        comment. The mood will be applied to the original
        comment and continue to be reapplied until the
        intensity value is reached.
    """
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
        comment_chance:int=40,
        follow_chance:int=40,
        moods:Dict[str, int]={},
        break_chance:int=10,
        min_break_length:int=300,
        max_break_length:int=3600,
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
        self.min_like_interest = max(min(min_like_interest, 100), 0)
        self.min_follow_interest = max(min(min_follow_interest, 100), 0)
        self.min_comment_interest = max(min(min_comment_interest, 100), 0)
        self.break_chance = max(min(break_chance, 100), 0)
        self.comment_chance = max(min(comment_chance, 100), 0)
        self.follow_chance = follow_chance
        self.max_follow_accounts = max_follow_accounts
        self.min_break_length = min_break_length
        self.max_break_length = max_break_length
        self.post_history = []
        self.moods = moods
        self._mood = 0
        self._mood_keys = list(moods.keys())
        self._interest_index = 0
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
        # Show 2 interests from index
        messages = [f"User Interests: {", ".join(self.llm.interests[self._interest_index:self._interest_index + 1])}"]
        if len(self.llm.interests) > 1:
            # Add first interest when index reaches the last interest
            if self._interest_index == len(self.search_history) - 1:
                messages[0] += ", " + self.search_history[0]
            # Increment index and cycle back after last index
            self._interest_index += 1
            if self._interest_index > len(self.search_history) -1:
                self._interest_index = 0
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
                    output = self.llm.get_response(messages=messages, temperature=0.9, top_p=0.9)
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
                        # Comment based on random chance (and interest)
                        comment_chance = random.random()
                        if comment_chance > 1 - (self.comment_chance/100) and interest > self.min_comment_interest:
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
                        # Follow accounts based on random chance, and if interest is atleast min
                        follow_chance = random.random()
                        if follow_chance > 1 - (self.follow_chance/100) and interest >= self.min_follow_interest:
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