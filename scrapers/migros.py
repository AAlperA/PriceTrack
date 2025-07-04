import os
import pika
import requests
from utils import fakeua
from utils.logger import logger
from storage import insert_products, insert_prices


class MigrosScraper:   
    def __init__(self, **kwargs):
        self.request_url = os.getenv('MIGROS_CATEGORIES_URL')
        self.api_url = os.getenv('MIGROS_API_URL')
        if not self.request_url or not self.api_url:
            self.request_url = kwargs.get('migros_categories_url')
            self.api_url = kwargs.get('migros_api_url')
            
        self.headers = {
            "User-Agent": fakeua.set_uagent()
        }
        self.response = requests.get(self.request_url, headers=self.headers)
        self.content = self.response.json()

    def category_links(self):
        data = self.content['data']
        categories = []
        for item in data:
            pretty_name = item['data']['prettyName']
            categories.append(self.api_url + pretty_name)
        return categories

    def link_generator(self):
        for link in self.category_links():
            page_num = 1
            while True:
                page_url = f"{link}?sayfa={page_num}"
                category_response = requests.get(page_url, headers=self.headers)
                data = category_response.json()['data']
                page_count = data['searchInfo']['pageCount']
                hit_count = data['searchInfo']['hitCount']
                
                if category_response.status_code != 200:
                    logger.error(f"Error: Status code {category_response.status_code}")
                    break
                
                elif page_count == 0 or hit_count == 0:
                    logger.info(f"No more data available on page {page_num}.")
                    break

                logger.info(f"fetched: {page_url}")
                yield data
                page_num += 1

    def scrape(self):
        product_data = []
        price_data = []
        data = self.link_generator()
        for page_data in data:
            market="migros"
            product_infos = page_data['searchInfo']['storeProductInfos']
            for info in product_infos:
                brand = info['brand']['name']
                product_name = info['name']
                try:
                    raw_regular_price = str(info['badges'][0]['value'])
                    regular_price = float(raw_regular_price.replace(',','.').replace(' TL',''))
                except:
                    regular_price = info['shownPrice']
                special_price =  float(info['loyaltyPrice']/100)
                if isinstance(regular_price, str):
                    regular_price, special_price = special_price, None
                try:
                    campaign = info['crmDiscountTags'][0]['tag']
                except:
                    campaign = None
                product_image = info['images'][0]['urls']['PRODUCT_HD']
                categories = info['categoriesForSorting']
                tags = [category['name'] for category in categories]
                product_data.append((product_name, brand, market, product_image, tags))
                price_data.append((market, product_name, special_price, regular_price, campaign))
                #Uncomment the following logger statement to debug scraped product information
                #logger.info(f"this product scraped = page: {market}, brand: {brand}, product: {product_name}")
        insert_products(product_data)
        insert_prices(product_data, price_data)

if __name__ == "__main__":
    scraper = MigrosScraper()
    scraper.scrape()