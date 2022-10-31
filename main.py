import traceback
from configparser import ConfigParser

import tweepy
import cv2

from crawl import Crawler
from logger import get_logger

logger = get_logger(__name__)

config = ConfigParser()
config.read("config.ini")

auth = tweepy.OAuth1UserHandler(
    config["twitter"]["consumer_key"], config["twitter"]["consumer_secret"],
    config["twitter"]["access_token"], config["twitter"]["access_token_secret"])
api = tweepy.API(auth)

def update_banner():
    img_path = "img/banner.png"
    img = cv2.imread(img_path)
    height, width, _ = img.shape
    api.update_profile_banner(
        "img/banner.png", height=height/2, width=width, offset_top=0, offset_left=0)

def main():
    with Crawler(config["atcoder"]["username"]) as crawler:
        contest = crawler.get_today_contest(1)
        if contest is None:
            return
        result = crawler.get_contest_result(contest)
        if result.get("IsRated") is not True:
            return
        crawler.wait_rating_update(result)
        update_banner()
        logger.info("updated banner image successfully!")


try:
    main()
except Exception:
    traceback.print_exc()



