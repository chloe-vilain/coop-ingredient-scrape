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
    # codes = ['850109005020', '050012101806', '025484000100', '050012102605', '030871302163', '025484000124', '050012104302', '030871401002', '030871000021', '025484000131']
    for link in links:
        codes.append(scraper.get_upc(link))
    ingredient_finder = IngredientFinderV1()
    for code in codes:
        print(code)
        product_name = ingredient_finder.get_product_name(code)
        ingredients = ingredient_finder.get_ingredients(code)
        if product_name is not None:
            print(product_name)
        else:
            print('product name not available')
        if ingredients is not None:
            print(ingredients)
        else:
            print('ingredients not available')
    scraper.teardown()

if __name__ == "__main__":
    main()

