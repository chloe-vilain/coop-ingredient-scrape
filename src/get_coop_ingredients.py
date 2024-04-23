# import asyncio
import argparse

from web_scrapers import SeleniumWebScraper
from ingredient_finders import IngredientFinderV1

MAX_ITEMS = 10
DEFAULT_ITEMS_COUNT = 10

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('food', type=str)
    parser.add_argument('--count', '-c', type=int, default=DEFAULT_ITEMS_COUNT, choices=range(1, MAX_ITEMS+1))
    args = parser.parse_args()

    scraper = SeleniumWebScraper()
    
    links = scraper.get_item_links(args.food)[:args.count]
    print('Matches:', links)
    codes = []
    #codes = ['850109005020', '050012101806', '025484000100', '050012102605', '030871302163', '025484000124', '050012104302', '030871401002', '030871000021', '025484000131']
    for link in links:
        codes.append(scraper.get_upc(link))
    ingredient_finder = IngredientFinderV1()
    print('Codes: ', codes)
    for code in codes:
        ingredient_finder.get_all_data(code)
    print(ingredient_finder.data)
    ingredient_finder.reconcile_data()
    for code, reconciled_data in ingredient_finder.reconciled_data.items():
        print(code)
        print(reconciled_data["name"])
        print(reconciled_data["ingredients"])
    scraper.teardown()

if __name__ == "__main__":
    main()

