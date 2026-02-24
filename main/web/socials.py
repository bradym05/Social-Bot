
# Declare base class
class BaseSocial:
    login_url:str
    feed_url:str
    feed_button:str
    like_button:str
    comment_section:str
    comments:str
    popup:str
    account:str

class Instagram(BaseSocial):
    login_url = "https://www.instagram.com"
    feed_url = r"https://www.instagram.com/explore/search/keyword/?q=rivals%20clips"
    feed_button = "Explore"
    popup = "x1cy8zhl"
    account = "x1dm5mii"