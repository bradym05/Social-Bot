
# Declare base class
class BaseSocial:
    login_url:str
    feed_url:str
    feed_button:str

class Instagram(BaseSocial):
    login_url = "https://www.instagram.com"
    feed_url = "https://www.instagram.com/explore/"
    feed_button = "Explore"