# Dependencies
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.virtual_authenticator import VirtualAuthenticatorOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from main.web.socials import BaseSocial, Instagram
from main.inputs import Typer
from typing import Dict

import time
import random
import atexit

# SETTINGS
DEFAULT_DRIVER_PATH = "D:\\brady\\Automation\\Social-Bot\\operadriver_win64\\operadriver_win64\\operadriver.exe"

# Declare browser class
class Browser:
    # Initialize object
    def __init__(
        self,
        credentials:Dict['username':str, 'password':str],
        platform:BaseSocial=Instagram,
        ):
        # Initialize variables
        self.driver = webdriver.Chrome()
        self.typer = Typer(type_callback=self.on_type)
        self.platform = platform
        self.credentials = credentials
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
        username = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
        password = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
        # Type in login credentials
        self.typer.type_query(self.credentials['username'], username)
        self.typer.type_query(self.credentials['password'], password)
        # Submit after filling out fields
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()
    # Scroll through feed, return array of posts
    def feed_step(self, post_count:int=6):
        # Check current page
        if self.driver.current_url == self.platform.login_url:
            # Find and click feed button
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, self.platform.feed_button))).click()
        elif str(self.driver.current_url) != self.platform.feed_url:
            # Go straight to feed
            self.driver.get(self.platform.feed_url)
        else:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
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
    def open_post(self, post_anchor:webdriver.remote.webelement.WebElement, new_tab:bool=False):
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
    # Describe the given post
    def describe_post(self, post_anchor) -> str | None:
        # Get _aagv class
        post_info = post_anchor.find_element(by=By.CLASS_NAME, value="_aagv")
        # Validate
        if post_info:
            # Get image info from _aagv class
            image_info = post_info.find_element(by=By.TAG_NAME, value="img")
            # Validate
            if image_info:
                # Get and return image description
                return image_info.get_attribute("alt")
    # Like the given post
    def like_post(self, post_anchor):
        # Random delay
        time.sleep(random.random()/10)
        # Open post
        self.open_post(post_anchor=post_anchor, new_tab=True)
        # Find like button
        like_button = WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.CLASS_NAME, self.platform.like_button)))
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