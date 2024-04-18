from selenium.webdriver.common.by import By

# URLS
BASE_SEARCH_URL = 'https://rivervalleycoop.storebyweb.com/s/1000-1033/b?q={query}&pn={page}'

# Regular expressionns
INVENTORY_PATTERN = r'https://rivervalleycoop.storebyweb.com/s/1000-1033/i/INV-1000-\d+$'
NO_RESULTS_PATTERN = r'No results for \".+\"'
HAS_RESULTS_PATTERN = r'Showing (\d+) to (\d+) of (\d+) Results'#\n for .+\n \((\d)+ Pages\)'
UPC_CODE_PATTERN = r"UPC:\s*(\d+)"
PAGES_PATTERN = r'\((\d+) Pages\)'

# Page Object Models 
# List items page
# todo: this is brittle; consider other options
PAGE_COUNT_TEXT = (By.XPATH, '/html/body/div[1]/div[1]/section/main/div[2]/div[2]/div[2]/span')#(By.CLASS_NAME, "text-right")

# Detail items page
UPC_TEXT = (By.CLASS_NAME, "upc")
DETAILS_LIST = (By.CLASS_NAME, "list-unstyled")
