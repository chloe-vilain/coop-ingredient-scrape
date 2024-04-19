# coop-ingredient-scrape
This project scrapes the River Valley Food Coop's website to identify products matching a user’s query, scrapes the UPC code, and leverages the Open Food Facts API to pull ingredients.

## Usage

#### System requirements
* Poetry python package manager: https://python-poetry.org/docs/
* Google Chrome 

#### Running
You can run the main script from the command line using `poetry run python {local path}/coop-ingredient-scrape/src/get_coop_ingredients.py {query} -c {count of products to return, optional}` -- for example, `poetry run python ~/code/coop-ingredient-scrape/src/get_coop_ingredients.py 'tofu' -c 10`

#### Pitfalls to look out for

* Element not found when JS fails to load - Occasionally, the Javascript from a page may fail to fully load before we search for the element. When this occurs, the locator will fail to find the element (most elements are dynamically generated). Typically, this is resolved by re-running the program. The sleep timer settings which determine how long we wait before searching for the element can also be adjusted in web_constants.py. Selenium also supports workflows which will await an element's loading; I plan to re-factor to use this less brittle approach in the future

* Locator changes - Because we do not own the code for the Coop web site, the page design is subject to change at any time, potentially rendering the locators unusable. We can't fully mitigate this concern, but we could run an integration test job to periodically confirm that the elements are available on the page so that we know of such changes and can respond quickly. Isolating the locators to their own file so that they can easily be changed makes it simple to address such regressions

* Missing ingredient information - I quickly discovered that the Open Food Facts database lacks detailed information about many products, and particularly (unsurprisingly) the locally-sourced whole food products available at the Coop. In the future, I would like to implement additional data sources to mitigate this limitation.  

## Design decisions

#### Anti-DOS safety checks
One of the biggest risks of web scraping is inadvertently DOS'ing the host (or issuing too many requests and getting IP-banned). This scenario can occur due to poor design or bugs in the code (while loops and recursion especially are particularly risky due to their ability to go infinite)

To mitigate this risk, I funnel all web & API requests through a specific method, which will check whether the total requests exceed max allowable requests and increment a counter. It will raise an exception if max allowable requests is reached. This design is applied in the `get_page` method for the SeleniumWebScraper class and the `_request` method for the APIIngredientHelper class. 

#### Ingredient finder multi-source design
I initially implemented this project using Open Food Facts API to pull ingredients. I quickly discovered that the Open Food Facts database lacks detailed information about many products, and particularly (unsurprisingly) the locally-sourced products available at the Coop.  

With this challenge in mind, I designed the ingredient finder to iterate over multiple possible sources (which sources to use can be defined at the class level) to pull ingredients. Today, OFF API and Food Data Central APIs are supported, and this framework can be expanded to support both additional external data sources (such as additional APIs or web scraped data) as well as internal data store lookups. The present implementation will check each source in priority order and return results when it finds a non-empty ingredients list.

#### Isolation of locators & URLs
For web scraping and automated testing, it is useful to isolate HTML locators for reusability and ease of updating. The Page-Object Model design pattern is the classic pattern used for isolating these components -- in this design pattern, each web page has its own class defining the locators and how to access them.

For this project, because the scope was small and I wished to move quickly, I took a lighter-weight approach and isolated the locators (along with URLs, regular expressions, and most other constants) in web_constants.py. If I continue to expand this project, I will consider refactoring to use the Page-Object Model pattern.

#### Web scraper composition 
I implemented this initial version using Selenium, but it is conceivable that one would experiment with multiple technologies for scraping web data. Python does not support interfaces, and the best alternative is using the abc package to define abstract base classes. I leveraged this design in `web_scrapers.py` to define the required methods in the abstract class BaseWebScraper, to be implemented by concrete web scraper classes such as SeleniumWebScraper as well as any future scrapers.

## Next steps

* Add new data sources, such as web-scraped ingredients list, to supplement Open Food Facts API
* Add unit tests with mocks for external requests
* Refactor locator functionality to await availability of locators (rather than using fixed sleep timer)
* Investigate using async flows to pull items & ingredient details in parallel  
* Add integration test script to verify existence of locators 
* Refactor to use logging over print statements
