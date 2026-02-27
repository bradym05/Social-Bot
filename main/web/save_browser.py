# Dependencies
from main.web import Browser
from os import path, mkdir
from time import time

import pickle

# SETTINGS
SAVE_FOLDER = "datastore"
SAVE_PATH = SAVE_FOLDER + "\\browser.pkl"
LOAD_KEYS = []

# Declare save browser subclass
class SaveBrowser(Browser):
    # Initialize object
    def __init__(self, *args, **kwargs):
        # Initialize from superclass
        super(SaveBrowser, self).__init__(*args, **kwargs)
        # Initialize variables
        self.custom_data = {}
        self._cookies = []
        self._logged_in = False
        self._save = True
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
                self._logged_in = True
        else:
            # Call base function, store result
            self._logged_in = Browser.login(self)
        # Save cookies if login was successful
        if self._logged_in == True:
            self._cookies = self.driver.get_cookies()
        return self._logged_in
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
        # Make sure login was successful first
        if self._logged_in:
            # Initialize data
            save_data = self.custom_data
            save_data['url'] = self.platform.feed_url
            # Save valid cookies
            valid = []
            for c in self._cookies:
                #if 'value' in c and c['value'].find('\\') == -1:
                if 'name' in c and c['name'] == "sessionid":
                    valid.append(c)
            # Reference valid cookies
            save_data['cookies'] = valid
            # Write save file accordingly
            if path.exists(SAVE_PATH):
                mode = 'wb'
            else:
                mode = 'xb'
                # Check if folder exists before creating new save file
                if not path.exists("datastore"):
                    mkdir(SAVE_FOLDER)
            with open(SAVE_PATH, mode) as f:
                pickle.dump(save_data, f)
            print("Session saved successfully")
            # Close normally
            Browser._close(self)