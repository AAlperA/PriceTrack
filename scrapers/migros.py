import os
import requests
from utils import fakeua
from utils.logger import logger
from messaging.publisher import RabbitPublisher


class MigrosScraper:   
    def __init__(self):
        self.publisher = RabbitPublisher()
        self.categories_url = os.getenv('MIGROS_CATEGORIES_URL')
        self.api_url = os.getenv('MIGROS_API_URL')
            
        self.headers = {
            "User-Agent": fakeua.set_uagent()
        }

        self.response = requests.get(self.categories_url, headers=self.headers)
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
                if category_response.status_code != 200:
                    logger.error(f"Error: Status code {category_response.status_code}")
                    break
                data = category_response.json()['data']
                page_count = data['searchInfo']['pageCount']
                hit_count = data['searchInfo']['hitCount']
                if page_count == 0 or hit_count == 0:
                    logger.info(f"No more data available on page {page_num}")
                    break
                logger.info(f"fetched: {page_url}")
                yield data
                page_num += 1

    def scrape(self):
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

                product_data = {"product_name":product_name, "brand":brand, "market":market, "product_image":product_image, "tags":tags}
                price_data = {"market":market, "product_name":product_name, "special_price":special_price, "regular_price":regular_price, "campaign":campaign}
                yield ("migros_product", product_data)
                yield ("migros_price", price_data)


if __name__ == "__main__":
    scraper = MigrosScraper()
    if scraper.publisher.channel is None:
        logger.error("(✗) Connection failed to RabbitMQ")
    else:
        for topic, payload in scraper.scrape():
            scraper.publisher.publish(topic, payload)
    scraper.publisher.close()
