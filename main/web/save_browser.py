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
    # Initialize object
    def __init__(self, *args, **kwargs):
        # Initialize from superclass
        super(SaveBrowser, self).__init__(*args, **kwargs)
        # Initialize variables
        self.custom_data = {}
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
                # Remove loaded keys
                data.pop('url')
                data.pop('cookies')
                # Load custom data
                for k, v in data.items():
                    self.custom_data[k] = v
                # Reload page
                self.driver.refresh()
        else:
            # Call base function
            Browser.login(self)
    # Add custom save data
    def save_data(self, key, val):
        self.custom_data[key] = val
    # Get custom saved data
    def get_data(self, key):
        if key in self.custom_data:
            return self.custom_data[key]
        return False
    # Overwrite close function
    def _close(self):
        # Initialize data
        save_data = self.custom_data
        save_data['url'] = self.driver.current_url
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