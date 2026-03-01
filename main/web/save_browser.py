# Dependencies
from main.web import Browser
from os import path, mkdir

import json
import pickle

# SETTINGS
SAVE_ATTRIBUTES = [ # Browser attributes that persist
    "cooldown_started"
]
SAVE_FOLDER = "datastore"
SAVE_PATH = SAVE_FOLDER + "/{key}.json"
LOAD_KEYS = []

# Declare save browser subclass
class SaveBrowser(Browser):
    """
    Browser which saves and loads data.

    Attributes
    ----------
    key : str
        Save file name, defaults to browser
    username : str
        Your instagram account username.
    timeout_exit : bool
        Automatically exit when an unhandled TimeoutException occurs.
    timeout_callback : Optional[callable]
        Callback when an unhandled TimeoutException occurs.
    """
    # Initialize object
    def __init__(self, key:str="browser", *args, **kwargs):
        # Initialize from superclass
        super(SaveBrowser, self).__init__(*args, **kwargs)
        # Initialize variables
        self.save_path = SAVE_PATH.format(key=key)
        self._cookies = []
        self._logged_in = False
        self._save = True

    # Override login function
    def login(self, **kwargs):
        # Load data
        if path.exists(self.save_path):
            with open(self.save_path, 'r') as f:
                # Load data
                self.data = json.load(f)
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
            for k in SAVE_ATTRIBUTES:
                self.data["attributes"][k] = getattr(self, k)
            # Write save file accordingly
            if path.exists(self.save_path):
                mode = 'w'
            else:
                mode = 'x'
                # Check if folder exists before creating new save file
                if not path.exists("datastore"):
                    mkdir(SAVE_FOLDER)
            with open(self.save_path, mode) as f:
                json.dump(self.data, f, indent=4)
            print("Session saved successfully")
            # Close normally
            Browser._close(self)