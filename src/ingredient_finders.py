import requests
from exceptions import RequestOverflowError
from utils.get_secrets import get_secret
from collections import defaultdict

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
    name = "OFFIngredientHelper"

    def get_data(self, code: str):
        data = {"name": None, "ingredients": None}
        facts = self._request(self.off_api_host, self.off_api_endpoint.format(code=code))
        if facts:
            product_details = facts.get('product', {})
            data["name"] = product_details.get('product_name')
            ingredients = product_details.get('ingredients', None)
            if ingredients:
                data["ingredients"] = [ingredient['text'].upper() for ingredient in ingredients]
        return data

class FDCIngredientHelper(APIIngredientsHelper):
    fdc_api_host = 'https://api.nal.usda.gov'
    fdc_api_endpoint = '/fdc/v1/foods/search?api_key={key}&query={query}'
    name = "FDCIngredientHelper"

    def __init__(self):
        self.api_key = get_secret("env_var", "FDC_API_KEY")

    def get_data(self, code):
        data = {"name": None, "ingredients": None}
        if not self.api_key:
            print('FDC API Key not available, skipping FDC data source.')
            return data
        facts = self._request(self.fdc_api_host, self.fdc_api_endpoint.format(key=self.api_key, query=code))
        all_results = facts.get('foods', [])
        for result in all_results:
            if result.get('gtinUpc') == code:
                data["ingredients"] = result["ingredients"].upper().split(' ')
                data["name"] = result.get("brandName")
                break
        return data
        

# Not yet implemented, but included as an example of how we could
# leverage multiple data sources
class DatabaseIngredientHelper:
    name = "DBIngredientHelper"
    
    def get_data(self, code):
        return {"name": None, "ingredients": None}
    
class BaseIngredientFinder:
    data_helpers = []
    data = defaultdict(dict)

    def __init__(self):
        self.helpers = [Helper() for Helper in self.data_helpers]

    def get_all_data(self, code: str):
        """
        Retrieve all pertinent data for a given code and update
        self.data with the results
        """
        for helper in self.helpers:
            self.data[code][helper.name] = helper.get_data(code)

    def reconcile_data(self):
        """
        Reconcile data to just a single result per code
        self.reconcile_data_method is an attribute of the class, so different
        IngredientFinders can use different methods of reconciliation 
        """
        self.reconciled_data = self.reconcile_data_method()

    def _by_order(self):
        """
        Reconcile >1 data source available by choosing the first non-null result
        Order is determined by the order of the data_helpers list
        """
        reconciled_data = {}
        for code, data in self.data.items():
            reconciled_data[code] = defaultdict(lambda: {"source": None, "value": None})
            print(data)
            for helper in self.helpers:
                if (name:=data[helper.name]["name"]):
                    reconciled_data[code]["name"] = {"source": helper.name, "value": name}
                if (ingredients:=data[helper.name]["ingredients"]):
                    reconciled_data[code]["ingredients"] = {"source": helper.name, "value": ingredients}
        return reconciled_data
              
class IngredientFinderV1(BaseIngredientFinder):
    data_helpers = [OFFIngredientHelper, FDCIngredientHelper, DatabaseIngredientHelper]
    reconcile_data_method = BaseIngredientFinder._by_order

        
