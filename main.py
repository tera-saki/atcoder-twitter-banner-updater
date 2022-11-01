"""main"""
import os
import traceback
import argparse
from configparser import ConfigParser

import cv2
import tweepy
from slack_sdk import WebhookClient

from crawl import Crawler
from logger import get_logger

logger = get_logger(__name__)

config = ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini"))

consumer_key = config["twitter"]["consumer_key"]
consumer_secret = config["twitter"]["consumer_secret"]
access_token = config["twitter"]["access_token"]
access_token_secret = config["twitter"]["access_token_secret"]

auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
api = tweepy.API(auth)

img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

webhook_url = config.get("slack", "webhook_url")


def update_banner() -> None:
    """update twitter banner image"""
    img_path = os.path.join(img_dir, "banner.png")
    img = cv2.imread(img_path)
    height, width, _ = img.shape
    api.update_profile_banner(
        img_path, height=height/2, width=width, offset_top=0, offset_left=0)


def notify_with_webhook() -> None:
    """send notification to slack"""
    client = WebhookClient(webhook_url)
    client.send(text="banner image was updated.")


def run(contest_type: str) -> None:
    """run crawler and update banner image if necessary"""
    with Crawler(config["atcoder"]["username"]) as crawler:
        contest = crawler.get_today_contest(contest_type)
        if contest is None:
            return
        result = crawler.get_contest_result(contest)
        if result is None or result["IsRated"] is False:
            return
        crawler.wait_rating_update(result)
        update_banner()
        logger.info("updated banner image successfully!")
        if webhook_url is not None:
            notify_with_webhook()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('type', choices=['abc', 'arc', 'agc'],
                        help='AtCoder contest type.')

    args = parser.parse_args()

    try:
        run(args.type)
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()
