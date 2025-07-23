import os
import requests
from dotenv import load_dotenv
from utils import fakeua
from utils.logger import logger
from messaging.publisher import RabbitPublisher

load_dotenv()


class A101Scraper:   
    def __init__(self):
        self.publisher = RabbitPublisher()
        self.api_url = os.getenv('A101_API_URL')
            
        self.headers = {
            "User-Agent": fakeua.set_uagent()
        }

    def pagination(self):
        category_num = 1
        while True:
            category_id = f"{category_num:02d}"
            url = self.api_url.replace("id=C01", f"id=C{category_id}")
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 404:
                logger.info(f"No more data available on page {category_id}")
                return
            data = resp.json()
            yield data
            category_num += 1
            logger.info(f"fetched: {url}")

    def scrape(self):
        data_generator = self.pagination()
        market = "a101"
        for data in data_generator:
            categories = data["children"]
            for category in categories:
                products = category["products"]
                tags = [category["name"]]
                for product in products:
                    regular_price = float(product["price"]["normal"] / 100)
                    special_price = float(product["price"]["discounted"] / 100)

                    campaign = product["campaigns"] if product["campaigns"] else None
                        
                    brand = product["attributes"]["brand"]
                    product_name = product["attributes"]["name"]
                    product_image = product["images"][0]["url"]

                    if special_price == regular_price:
                        special_price = None

                    product_data = {
                        "product_name": product_name,
                        "brand": brand,
                        "market": market,
                        "product_image": product_image,
                        "tags": tags
                    }
                
                    price_data = {
                        "market":market, 
                        "product_name":product_name, 
                        "special_price":special_price, 
                        "regular_price":regular_price, 
                        "campaign":campaign
                    }

                    yield (market, "product", product_data)
                    yield (market, "price", price_data)


if __name__ == "__main__":
    scraper = A101Scraper()
    if scraper.publisher.channel is None:
        logger.error("(✗) Connection failed to RabbitMQ")
    else:
        for market, topic, payload in scraper.scrape():
            scraper.publisher.publish(market, topic, payload)
    scraper.publisher.close()
    