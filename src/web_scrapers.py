from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import re
from page_object_models import *

import time

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

# TODO: refactor using abstract class (ABC)
class BaseWebScraper:

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
    def get_page(self, url, sleep_timer=1):
        if self.request_counter > MAX_REQUESTS:
            raise RequestOverflowError("Too many requests issued; aborting")
        else:
            self.request_counter += 1
            self.driver.get(url)
            # Sleep to allow js to render
            time.sleep(sleep_timer)
        
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
    
    def get_item_links(self, query):

        # First, determin the total count of pages
        url = BASE_SEARCH_URL.format(query=query, page=1)
        self.get_page(url, sleep_timer=2)
        page_count = min(self._get_page_count(), MAX_PAGES)
        if page_count <= 0:
            return []
        
        matches = []
        unmatches = []
        # for deduplication 
        all_link_set = set()

        # iterate over all pages to retrieve items
        for page in range(2, page_count+1):
            print(f'Retrieving the links for query {query} page {page}')
            elems = self.driver.find_elements(By.TAG_NAME, "a")
            for elem in elems:
                link_text = elem.get_attribute("href")
                if re.fullmatch(INVENTORY_PATTERN, link_text) and link_text not in all_link_set:
                    matches.append(link_text)
                    all_link_set.add(link_text)
                # we track unmatches for debugging purposes -- We can spot-check these links to see 
                # if there are any exceptions to our standard pattern. 
                elif link_text not in all_link_set:
                    unmatches.append(link_text)
                    all_link_set.add(link_text)
                
            # don't fetch the items again on the last page
            if page == page_count + 1:
                break

            url = BASE_SEARCH_URL.format(query=query, page=page)
            self.get_page(url, sleep_timer=2)

        print('Matches:', matches)
        print('Unnmatches:', unmatches)
        
        return matches

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

    def _get_page_count(self):
        elem = self.driver.find_element(*PAGE_COUNT_TEXT)
        page_text = elem.text.split('\n')[-1]
        # print('Pages pattern: ', PAGES_PATTERN)
        has_results_match = re.match(PAGES_PATTERN, page_text)
        if has_results_match:
            return int(has_results_match.groups()[0])
        elif re.fullmatch(NO_RESULTS_PATTERN, page_text):
            return 0
        else:
            raise PatternMatchError(f'Could not match text {page_text} to expected regular expression')

    def get_upc(self, url):
        self.get_page(url)
        upc_elem = self.driver.find_element(*UPC_TEXT)
        upc_text = upc_elem.text
        upc_code_match = re.match(UPC_CODE_PATTERN, upc_text)
        code = upc_code_match.groups()[0]
        return code