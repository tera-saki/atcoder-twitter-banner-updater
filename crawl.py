import os
import re
from time import sleep
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait

import requests
import cv2

from logger import get_logger


class Crawler:
    """crawler class"""

    CONTEST_SHORT_NAME = ["ABC", "ARC", "AGC"]

    def __init__(self, username: str):
        self.username = username

        self.img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
        os.makedirs(self.img_dir, exist_ok=True)

        self.logger = get_logger(__name__)

        self._init_driver()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trackback):
        if exc_type is not None:
            self.logger.error(exc_type, exc_value, trackback)
        self.driver.quit()

    def _init_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=options)

    def _find_element_by_tag(self, tag: str, timeout: int = 10):
        return WebDriverWait(self.driver, timeout=timeout) \
            .until(lambda d: d.find_element(By.TAG_NAME, tag))

    def _find_element_by_id(self, id_: str, timeout: int = 10):
        return WebDriverWait(self.driver, timeout=timeout) \
            .until(lambda d: d.find_element(By.ID, id_))

    def _find_element_by_xpath(self, xpath: str, timeout: int = 10):
        return WebDriverWait(self.driver, timeout=timeout) \
            .until(lambda d: d.find_element(By.XPATH, xpath))

    def get_today_contest(self, contest_type: int) -> str | None:
        """
        if the contest of specified type was held today, return the id of that contest.
        otherwise, return None.

        Args:
            contest_type (int): 1: ABC, 2: ARC, 3: AGC

        Returns:
            str | None: contest id (e.g. abc 123)
        """
        url = f"https://atcoder.jp/contests/archive?ratedType={contest_type}"
        self.driver.get(url)

        tbody = self._find_element_by_tag("tbody")
        tr0 = tbody.find_element(By.TAG_NAME, "tr")
        tds = tr0.find_elements(By.TAG_NAME, "td")
        _start, _contest_name, _duration = tds[0], tds[1], tds[2]

        start = _start.text
        regex = r"\d{4}-\d{2}-\d{2}"
        contest_day = re.match(regex, start)[0]
        today = date.today().isoformat()
        duration = _duration.text
        if duration >= "03:00":
            today -= timedelta(days=1)
        if contest_day != today:
            self.logger.info("There was no %s today.", self.CONTEST_SHORT_NAME[contest_type - 1])
            return None

        contest_url = _contest_name.find_element(By.TAG_NAME, "a").get_attribute('href')
        contest_id = contest_url.split('/')[-1]
        self.logger.info("There was %s today!", contest_id)
        return contest_id

    def get_contest_result(self, contest_id: str) -> dict | None:
        """
        return your result of the specified contest.
        if your data was not found, return None.

        Args:
            contest_id (str): contest id (e.g. abc123)

        Returns:
            dict | None: your contest result
        """
        url = f"https://atcoder.jp/contests/{contest_id}/results/json"
        results = requests.get(url, timeout=60).json()
        for res in results:
            if res["UserName"] == self.username:
                self.logger.info("found your record in the standings.")
                return res
        self.logger.info("your record was not found in the standings.")
        return None

    def wait_rating_update(self, result: dict, interval: int = 60) -> None:
        """wait until rating is updated.

        Args:
            result (dict): contest result
        """
        old_rating = result["OldRating"]
        url = f"https://atcoder.jp/users/{self.username}"
        self.driver.get(url)
        xpath = "//th[contains(text(), 'Rating')]/following-sibling::td/span"

        self.logger.info("waiting for rating update...")
        while True:
            self.driver.refresh()
            sleep(1)

            rating = self._find_element_by_xpath(xpath).text
            if rating != old_rating:
                self.logger.info("rating changes detected.")
                break
            sleep(interval)


    def take_screenshot(self) -> None:
        """
        take screenshot of profile page.
        the screenshot is saved as img/banner.png
        """
        url = f"https://atcoder.jp/users/{self.username}"
        self.driver.get(url)
        sleep(1)

        file_status = os.path.join(self.img_dir, "status.png")
        file_graph = os.path.join(self.img_dir, "graph.png")
        file_banner = os.path.join(self.img_dir, "banner.png")

        status = self._find_element_by_id("ratingStatus")
        status.screenshot(file_status)
        graph = self._find_element_by_id("ratingGraph")
        graph.screenshot(file_graph)

        img_status = cv2.imread(file_status)
        img_graph = cv2.imread(file_graph)
        img = cv2.vconcat([img_status, img_graph])
        cv2.imwrite(file_banner, img)
        self.logger.info("screenshot was saved.")