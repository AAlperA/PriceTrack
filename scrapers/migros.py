import os
import requests
from dotenv import load_dotenv
from utils import fakeua
from utils.logger import logger
from messaging.publisher import RabbitPublisher

load_dotenv()

class MigrosScraper:   
    def __init__(self):
        self.market = "migros"
        self.total_page = 0
        self.publisher = RabbitPublisher()
        self.categories_url = os.getenv("MIGROS_CATEGORIES_URL")
        self.api_url = os.getenv("MIGROS_API_URL")
        self.headers = {
            "User-Agent": fakeua.set_uagent()
        }

    def get_categories(self):
        """
        Requesting to migros's home page to get all category urls

        Returns List of category URLs
        """
        response = requests.get(self.categories_url, headers=self.headers)
        content = response.json()
        data = content['data']
        categories = []

        for item in data:
            pretty_name = item['data']['prettyName']
            categories.append(self.api_url + pretty_name)
        return categories

    def link_generator(self):
        """
        Adds categories to the API URL and increases the number of pages

        If request is unsuccesful "while loop" breaking with "status_code != 200"
        If page_count or hit_count is 0 than while loop is breaks

        Yields JSON response data for a single page
        """
        for link in self.get_categories():
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
                self.total_page += 1
                yield data
                page_num += 1

    def scrape(self):
        """
        Scrapes each paginated categories and makes it ready for RabbitMQ

        Yields 2 tuples as products and prices
        """
        data = self.link_generator()
        for page_data in data:
            product_data = []
            price_data = []
            product_infos = page_data['searchInfo']['storeProductInfos']
            for info in product_infos:
                brand = info['brand']['name']
                product_name = info['name']
                regular_price = float(info['regularPrice']/100)
                special_price = float(info['shownPrice']/100)

                if regular_price == special_price:
                    special_price = None

                try:
                    campaign = info['crmDiscountTags'][0]['tag']
                except IndexError:
                    campaign = None

                product_image = info['images'][0]['urls']['PRODUCT_HD']
                tags = info['category']['name']

                products = {
                    "product_name": product_name,
                    "brand": brand,
                    "market": self.market,
                    "product_image": product_image,
                    "tags": tags
                }

                prices = {
                    "product_name": product_name,
                    "market": self.market,
                    "special_price": special_price,
                    "regular_price": regular_price,
                    "campaign": campaign
                }

                product_data.append(products)
                price_data.append(prices)

            yield (self.market, "product", product_data)
            yield (self.market, "price", price_data)

        logger.info(f"A total of {self.total_page} pages were scraped")


if __name__ == "__main__":
    scraper = MigrosScraper()
    if scraper.publisher.channel is None:
        logger.error("(✗) Connection failed to RabbitMQ")
    else:
        for market, topic, payload in scraper.scrape():
            scraper.publisher.publish(market, topic, payload)
    scraper.publisher.close()
