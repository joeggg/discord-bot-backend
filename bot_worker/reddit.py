import random
import time
import requests

from .config import REDDIT_CONF


async def meme_of_day() -> tuple[int, dict]:
    """
    returns image url with title, subreddit and author -randomly selected from output of scrape_subreddit
    """
    ##get authorisation
    set_auth()

    memes = []
    for sub in REDDIT_CONF.subreddits:
        memes.extend(scrape_subreddit(sub, time="week", lim=10))

    selection = random.randrange(0, len(memes))
    return 0, memes[selection]


def set_auth() -> None:
    # Only auth if token is expired
    if time.time() < REDDIT_CONF.auth_time + (100 * 60):
        return
    # note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
    auth = requests.auth.HTTPBasicAuth(REDDIT_CONF.creds["client_id"], REDDIT_CONF.creds["secret"])

    # here we pass our login method (password), username, and password
    data = {
        "grant_type": "password",
        "username": REDDIT_CONF.creds["username"],
        "password": REDDIT_CONF.creds["password"],
    }

    # setup our header info, which gives reddit a brief description of our app
    headers = {"User-Agent": "botblue"}

    # send our request for an OAuth token
    res = requests.post(
        "https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers
    )

    # print(res)
    # convert response to JSON and pull access_token value
    token = res.json()["access_token"]

    # add authorization to our headers dictionary
    REDDIT_CONF.auth_headers = {**headers, **{"Authorization": f"bearer {token}"}}
    REDDIT_CONF.auth_time = time.time()

    # while the token is valid (~2 hours) we just add headers=headers to our requests


def scrape_subreddit(
    subreddit: str, time: str = "week", lim: int = 10, controversial: bool = False
) -> list[dict]:
    """
    function that scrapes subreddit posts and collects images

    inputs:
    subreddit - name of subreddit (str)
    auth - 'headers' output of initialise auth function (dict)
    time - timeframe of page being called
    lim - number of posts pulled from subreddit - default = 10 (int)
    controversial - if True, returns controversial listings as opposed to top listings - default = False (bool)
    -----------

    returns
    list of dicts containing title, image url and author each
    """
    ##set params for api request
    param_dict = {"t": time, "limit": lim}
    ##set cat keyword
    cat = "controversial" if controversial else "top"

    ##make the request
    res = requests.get(
        f"https://oauth.reddit.com/r/{subreddit}/{cat}",
        headers=REDDIT_CONF.auth_headers,
        params=param_dict,  # type: ignore
    )
    # res objct contains listings data
    data = []
    ##iterate through top page of subreddit
    for item in res.json()["data"]["children"]:
        ##check item is a post, not comment/user etc
        if item["kind"] == "t3":
            ##if post, then we can carry on
            post = item["data"]
            ##check post is an image
            # if 'post_hint' in post and post['post_hint'] == 'image':
            if "url" in post and post["url"].startswith("https://i.redd.it"):
                ##if post is image, save title and image url
                data.append(
                    {
                        "title": post["title"],
                        "url": post["url"],
                        "author": post["author"],
                        "subreddit": "r/" + subreddit,
                    }
                )

    return data
