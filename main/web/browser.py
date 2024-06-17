# Dependencies
from selenium import webdriver
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
        # Initialize variables
        selected_posts = []
        # Check current page
        if self.driver.current_url == self.platform.login_url:
            # Find and click feed button
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, self.platform.feed_button))).click()           
        elif self.driver.current_url != self.platform.feed_url:
            # Go straight to feed
            self.driver.get(self.platform.feed_url)
        # Find posts
        all_posts = WebDriverWait(self.driver, 10).until(EC.all_of((By.CLASS_NAME, "_aagv")))
        # Select random posts
        for post in all_posts:
            select_chance = random.random()
            if select_chance >= 0.5:
                selected_posts.append(post)
                if len(selected_posts) == post_count:
                    break
        return selected_posts