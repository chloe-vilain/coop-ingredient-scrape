import requests
        
class BaseIngredientFinder:
    # which methods to try to pull ingredients, ordered by
    # precedence
    ingredient_fetch_methods = []

    def get_ingredients(self, *args):
        raise NotImplementedError

    # To be implemented - retrieve data from data stores 
    def get_ingredients_from_database(self, code):
        return None

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

class OFFIngredientFinder(BaseIngredientFinder):
    api_url = 'https://world.openfoodfacts.org/api/v3/product/{code}.json'
    results_cache = {}

    def __init__(self):
        self.ingredient_fetch_methods = [self.get_ingredients_from_api, 
                                         self.get_ingredients_from_database]

    def get_ingredients_from_api(self, code: str):
        facts = self._call_OFF_api(code)
        if facts:
            ingredients_list = facts.get('product', {}).get('ingredients', [])
            ingredients_text = [ingredient['text'] for ingredient in ingredients_list]
            return ingredients_text if len(ingredients_text) > 0 else None
        else:
            return None
        
    def get_product_name_from_api(self, code: str):
        facts = self._call_OFF_api(code)
        if facts:
            return facts.get('product', {}).get('product_name', None)
        
    def _call_OFF_api(self, code):
        url = self.api_url.format(code=code)
        if url in self.results_cache:
            return self.results_cache[url]
        else:
            res = requests.get(url)
            if res.status_code == 200:
                results_json = res.json()
                self.results_cache[url] = results_json
                return results_json
            else:
                return None

    
    


