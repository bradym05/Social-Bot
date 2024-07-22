# Dependencies
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.virtual_authenticator import VirtualAuthenticatorOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from main.web.socials import BaseSocial, Instagram
from main.inputs import Typer
from typing import Dict, List, Optional

import time
import random
import atexit

# Declare browser class
class Browser:
    # Initialize object
    def __init__(
        self,
        credentials:Dict['username':str, 'password':str],
        platform:BaseSocial=Instagram,
        timeout_exit:bool=True,
        timeout_callback:Optional[callable]=False
        ):
        # Initialize variables
        self.driver = webdriver.Chrome()
        self.driver.delete_all_cookies()
        self.typer = Typer(type_callback=self.on_type)
        self.platform = platform
        self.credentials = credentials
        self.timeout_exit = timeout_exit
        self.timeout_callback = timeout_callback
        # Setup virtual authenticator
        self.driver.add_virtual_authenticator(
            VirtualAuthenticatorOptions()
        )
        # Set implied wait time
        self.driver.implicitly_wait(10)
        # Close on exit
        atexit.register(self._close)
    # Close connection on exit
    def _close(self):
        self.driver.quit()
    # Callback on driver timeout exception
    def _on_timeout(self, e):
        # Output timeout error
        print('\033[1m' + "TIMEOUT EXCEPTION" + '\033[0m')
        print(str(e))
        # Check for timeout callback
        if getattr(self, "timeout_callback", False):
            self.timeout_callback()
        # Check if exit on timeout is enabled
        if self.timeout_exit:
            # Exit program
            exit()
    # Callback for typer
    def on_type(self, query:str, character:str, element:EC.WebElement):
        if character == "":
            element.send_keys(Keys.BACKSPACE)
        else:
            element.send_keys(character)
    # Get requested site and login
    def login(self):
        # Load site
        self.driver.get(self.platform.login_url)
        # Get input fields
        try:
            username = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
            password = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
        except TimeoutException as e:
            self._on_timeout(e)
        # Type in login credentials
        self.typer.type_query(self.credentials['username'], username)
        self.typer.type_query(self.credentials['password'], password)
        # Submit after filling out fields
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
        except TimeoutException as e:
            self._on_timeout(e)
    # Search the web for the given query, returns top sites
    def search_web(self, query:str) -> Dict[str, str]:
        final_results = {}
        # Validate query
        if len(query) > 0:
            # Get original tab
            original_tab = self.driver.current_window_handle
            # Open new tab and go to google
            self.driver.switch_to.new_window('tab')
            self.driver.get("https://www.google.com")
            # Find search bar
            try:
                search_bar = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, "q")))
            except TimeoutException as e:
                self._on_timeout(e)
            # Wait randomly
            time.sleep(random.random())
            search_bar.click()
            time.sleep(random.random())
            # Type search query
            lines = query.splitlines()
            typed = ""
            if len(lines) == 0:
                lines = [query]
            for l in lines:
                for char in l.strip():
                    if (char.isalnum() and char.isascii) or char == " ":
                        typed += char
                        try:
                            search_bar.send_keys(char)
                        except:
                            continue
            # Validate typed query
            if len(typed) > 0:
                # Wait randomly
                time.sleep(random.random())
                # Search and get result container
                search_bar.submit()
                try:
                    results_container = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, "search")))
                    results_container = WebDriverWait(results_container, 10).until(EC.visibility_of_element_located((By.ID, "rso")))
                except TimeoutException as e:
                    self._on_timeout(e)
                # Get results from container
                all_results = results_container.find_elements(By.TAG_NAME, "div")
                # Iterate over all results
                for result in all_results:
                    # Get inner result and find last child
                    last_child = result.get_property("lastChild")
                    if last_child and type(last_child) == WebElement:
                        # Get heading from last child's inner text
                        heading = last_child.get_property("innerText")
                        if heading:
                            heading = heading.splitlines()[0]
                            # Get URL from href attribute
                            url = last_child.get_attribute("href")
                            if url:
                                # Reference
                                final_results[heading] = url
            # Close search tab
            self.driver.close()
            self.driver.switch_to.window(original_tab)
        # Return final results
        return final_results
    # Scroll through feed, return array of posts
    def feed_step(self, post_count:int=6) -> List[WebElement]:
        # Check current page
        if self.driver.current_url == self.platform.login_url:
            # Find and click feed button
            try:
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, self.platform.feed_button))).click()
            except TimeoutException as e:
                self._on_timeout(e)
        elif str(self.driver.current_url) != self.platform.feed_url:
            # Go straight to feed
            self.driver.get(self.platform.feed_url)
        else:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2 + random.random())
        # Initialize variables
        selected_posts = []
        post_anchors = []
        # Find post anchors
        while len(post_anchors) == 0:
            time.sleep(random.random()/10)
            post_anchors = self.driver.find_elements(by=By.TAG_NAME, value="a")
            post_anchors = [[anchor, anchor.get_attribute("href")] for anchor in post_anchors]
            post_anchors = [anchor[0] for anchor in post_anchors if anchor[1].startswith("https://www.instagram.com/p/")]
        # Validate post count
        if len(post_anchors) >= post_count:
            # Select posts randomly
            for _ in range(post_count):
                # Append random anchor, remove from list of anchors
                i = random.randrange(0, len(post_anchors) - 1)
                selected_posts.append(post_anchors.pop(i))
        else:
            selected_posts = post_anchors
        # Return selected posts
        return selected_posts
    # Open the given post
    def open_post(self, post_anchor:WebElement, new_tab:bool=True):
        # Get currently opened post
        current_post = getattr(self, "_current_post", False)
        # Check if open already
        if current_post and current_post == post_anchor:
            return
        else:
            # Check for current post
            if current_post:
                # Close existing post
                self.close_post()
            # Random delay
            time.sleep(random.random()/10)
            # Update current post
            self._current_post = post_anchor
            self._new_tab = new_tab
            # Get post url
            post_url = post_anchor.get_attribute("href")
            # Open new tab or open on current page
            if new_tab == True:
                # Open post link
                self.driver.switch_to.new_window('tab')
                self.driver.get(post_url)
            else:
                # Click the post
                post_anchor.click()
            # Update post url
            self._post_url = str(post_url)
    # Close current post
    def close_post(self):
        # Check if post is open
        post = getattr(self, "_current_post", False)
        if getattr(self, "_new_tab", False):
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        elif post:
            pass
        # Reset variables
        self._current_post = None
        self._new_tab = None
        self._post_url = None
    # Get post image
    def get_post_image(self, post_anchor:WebElement) -> WebElement | None:
        # Get _aagv class
        try:
            post_info = WebDriverWait(post_anchor, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "_aagv")))
        except TimeoutException as e:
            self._on_timeout(e)
        # Validate
        if post_info:
            # Get image info from _aagv class
            image_info = post_info.find_element(by=By.TAG_NAME, value="img")
            # Return image info
            return image_info
    # Describe the given post
    def describe_post(self, post_anchor:WebElement) -> str | None:
        # Get image info
        image_info = self.get_post_image(post_anchor=post_anchor)
        # Validate image info
        if image_info:
            # Get and return image description
            return image_info.get_attribute("alt")
    # Scroll to the end of a slides post
    def scroll_post(self, post_anchor:WebElement):
        # Open post
        self.open_post(post_anchor=post_anchor)
        # Find scroll button
        all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
        scroll_button = False
        for button in all_buttons:
            if button.get_attribute("aria-label") == "Next":
                scroll_button = button
                break
        if scroll_button:
            # Scroll to the last slide
            while True:
                time.sleep(1 + (2 * random.random()))
                try:
                    scroll_button.click()
                except StaleElementReferenceException:
                    break
    # Like the given post
    def like_post(self, post_anchor:WebElement):
        # Open post
        self.open_post(post_anchor=post_anchor, new_tab=True)
        # Find like button
        try:
            like_button = WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CLASS_NAME, self.platform.like_button)))
        except TimeoutException as e:
            self._on_timeout(e)
        like_button = like_button.find_element(by=By.TAG_NAME, value="div").find_element(by=By.TAG_NAME, value="div")
        # Check if button was found
        if like_button:
            # Random delay
            time.sleep(random.random()/5)
            # Hover on button
            like_button.click()
            # Random delay
            time.sleep(random.random()/20)
            # Press button
            like_button.click()
    # Get profile buttons of given post
    def get_profile_buttons(self, post_anchor:WebElement) -> List[WebElement]:
        # Open post
        self.open_post(post_anchor=post_anchor, new_tab=True)
        # Find comment section
        try:
            comment_section = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "x4h1yfo")))
        except TimeoutException as e:
            self._on_timeout(e)
        comment_section = comment_section.find_element(by=By.CLASS_NAME, value=str(self.platform.comments))
        # Get post profile from comment section
        post_profile = comment_section.find_element(by=By.CLASS_NAME, value="xyinxu5")
        # Get buttons from post profile
        try:
            profile_buttons = WebDriverWait(comment_section, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "x1i10hfl")))
        except TimeoutException as e:
            self._on_timeout(e)
        # Return results
        return profile_buttons
    # Follow the account who posted the given post
    def follow_profile(self, post_anchor:WebElement):
        # Get profile buttons
        profile_buttons = self.get_profile_buttons(post_anchor=post_anchor)
        # Find follow button
        follow_button = False
        for button in profile_buttons:
            if button.get_attribute("innerText") == "Follow":
                follow_button = button
                break
        # Check if follow button was found
        if follow_button:
            # Random delay
            time.sleep(random.random()/20)
            # Press follow button
            follow_button.click()
    # Open the profile of the account who posted the given post
    def open_profile(self, post_anchor:WebElement):
        # Get profile buttons
        profile_buttons = self.get_profile_buttons(post_anchor=post_anchor)
        # Find profile button
        page_button = False
        for button in profile_buttons:
            if button.get_attribute("innerText") != "Follow" and button.get_attribute("innerText") != "Following":
                page_button = button
                break
        # Check if profile button was found
        if page_button:
            # Random delay
            time.sleep(random.random()/20)
            # Press page button
            page_button.click()
            # Wait for page to load
            time.sleep(5)
    # Follow people who are followed by the currently opened profile
    def follow_profile_following(self, count:int=1):
        # Get account buttons
        try:
            account_buttons = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "x1i10hfl")))
        except TimeoutException as e:
            self._on_timeout(e)
        # Find following button
        following_button = False
        for button in account_buttons:
            inner_text = button.get_attribute("innerText")
            if inner_text and inner_text.find("following") > -1:
                following_button = button
                break
        # Check if following button was found
        if following_button:
            # Random delay
            time.sleep(random.random()/20)
            # Press following button
            following_button.click()
            # Wait until loaded
            time.sleep(1 + random.random())
            # Get list of accounts
            try:
                possible_divs = WebDriverWait(self.driver, 10).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, str(self.platform.popup))))
                popup_div = False
                for div in possible_divs:
                    inner_text = div.get_attribute("innerText")
                    leading_text = inner_text.splitlines()[0]
                    if leading_text == "Following":
                        popup_div = div
                        break
                if popup_div:
                    followers_container = WebDriverWait(popup_div, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "x7r02ix")))
                    account_containers = WebDriverWait(followers_container, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, str(self.platform.account))))
            except TimeoutException as e:
                self._on_timeout(e)
            # Get follow buttons from account containers
            follow_buttons = []
            for account in account_containers:
                button = account.find_element(by=By.TAG_NAME, value="button")
                if button.get_attribute("innerText") == "Follow":
                    follow_buttons.append(button)
            # Validate found buttons
            if len(follow_buttons) > 0:
                # Clamp count
                count = min(count, len(follow_buttons))
                # Follow the given number of accounts
                for i in range(count):
                    index = random.randrange(0, len(follow_buttons))
                    button = follow_buttons.pop(index)
                    # Wait random delay
                    time.sleep(random.random()/20)
                    # Click follow button
                    button.click()
    # Get all comments from the comment section of the given post
    def get_comments(self, post_anchor:WebElement) -> List[str]:
        # Open post
        self.open_post(post_anchor=post_anchor, new_tab=True)
        # Find comment section
        try:
            comment_section = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "x4h1yfo")))
        except TimeoutException as e:
            self._on_timeout(e)
        comment_section = comment_section.find_element(by=By.CLASS_NAME, value=str(self.platform.comments))
        combined_comments = comment_section.get_attribute("innerText")
        # Split comments by the Reply button
        combined_comments = combined_comments.split(sep="Reply")
        string_comments = []
        # Iterate over all comments
        for comment in combined_comments[1:]:
            # Split by lines
            main = comment.splitlines()
            # Iterate over each line
            for i, section in enumerate(main[:-1]):
                # Clean up and validate section
                section = section.strip()
                if len(section) > 1:
                    # Get important information
                    time_unit = section[-1]
                    first_digit = section[0]
                    # Check for comment date indicator
                    if first_digit.isdigit() and (time_unit == 'd' or time_unit == 'h' or time_unit == 'm' or time_unit == 'y'):
                        # Date indicator is right before comment, therefore the next line must be a comment
                        string_comments.append(main[i + 1])
                        break
        # Return final list of comments
        return string_comments
    # Comment on the given post
    def comment_post(self, post_anchor:WebElement, comment:str):
        # Open post
        self.open_post(post_anchor=post_anchor, new_tab=True)
        # Get comment section input field
        try:
            comment_input = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "form")))
        except TimeoutException as e:
            self._on_timeout(e)
        #comment_input = self.driver.find_element(by=By.TAG_NAME, value="form")
        comment_input.click()
        comment_input = comment_input and comment_input.find_element(by=By.TAG_NAME, value="textarea")
        # Validate comment input
        if comment_input:
            # Type in comment
            self.typer.type_query(comment, comment_input)
            # Submit after typing comment
            self.on_type(comment, Keys.ENTER, comment_input)
            # Wait after commenting
            time.sleep(4 + random.random())