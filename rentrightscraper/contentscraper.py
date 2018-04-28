"""rentright.scraper.contentscraper"""
import datetime
import os
import requests
import time

from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from google.cloud import datastore

from rentrightscraper.util.log import get_configured_logger

class ContentScraper(object):
    """Implements a content scrape for a list of listings.

    Assumes that listings have been stored in Google Datastore.

    Attributes:
        logger: self explanatory
        proxy: proxy IP set by env var HTTP_PROXY
        ua: UserAgent object to generate random user agents
        zipcode: zip code for this scrape
    """

    def __init__(self):
        """Init ContentScraper.

        proxy is set to value of HTTP_PROXY environment variable
        logger is retrieved from get_configured_logger function
        """
        self.logger = get_configured_logger(__name__)
        self.proxy = os.environ['PROXY']
        self.ua = UserAgent()
        self.sleeplong = 5
        self.logger.info('ListingScraper initialized.')

    def execute(self, listing):
        """Executes a content scrape for the requested zip code and database."""
        url = listing["link"]
        self.logger.info('Scraping details for: {}'.format(url))
        content = self._scrape_details(url)
        self._writedetailstodatastore(content, listing)
        return content

    def _postnotfound(self, content):
        """Returns whether or not the page has a .post-not-found-heading

        :param content: str of content
        :return: bool: True if content has .post-not-found-heading class
        """
        soup = BeautifulSoup(content, 'html.parser')
        if soup.select('.post-not-found-heading'):
            return True
        else:
            return False

    def _scrape_details(self, url):
        """Get a page of content.

        Configures user-agent header and http(s) proxy to make a safe scrape
        of a particular URL.

        :param url: str, the url to get the content from
        :return: str containing content from the url
        """
        headers = {'User-Agent': self.ua.random}
        proxies = {'http': self.proxy, 'https': self.proxy}

        while True:
            try:
                resp = requests.get(url, headers=headers, proxies=proxies)
                # resp = requests.get(url, headers=headers)
                if self._postnotfound(resp.content):
                    self.logger.info('Page not found.')
                    break
                if resp.status_code != 200:
                    raise Exception(
                            'Response contained invalid '
                            'status code {}'.format(resp.status_code)
                          )
                break
            except Exception as e:
                self.logger.info('Exception occurred during request.')
                self.logger.info('{}'.format(e))
                self.logger.info(
                    'Sleeping for {} seconds'.format(self.sleeplong)
                )
                time.sleep(self.sleeplong)
                self.logger.info('Retrying')

        return resp.content

    def _writedetailstodatastore(self, content, listing):
        """Write the results of a scrape to Datastore.

        The original listing object is passed through so that the record in the
        table can be updated to reflect that the content has been acquired.

        :param url: string, url that was scraper
        :param content: string, html content that from the url
        :param listing: dict, contains original listing that was processed
        :return:
        """
        ds_client = datastore.Client()
        listing_key = ds_client.key("ListingLink", listing["id"])
        listing_entity = ds_client.get(listing_key)
        listing_entity["content"] = content
        listing_entity["content_acquired"] = True
        listing_entity["content_parsed"] = False
        listing_entity["time_content_acquired"] = datetime.datetime.utcnow()
