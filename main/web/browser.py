# Dependencies
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.virtual_authenticator import VirtualAuthenticatorOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from main.inputs import Typer
from typing import List, Optional
from main.utils.chrome import no_indicators

import time
import random
import atexit
import urllib.parse as url_parse

# Settings
HOME_URL = "https://www.instagram.com/"
FEED_URL = HOME_URL + "explore/"
COOLDOWN_LENGTH = 86400

# Gets post info from the given browser and post
class PostInfo:

    # props
    comments: List[str]
    like_button: WebElement | None
    follow_button: WebElement | None
    comment_input: WebElement | None
    author: str | None
    profile: str | None

    # Get info using given browser
    def __init__(self, browser, post_anchor):
        # Initialize post info
        self.comments = []
        # Open post
        browser.open_post(post_anchor=post_anchor, new_tab=True)
        # Yield until comment form loads
        try:
            self.comment_input = WebDriverWait(browser.driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "form")))
        except TimeoutException as e:
            self.comment_input = None
        # Find all buttons
        all_buttons: List[WebElement] = browser.driver.find_elements(By.CSS_SELECTOR, "div[role='button']")
        for button in all_buttons:
            try:
                match button.accessible_name:
                    case "Reply": # Reply button only exists in comments
                        comment_div: WebElement = button.find_element(By.XPATH, "..")
                        if type(comment_div) == WebElement:
                            # Get lines
                            comment_lines = comment_div.find_element(By.XPATH, "..").text.splitlines()
                            # Comment SHOULD be on the 3rd line
                            if len(comment_lines) > 2 and comment_lines[2] != "Reply":
                                self.comments.append(comment_lines[2])
                    case "Comment": # Comment button only exists in post buttons div
                        # Post buttons *should* be located in the second parent element
                        post_button_div = button.find_element(By.XPATH, "../..")
                        # Iterate over all post buttons
                        for post_button in post_button_div.find_elements(By.CSS_SELECTOR, "div[role='button']"):
                            if post_button.accessible_name == "Like":
                                self.like_button = post_button
                                break
                    case "Follow":
                        self.follow_button = button
                        # Profile link *should* be located in the second parent element
                        post_header_div = button.find_element(By.XPATH, "../..")
                        post_author_link = post_header_div.find_element(By.CSS_SELECTOR, "a[role='link']")
                        # Iterate over all header buttons
                        self.author = post_author_link.text
                        self.profile = f"{HOME_URL}{self.author}/"
            except StaleElementReferenceException as e:
                continue

