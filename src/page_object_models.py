from selenium.webdriver.common.by import By

# List items page
# todo: this is brittle; consider other options
# relative locator?
PAGE_COUNT_TEXT = (By.XPATH, '/html/body/div[1]/div[1]/section/main/div[2]/div[2]/div[2]/span')#(By.CLASS_NAME, "text-right")

# Detail items page
UPC_TEXT = (By.CLASS_NAME, "upc")
DETAILS_LIST = (By.CLASS_NAME, "list-unstyled")


#NEXT_BUTTON = {"method": By.}