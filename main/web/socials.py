
# Declare base class
class BaseSocial:
    login_url:str
    feed_url:str
    feed_button:str
    like_button:str
    comments:str

class Instagram(BaseSocial):
    login_url = "https://www.instagram.com"
    feed_url = "https://www.instagram.com/explore/"
    feed_button = "Explore"
    like_button = "xp7jhwk"
    comments = "x78zum5"