# Declare browser class
class Browser:
    """
    Browser with built in functionality for
    Instagram.

    Attributes
    ----------
    username : str
        Your instagram account username.
    timeout_exit : bool
        Automatically exit when an unhandled TimeoutException occurs.
    timeout_callback : Optional[callable]
        Callback when an unhandled TimeoutException occurs.
    """
    # Initialize object
    def __init__(
        self,
        username:str,
        timeout_exit:bool=True,
        timeout_callback:Optional[callable]=False
        ):

        # Initialize variables
        self.driver = no_indicators()
        self.driver.delete_all_cookies()
        self.typer = Typer(type_callback=self.on_type)
        self.username = username
        self.timeout_exit = timeout_exit
        self.timeout_callback = timeout_callback
        self.cooldown_started = False
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
        elif ord(character) <= 0xFFFF:
            element.send_keys(character)

    # Humanize movement to element
    def to_element(self, element):
        ActionChains(self.driver, 250 + random.random() * 500).move_to_element_with_offset(element, random.randint(-2, 2), random.randint(-1, 1))

    # Login using sessionid cookie
    def login(self, sessionid:str|None=None, password:str|None=None) -> bool:
        """
        Login has two options:
        - Login by adding your account's sessionid cookie (recommended) 
        - Attempt to login w/ password. This is likely to fail and may require you
        to retry several times before succeeding.
        
        Parameters
        ----------
        sessionid : str | None
            The VALUE of your sessionid cookie. You can obtain this by logging in to
            instagram on chrome and navigating to the application tab in
            inspect element. It will be in storage/cookies/https://www.instagram.com
        password : str | None
            Your instagram account's password.
        
        Returns
        -------
        bool
            The result of the login attempt
        """
        # Load site
        self.driver.get("https://www.instagram.com")
        # Check if session id was given
        if sessionid:
            # Add session id 
            self.driver.add_cookie({
                "name": "sessionid",
                "value": sessionid
            })
            # Reload page
            self.driver.refresh()
            return True
        elif password:
            # Get input fields
            try:
                usernameField = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text']")))
                passwordField = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']")))
            except TimeoutException as e:
                self._on_timeout(e)
            # Type in login credentials
            self.to_element(usernameField)
            self.typer.type_query(self.username, usernameField)
            self.to_element(passwordField)
            self.typer.type_query(password, passwordField)
            # Submit after filling out fields
            time.sleep(random.random())
            passwordField.send_keys(Keys.ENTER)
            # Wait for next page to load
            try:
                WebDriverWait(self.driver, 10).until(EC.staleness_of(passwordField))
            except TimeoutException as e:
                self._on_timeout(e)
            # Wait for continue button, catch timeout error WITHOUT exiting program (if this button appears it means the login failed)
            continueButton = False
            try:
                continueButton = WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Continue']")))
                print("Login Failed")
            except TimeoutException as e:
                print("Login Successful")
            # Check if continue button was found
            return not continueButton
        else:
            return False

    # Search the web for the given query, returns top sites
    def search_web(self, query:str) -> List[str]:
        """
        Search DuckDuckGo for the given query and get the results.
        
        Parameters
        ----------
        query : str
            The query to search for on DuckDuckGo

        Returns
        -------
        List[str]
            A list of each result's summary.
        """
        final_results = []
        # Validate query
        if len(query) > 0:
            # Get original tab
            original_tab = self.driver.current_window_handle
            # Open new tab and go to duckduckgo
            self.driver.switch_to.new_window('tab')
            self.driver.get("https://duckduckgo.com")
            # Find search bar
            try:
                search_bar = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "searchbox_input")))
            except TimeoutException as e:
                return []
            # Hover search bar
            self.to_element(search_bar)
            # Click after hovering
            time.sleep(random.random())
            search_bar.click()
            time.sleep(random.random())
            # Validate query
            if len(query) > 0:
                # Type
                self.typer.type_query(query, search_bar)
                # Wait randomly
                time.sleep(random.random())
                # Search and get result container
                search_bar.send_keys(Keys.ENTER)
                try:
                    results_container = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ol[class='react-results--main']")))
                except TimeoutException as e:
                    return []
                # Get results from container
                all_results = results_container.find_elements(By.TAG_NAME, "article")
                for result_article in all_results:
                    # Ads start with ra, results start with r[num]
                    is_ad = result_article.id[:2] == "ra"
                    # Skip ads and articles with no text
                    if not is_ad and result_article.text and len(result_article.text) > 0:
                        article_summary = result_article.text.splitlines()[-1]
                        if len(article_summary) >= 30:
                            final_results.append(result_article.text.splitlines()[-1])
            # Close search tab
            self.driver.close()
            self.driver.switch_to.window(original_tab)
        # Return final results
        return final_results
    
    # Search given query on feed
    def feed_search(self, query:str):
        """
        Searches the instagram explore page for the given query
        
        Parameters
        ----------
        query : str
            The query to search for on instagram explore

        """
        self.driver.get(FEED_URL + f"search/keyword/?q={url_parse.quote(query)}")
        # Check if failed to load
        try:
            reload_button = WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Reload Page']")))
            # Reload and wait
            reload_button.click()
            time.sleep(1)
        except TimeoutException as e:
            pass
            
    # Scroll through feed, return array of posts
    def feed_step(self, post_count:int=6) -> List[WebElement]:
        """
        Opens the explore page, or scrolls down if already open, and
        returns a list of each post anchor in random order.
        
        Parameters
        ----------
        post_count : int
            The number of posts to include. Defaults to 6.

        Returns
        -------
        List[WebElement]
            A list of post anchors in random order.
        """
        # Check current page
        if str(self.driver.current_url).find(FEED_URL) > -1:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            # Go straight to feed
            self.driver.get(FEED_URL)
        time.sleep(2 + random.random())
        # Initialize variables
        selected_posts = []
        post_anchors = []
        # Find post anchors
        while len(post_anchors) == 0:
            time.sleep(random.random()/10)
            post_anchors = self.driver.find_elements(by=By.TAG_NAME, value="a")
            post_anchors = [[anchor, anchor.get_attribute("href")] for anchor in post_anchors]
            post_anchors = [anchor[0] for anchor in post_anchors if anchor[1].startswith(f"{HOME_URL}p/")]
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
        """
        Opens the given post if it isn't already open. If new_tab is
        set to true, the post anchor's href will be opened in a new tab.
        Otherwise clicks the post anchor opening in a popup.
        
        Parameters
        ----------
        post_anchor : WebElement
            The post anchor to click on.
        new_tab : bool | None
            Bool to indicate if the post should open in a new tab.
            Defaults to True.

        """
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
            self._profile_open = False
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
    def close_post(self) -> bool:
        """
        Close the current tab if post opened in a new tab,
        otherwise find and click the close button.
        
        Returns
        -------
        bool
            Indicates whether the post closed successfully or not
        """
        # Check if post is open
        post = getattr(self, "_current_post", False)
        if getattr(self, "_new_tab", False):
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        elif post:
            # Get close button
            try:
                close_button = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, "//button[text()='Close']")))
            except TimeoutException as e:
                return False
            # Click close button
            self.to_element(close_button)
            close_button.click()
        # Reset variables
        self._current_post = None
        self._new_tab = None
        self._post_url = None
        return True

    # Get post image
    def get_post_image(self, post_anchor:WebElement) -> WebElement | None:
        # Get _aagv class
        try:
            post_info = WebDriverWait(post_anchor, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "_aagv")))
        except TimeoutException as e:
            return None
        # Validate
        if post_info:
            # Get image info from _aagv class
            image_info = post_info.find_element(by=By.TAG_NAME, value="img")
            # Return image info
            return image_info
        
    # Returns the alt text of the post thumbnail
    def get_alt(self, post_anchor:WebElement) -> str | None:
        # Get image info
        image_info = self.get_post_image(post_anchor=post_anchor)
        # Validate image info
        if image_info:
            # Get and return image description
            return image_info.get_attribute("alt")
        
    # Scroll to the end of a slides post
    def scroll_post(self, post_anchor:WebElement):
        """
        Scrolls through slides of a post until the last slide.
        """
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
        # Get post info
        post_info: PostInfo = PostInfo(self, post_anchor)
        if getattr(post_info, "like_button", None):
            # Random delay
            time.sleep(random.random()/5)
            # Hover on button and click
            self.to_element(post_info.like_button)
            post_info.like_button.click()

    # Follow the account who posted the given post
    def follow_profile(self, post_anchor:WebElement):
        # Get post info
        post_info: PostInfo = PostInfo(self, post_anchor)
        if getattr(post_info, "follow_button", None):
            # Random delay
            time.sleep(random.random()/20)
            # Press follow button
            post_info.follow_button.click()

    # Open the profile of the account who posted the given post
    def open_profile(self, post_anchor:WebElement):
        # Open profile from post info
        post_info: PostInfo = PostInfo(self, post_anchor)
        if getattr(post_info, "profile", None) and not getattr(self, "_profile_open", False):
            # Indicate profile is open
            self._profile_open = True
            self.driver.get(post_info.profile)

    # Get all comments from the comment section of the given post
    def get_comments(self, post_anchor:WebElement) -> List[str]:
        return PostInfo(self, post_anchor).comments

    # Comment on the given post
    def comment_post(self, post_anchor:WebElement, comment:str):
        # Get post info
        post_info = PostInfo(self, post_anchor)
        # Make sure comment input loaded
        if getattr(post_info, "comment_input", None):
            # Move mouse to comment input and click 
            self.to_element(post_info.comment_input)
            post_info.comment_input.click()
            # Get text field
            text_field = post_info.comment_input.find_element(by=By.TAG_NAME, value="textarea")
            # Validate text field
            if text_field:
                # Type in comment
                self.typer.type_query(comment, text_field)
                # Submit after typing comment
                self.on_type(comment, Keys.ENTER, text_field)
                # Wait after commenting
                time.sleep(2 + random.random())

    # Returns true if cooldown started
    def is_on_cooldown(self) -> bool:
        """
        Checks if a follow cooldown was detected in the last 24 hours.

        Returns
        -------
        bool
            Indicates if on cooldown
        """
        # Check if started
        if self.cooldown_started:
            # Disable cooldown after set length
            if time.time() - self.cooldown_started >= COOLDOWN_LENGTH:
                self.cooldown_started = False
            else:
                return True
        return False

    # Presses the given number of follow buttons
    def click_follow_buttons(self, header:str, follow:bool, count:int=1, max_retries:int=10) -> int:
        """
        Opens the followers/following tab on the current profile and follows 
        the given number of accounts. The profile must already be open.
        
        Parameters
        ----------
        header : str
            The name of the button on the profile to click. Also the header 
            that appears when the tab opens (followers, following). This is 
            used to wait until the dialog loads before proceeding, because
            it switches at first.
        follow : bool
            If true, search for and click buttons to follow accounts. If false,
            search for and click buttons to unfollow accounts.
        count : int | None
            How many accounts to follow/unfollow. Defaults to 1
        max_retries : int | None
            How many times to retry when getting the given count. If max
            retries is exceeded, the buttons that did load will still be
            clicked. Defaults to 10.
        
        Returns
        -------
        int
            The number of accounts followed/unfollowed
        """
        # Don't proceed if cooldown started
        if self.is_on_cooldown(): return 0
        clicked = 0
        all_links: List[WebElement] = self.driver.find_elements(By.CSS_SELECTOR, "a[role='link']")
        followers_link = None
        for link in all_links:
            if link.accessible_name.find(header.lower()) > -1:
                followers_link = link
                break
        # Check if link was found
        if followers_link:
            # Open followers
            self.to_element(followers_link)
            followers_link.click()
            # Wait for followers tab to load
            try:
                # Wait for header to load first because dialog tab switches
                WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, f"//div[text()='{header}']")))
                followers_tab = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[role='dialog']")))
            except TimeoutException as e:
                return
            button_name = "follow" if follow else "following"
            # Repeat until at least one button loads
            retries = 0
            while clicked == 0 and retries < max_retries and not self.cooldown_started:
                all_buttons = []
                while len(all_buttons) < count:
                    initial_length = len(all_buttons)
                    # Hover over followers frame and scroll
                    self.to_element(followers_tab)
                    # Scroll down
                    scroll_origin = ScrollOrigin.from_element(followers_tab)
                    ActionChains(self.driver).scroll_from_origin(scroll_origin, 0, 1000).perform()
                    # Give time for new accounts to load
                    time.sleep(3)
                    # Get all buttons in followers tab
                    all_buttons = followers_tab.find_elements(By.CSS_SELECTOR, "button")
                    # Stop scrolling if nothing new loaded
                    if initial_length == len(all_buttons):
                        break
                for follow_button in all_buttons:
                    if follow_button.accessible_name.lower() == button_name:
                        # Press button
                        self.to_element(follow_button)
                        follow_button.click()
                        # Check if on cooldown first
                        try:
                            WebDriverWait(self.driver, 0.5).until(EC.visibility_of_element_located((By.XPATH, "//*[text()='Try Again Later']")))
                            print("FOLLOW COOLDOWN DETECTED")
                            self.cooldown_started = time.time()
                            break
                        except TimeoutException as e:
                            pass
                        if not follow:
                            # Check if cancel button appeared
                            try:
                                cancel_button = WebDriverWait(self.driver, 0.5).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Cancel']")))
                                # Get unfollow button
                                unfollow_dialog = cancel_button.find_element(By.XPATH, "..")
                                unfollow_button = unfollow_dialog.find_element(By.XPATH, "//button[text()='Unfollow']")
                                # Click unfollow button
                                self.to_element(unfollow_button)
                                unfollow_button.click()
                            except TimeoutException as e:
                                pass
                        clicked += 1
                        # Random delay
                        time.sleep(random.random()/2)
                        # Check count
                        if clicked >= count:
                            break
                retries += 1
                time.sleep(1)
        return clicked

    # Follow people who follow the currently opened profile
    def follow_profile_followers(self, post_anchor:WebElement, count:int=1):
        """
        Opens the post anchor's author's profile and follows people that
        follow them. This method checks if a follow cooldown is currently
        in place before performing any actions.
        
        Parameters
        ----------
        post_anchor : WebElement
            The post anchor
        count : int | None
            How many people to follow. Defaults to 1.

        """
        if self.is_on_cooldown(): print("CANNOT FOLLOW ON COOLDOWN"); return
        # Attempt to open profile
        self.open_profile(post_anchor=post_anchor)
        if getattr(self, "_profile_open", False):
            # Follow profile followers
            followed = self.click_follow_buttons("Followers", True, count)
            print(f"Total accounts followed {followed}")

    # Unfollow given number of accounts
    def unfollow(self, count:int=1):
        """
        Opens the the user account and unfollows people they are following. 
        This method checks if a follow cooldown is currently in place before 
        performing any actions.
        
        Parameters
        ----------
        post_anchor : WebElement
            The post anchor
        count : int | None
            How many people to unfollow. Defaults to 1.

        """
        if self.is_on_cooldown():  print("CANNOT UNFOLLOW ON COOLDOWN"); return
        # Open followers page
        self.driver.get(f"{HOME_URL}{self.username}/")
        # Unfollow
        unfollowed = self.click_follow_buttons("Following", False, count)
        print(f"Total accounts unfollowed {unfollowed}")