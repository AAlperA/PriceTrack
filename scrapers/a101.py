import os
import requests
from dotenv import load_dotenv
from utils import fakeua
from utils.logger import logger
from messaging.publisher import RabbitPublisher

load_dotenv()

class A101Scraper:   
    def __init__(self):
        self.market = "a101"
        self.total_page = 0
        self.publisher = RabbitPublisher()
        self.api_url = os.getenv('A101_API_URL')
        self.headers = {
            "User-Agent": fakeua.set_uagent()
        }

    def pagination(self):
        """
        Iterates over category IDs in the API until status code 404.

        Yields JSON response data for a single page
        """
        category_num = 1
        while True:
            category_id = f"{category_num:02d}"
            url = self.api_url.replace("id=C01", f"id=C{category_id}")
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                logger.info(f"No more data available on page {category_id}")
                return
            
            data = resp.json()
            self.total_page += 1
            yield data
            category_num += 1
            logger.info(f"fetched: {url}")

    def scrape(self):
        """
        Scrapes categories and makes it ready for RabbitMQ

        Yields 2 tuples as products and prices
        """
        data_generator = self.pagination()
        for data in data_generator:
            product_data = []
            price_data = []
            categories = data["children"]
            for category in categories:
                tags = [category["name"]]
                product_infos = category["products"]
                for info in product_infos:
                    regular_price = float(info["price"]["normal"] / 100)
                    special_price = float(info["price"]["discounted"] / 100)

                    campaign = info["campaigns"] if info["campaigns"] else None
                        
                    brand = info["attributes"]["brand"]
                    product_name = info["attributes"]["name"]
                    product_image = info["images"][0]["url"]

                    if special_price == regular_price:
                        special_price = None

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

            if product_data and price_data:
                yield (self.market, "product", product_data)
                yield (self.market, "price", price_data)
        logger.info(f"A total of {self.total_page} pages were scraped")


if __name__ == "__main__":
    scraper = A101Scraper()
    if scraper.publisher.channel is None:
        logger.error("(✗) Connection failed to RabbitMQ")
    else:
        for market, topic, payload in scraper.scrape():
            scraper.publisher.publish(market, topic, payload)
    scraper.publisher.close()
    