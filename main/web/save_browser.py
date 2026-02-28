# Dependencies
from main.web import Browser
from os import path, mkdir

import pickle

# SETTINGS
SAVE_FOLDER = "datastore"
SAVE_PATH = SAVE_FOLDER + "\\browser.pkl"
LOAD_KEYS = []

# Declare save browser subclass
class SaveBrowser(Browser):
    """
    Browser which saves and loads data.

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
    def __init__(self, *args, **kwargs):
        # Initialize from superclass
        super(SaveBrowser, self).__init__(*args, **kwargs)
        # Initialize variables
        self.custom_data = {}
        self._cookies = []
        self._logged_in = False
        self._save = True

    # Override login function
    def login(self, **kwargs):
        # Load data
        if path.exists(SAVE_PATH):
            with open(SAVE_PATH, 'rb') as f:
                # Load data
                self.data = pickle.load(f)
                # Load attributes
                if 'attributes' in self.data.keys():
                    for attribute, value in self.data['attributes'].items():
                        setattr(self, attribute, value)
                # Load sessionid
                if 'sessionid' in self.data.keys():
                    self._logged_in = Browser.login(self, sessionid=self.data['sessionid'])
                    return self._logged_in
        # Call base function, store result and return
        self._logged_in = Browser.login(self, **kwargs)
        # Save session id if login was successful
        if self._logged_in == True:
            cookie = self.driver.get_cookie("sessionid")
            if cookie:
                self.data['sessionid'] = cookie["value"]
        return self._logged_in

    # Add save data
    def save_data(self, key, val):
        self.data[key] = val
    # Get saved data
    def get_data(self, key):
        if key in self.data:
            return self.data[key]
        return False
    
    # Overwrite close function
    def _close(self):
        # Make sure login was successful first
        if self._logged_in:
            # Save attributes
            self.data["attributes"] = {
                "cooldown_started": self.cooldown_started
            }
            # Write save file accordingly
            if path.exists(SAVE_PATH):
                mode = 'wb'
            else:
                mode = 'xb'
                # Check if folder exists before creating new save file
                if not path.exists("datastore"):
                    mkdir(SAVE_FOLDER)
            with open(SAVE_PATH, mode) as f:
                pickle.dump(self.data, f)
            print("Session saved successfully")
            # Close normally
            Browser._close(self)