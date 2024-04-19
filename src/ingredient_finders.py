import requests
from exceptions import RequestOverflowError
from utils.get_secrets import get_secret

MAX_REQUESTS = 100

REQUEST_MAX_BY_HOST = {
    'https://world.openfoodfacts.org': 100,
    'https://api.nal.usda.gov': 100
}

class APIIngredientsHelper:
    results_cache = {}
    request_counter = {host: 0 for host in REQUEST_MAX_BY_HOST}

    # assumption: all requests are GET requests
    def _request(self, host, endpoint):
        url = host + endpoint
        if url in self.results_cache:
            return self.results_cache[url]
        elif self.request_counter[host] <= REQUEST_MAX_BY_HOST[host]:
            res = requests.get(url)
            self.request_counter[host] += 1
            if res.status_code == 200:
                results_json = res.json()
                self.results_cache[url] = results_json
                return results_json
            else:
                return None
        else:
            raise RequestOverflowError(f'Exceeded maximum requests to {host}')

class OFFIngredientHelper(APIIngredientsHelper):
    off_api_host = 'https://world.openfoodfacts.org'
    off_api_endpoint = '/api/v3/product/{code}.json'

    def get_ingredients_from_OFF_api(self, code: str):
        facts = self._request(self.off_api_host, self.off_api_endpoint.format(code=code))
        if facts:
            ingredients_list = facts.get('product', {}).get('ingredients', [])
            ingredients_name_list = [ingredient['text'].upper() for ingredient in ingredients_list]
            if len(ingredients_name_list) > 0:
                return ingredients_name_list, "OFF"
        
    def get_product_name_from_OFF_api(self, code: str):
        facts = self._request(self.off_api_host, self.off_api_endpoint.format(code=code))
        if facts:
            name = facts.get('product', {}).get('product_name', None)
            if name:
                return name, "OFF"

class FDCIngredientHelper(APIIngredientsHelper):
    fdc_api_host = 'https://api.nal.usda.gov'
    fdc_api_endpoint = '/fdc/v1/foods/search?api_key={key}&query={query}'

    def get_ingredients_from_FDC_api(self, code, *key_args):
        """
        Query the FDC API using the UPC code
        """
        api_key = self.fdc_api_key
        facts = self._request(self.fdc_api_host, self.fdc_api_endpoint.format(key=api_key, query=code))
        all_results = facts.get('foods', [])
        ingredients = None
        for result in all_results:
            if result.get('gtinUpc') == code:
                ingredients = result["ingredients"].upper().split(' ')
                return ingredients, "FDC"
    
    def get_name_from_FDC_api(self, code, *key_args):
        api_key = self.fdc_api_key
        facts = self._request(self.fdc_api_host, self.fdc_api_endpoint.format(key=api_key, query=code))
        all_results = facts.get('foods', [])
        for result in all_results:
            if result.get('gtinUpc') == code and (brand_name:=result.get("brandName")):
                return brand_name, "FDC"
        

# Not yet implemented, but included as an example of how we could
# leverage multiple data sources
class DatabaseIngredientHelper:

    def get_ingredients_from_database(self, code):
        return None
    
    def get_product_name_from_database(self, code):
        return None
        
class BaseIngredientFinder:
    # which methods to try to pull ingredients, ordered by
    # precedence

    def __init__(self):
        self.ingredient_fetch_methods = []
        self.name_fetch_methods = []

    def get_ingredients(self, code: str):
        """
        Iterate over the ingredient_fetch_methods, which are ordered
        by precedence. Return the first non-null result. Reconciling 
        multiple results is not currently in scope
        """
        for method in self.ingredient_fetch_methods:
            results = method(code)
            if results:
                return results
    
    def get_product_name(self, code):
        for method in self.name_fetch_methods:
            results = method(code)
            if results:
                return results
              
class IngredientFinderV1(BaseIngredientFinder, OFFIngredientHelper, FDCIngredientHelper, DatabaseIngredientHelper):

    def __init__(self):
        super().__init__()
        self.fdc_api_key = get_secret("env_var", "FDC_API_KEY")
        self.ingredient_fetch_methods = [self.get_ingredients_from_OFF_api,
                                         self.get_ingredients_from_FDC_api,
                                         self.get_ingredients_from_database]
        self.name_fetch_methods = [self.get_product_name_from_OFF_api,
                                   self.get_name_from_FDC_api,
                                   self.get_product_name_from_database]
        
