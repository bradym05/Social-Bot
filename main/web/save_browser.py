# Dependencies
from main.web import Browser
from os import path
from time import time

import pickle

# SETTINGS
SAVE_PATH = "datastore\\browser.pkl"
LOAD_KEYS = []

# Declare save browser subclass
class SaveBrowser(Browser):
    # Initialize from superclass
    def __init__(self, *args, **kwargs):
        super(SaveBrowser, self).__init__(*args, **kwargs)
    # Overwrite login function
    def login(self):
        # Load data
        if path.exists(SAVE_PATH):
            with open(SAVE_PATH, 'rb') as f:
                # Load file
                data = pickle.load(f)
                # Go to last page
                last_page = data['url']
                self.driver.get(last_page)
                # Load cookies
                for c in data['cookies']:
                    if 'expiry' in c:
                        if float(c['expiry']) < time():
                            continue
                    self.driver.add_cookie(c)
                # Reload page
                self.driver.refresh()
        else:
            # Call base function
            Browser.login(self)
    # Overwrite close function
    def _close(self):
        # Initialize data
        save_data = {
            'url':self.driver.current_url,
            }
        # Save valid cookies
        cookies = self.driver.get_cookies()
        valid = []
        for c in cookies:
            if 'value' in c and c['value'].find('\\') == -1:
                valid.append(c)
        # Reference valid cookies
        save_data['cookies'] = valid
        # Write save file accordingly
        mode = 'wb' if path.exists(SAVE_PATH) else 'xb'
        with open(SAVE_PATH, mode) as f:
            pickle.dump(save_data, f)
        # Close normally
        Browser._close(self)