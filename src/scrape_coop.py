import asyncio
import time
import re
import requests

from requests_html import AsyncHTMLSession
from bs4 import BeautifulSoup
from websockets import client
from abc import ABC

from page_object_models import PAGE_COUNT_TEXT, UPC_TEXT, DETAILS_LIST

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# URLs
BASE_SEARCH_URL = 'https://rivervalleycoop.storebyweb.com/s/1000-1033/b?q={query}&pn={page}'
OPEN_FOOD_FACTS_URL = 'https://world.openfoodfacts.org/api/v3/product/{code}.json'

# Regular expressionns
INVENTORY_PATTERN = r'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-\d+$'
NO_RESULTS_PATTERN = r'No results for \".+\"'
HAS_RESULTS_PATTERN = r'Showing (\d+) to (\d+) of (\d+) Results'#\n for .+\n \((\d)+ Pages\)'
UPC_CODE_PATTERN = r"UPC:\s*(\d+)"


# Make sure to not accidentally DOS our beloved coop
MAX_ITEMS = 10
MAX_PAGES = 3

# 'break glass' case - make sure that we aren't accidentally DOS'ing via infinite recursion by tracking
# with a global variable and ensuring it doesn't exceed max allowable amount
MAX_REQUESTS = 50

class PatternMatchError(Exception):
    """Exception raised when text does not match any expected regex patterns."""
    pass

class RequestOverflowError(Exception):
    """Exception raised when we are triggering too many requests, risking accidental DOS"""
    pass


class BaseWebScraper:

    #@abstractmethod
    # TODO: refactor using abstract method
    def get_item_links(self, query, page):
        raise NotImplemntedError

    def get_upc(self, url):
        raise NotImplemntedError

    def get_page(self, url):
        raise NotImplemntedError

class SeleniumWebScraper(BaseWebScraper):

    def __init__(self):
        self.driver = self.launch_driver()
        self.request_counter = 0

    def teardown(self):
        self.driver.quit()

    #TODO: look into setting up local caching proxies
    def get_page(self, url):
        if self.request_counter > MAX_REQUESTS:
            raise RequestOverflowError("Too many requests issued; aborting")
        else:
            self.request_counter += 1
            self.driver.get(url)
            # Sleep to allow js to render
            time.sleep(1)
        
    def launch_driver(self):
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        #chrome_options.add_argument("--headless")  # Ensures Chrome runs in headless mode
        #chrome_options.add_argument("--disable-gpu")  # Disables GPU hardware acceleration
        #chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, REQUIRED on Linux if running as root user
        #chrome_options.add_argument("--disable-dev-shm-usage")  # Overcomes limited resource problems

        # Initialize WebDriver with the specified service and options
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver

    def get_item_links(self, query, page=1):

        print(f'Retrieving the links for query {query} page {page}')
        # First, get all the links on the page
        url = BASE_SEARCH_URL.format(query=query, page=page)
        self.get_page(url)
        elems = self.driver.find_elements(By.TAG_NAME, "a")

        # Next, filter to only strings which match the regular expression pattern
        # for item links. Using regular expressions may be slightly over-engineering in 
        # this scenario where we can just find a substring, but I prefer this approach to 
        # be more future-proof in case the link format changes.
        matches = []
        unmatches = []
        for elem in elems:
            link_text = elem.get_attribute("href")
            if re.fullmatch(INVENTORY_PATTERN, link_text):
                matches.append(link_text)
            # we track unmatches for debugging purposes -- We can spot-check these links to see 
            # if there are any exceptions to our standard pattern. 
            else:
                unmatches.append(link_text)
        print('Matches:', matches)
        print('Unnmatches:', unmatches)

        # Next, determine whether there are more pages. If not, return, otherwise, recurse.
        # recursion is probably not the best, change this to calculate once and iterate
        if self._has_more_pages() and len(matches) <= MAX_ITEMS and page <= MAX_PAGES:
            page += 1
            matches_next = self.get_item_links(query, page=page)
            matches.extend(matches_next)
        matches_deduped = self._deduplicate_matches(matches)
        return matches_deduped

    def _has_more_pages(self):
        elem = self.driver.find_element(*PAGE_COUNT_TEXT)
        page_text = elem.text
        has_results_match = re.match(HAS_RESULTS_PATTERN, page_text)
        if has_results_match:
            _, last, total = has_results_match.groups()
            if last == total: 
                return False
            else:
                return True
        elif re.fullmatch(NO_RESULTS_PATTERN, page_text):
            return False
        else:
            raise PatternMatchError(f'Could not match text {page_text} to expected regular expression')

    def _deduplicate_matches(self, matches):
        matches_set = set()
        matches_deduped = []
        for m in matches:
            if not m in matches_set:
                matches_deduped.append(m)
                matches_set.add(m)
        return matches_deduped

    def get_upc(self, url):
        self.get_page(url)
        upc_elem = self.driver.find_element(*UPC_TEXT)
        upc_text = upc_elem.text
        upc_code_match = re.match(UPC_CODE_PATTERN, upc_text)
        code = upc_code_match.groups()[0]
        return code
        
class BaseIngredientFinder:

    def get_ingredients(self, *args):
        return NotImplemntedError

class ApiIngredientFinder(BaseIngredientFinder):

    def get_facts(self, code):
        url = OPEN_FOOD_FACTS_URL.format(code=code)
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
        else:
            return None

    def get_ingredients(self, facts):
        ingredients_list = facts.get('product', {}).get('ingredients', [])
        ingredients_text = [ingredient['text'] for ingredient in ingredients_list]
        return ingredients_text

def main():
    scraper = SeleniumWebScraper()
    query = 'tofu'
    links = scraper.get_item_links(query)[:MAX_ITEMS]
    #links = ['https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-15900', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-9052', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-9447', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-9053', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-39791', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-9446', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-12357', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-45776', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-11286', 'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-9445']
    print('Matches:', links)
    codes = []
    for link in links:
        codes.append(scraper.get_upc(link))
    #codes = ['850109005020', '050012101806', '025484000100', '050012102605', '030871302163', '025484000124', '050012104302', '030871401002', '030871000021', '025484000131']
    ingredient_finder = ApiIngredientFinder()
    for code in codes:
        print(code)
        facts = ingredient_finder.get_facts(code)
        if facts is not None:
            ingredients = ingredient_finder.get_ingredients(facts)
            if ingredients != []:
                print(ingredients)
            else:
                print('ingredients not available')
        else:
            print('ingredients not available')

    #scraper.teardown()

if __name__ == "__main__":
    main()

