import asyncio
import random
import time

import aiohttp

from .config import REDDIT_CONF


async def meme_of_day() -> tuple[int, dict]:
    """
    returns image url with title, subreddit and author -randomly selected from output of scrape_subreddit
    """
    async with aiohttp.ClientSession() as session:
        ##get authorisation
        await set_auth(session)

        coros = [
            scrape_subreddit(session, sub, time="week", lim=20) for sub in REDDIT_CONF.subreddits
        ]

        memes = []
        for result in await asyncio.gather(*coros):
            memes.extend(result)

    selection = random.randrange(0, len(memes))
    return 0, memes[selection]


async def set_auth(session: aiohttp.ClientSession) -> None:
    # Only auth if token is expired
    if time.time() < REDDIT_CONF.auth_time + (100 * 60):
        return

    # note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
    auth = aiohttp.BasicAuth(REDDIT_CONF.creds["client_id"], REDDIT_CONF.creds["secret"])

    # here we pass our login method (password), username, and password
    data = {
        "grant_type": "password",
        "username": REDDIT_CONF.creds["username"],
        "password": REDDIT_CONF.creds["password"],
    }

    # setup our header info, which gives reddit a brief description of our app
    headers = {"User-Agent": "botblue"}

    # send our request for an OAuth token
    async with session.post(
        "https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers
    ) as res:
        # convert response to JSON and pull access_token value
        token = (await res.json())["access_token"]

    # add authorization to our headers dictionary
    REDDIT_CONF.auth_headers = {**headers, **{"Authorization": f"bearer {token}"}}
    REDDIT_CONF.auth_time = time.time()

    # while the token is valid (~2 hours) we just add headers=headers to our requests


async def scrape_subreddit(
    session: aiohttp.ClientSession,
    subreddit: str,
    time: str = "week",
    lim: int = 10,
    controversial: bool = False,
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
    async with session.get(
        f"https://oauth.reddit.com/r/{subreddit}/{cat}",
        headers=REDDIT_CONF.auth_headers,
        params=param_dict,
    ) as res:
        results = await res.json()
    # res objct contains listings data
    data = []
    ##iterate through top page of subreddit
    for item in results["data"]["children"]:
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
                        "score": post["score"],
                        "upvote_ratio": f'{int(100*post["upvote_ratio"])}%',
                    }
                )

    return data
