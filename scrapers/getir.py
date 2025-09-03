import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from utils.logger import logger
from utils.fakeua import set_uagent as ua
from messaging.publisher import RabbitPublisher
from dotenv import load_dotenv
import time
import random
from playwright.sync_api import sync_playwright

load_dotenv()

class GetirScraper:
    def __init__(self):
        self.publisher = RabbitPublisher()
        self.url = os.getenv('GETIR_URL')
        self.market = "getir"
        self.playwright = None
        self.browser = None 
        self.context = None
        self.page = None
        
    def setup_playwright(self):
        """Start playwright browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
        )
        self.context = self.browser.new_context(
            user_agent=ua()
        )
        return True

    def close_playwright(self):
        """Close playwright browser"""
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Error closing playwright: {e}")
    
    def fetch_html(self, url=None):
        """Fetch and return JavaScript-rendered HTML content from given URL"""
        if url is None:
            url = self.url
            
        if not self.playwright:
            if not self.setup_playwright():
                return None
                
        self.page = self.context.new_page()
        
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        self.page.wait_for_load_state('networkidle', timeout=60000)
        
        try:
            logger.info("Waiting for category links...")
            self.page.wait_for_selector('a[href*="/buyuk/kategori/"]', timeout=30000)
        except:
            logger.info("Waiting for product links...")
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.page.wait_for_selector('a[href*="/buyuk/urun/"]', timeout=30000)
        
        html = self.page.content()
        self.page.close()
        return html

    def get_categories(self):
        """
        Scrapes all category URLs from Getir's home page
        
        Returns a list of category URLs
        """
        html = self.fetch_html()
        soup = BeautifulSoup(html, "html.parser")
        
        category_urls = soup.select('a[href*="/buyuk/kategori/"]')

        cats = []
        for category_link in category_urls:
            href = category_link.get("href")
            href = urljoin(self.url, href)
            cats.append(href)

        logger.info(f'Number of categories found: {len(cats)}')
        return cats

    def scrape(self):
        """
        Scrapes each paginated categories and makes it ready for RabbitMQ

        Yields 2 tuples as products and prices
        """
        try:
            categories = self.get_categories()
            
            product_data = [] 
            price_data = []    
            for category_url in categories:
                logger.info(f"Category is processing: {category_url}")
                
                try:
                    html = self.fetch_html(category_url)
                    soup = BeautifulSoup(html, "html.parser")
                    products = soup.select('a[href*="/buyuk/urun/"]')
                    
                    logger.info(f"{len(products)} > Products found in this category")
                    
                    for product in products:
                        try:
                            figure = product.find('figure')
                            product_name = figure.get('title')
                            
                            img = product.select_one('img[data-testid="main-image"]')
                            product_image = img.get('src') if img else None
                            
                            container = product.find_parent("article")
                            regular_price = None
                            special_price = None
                            campaign = None
                            
                            if container:
                                price_spans = container.select('span[data-testid="text"]')
                                prices = [span.text for span in price_spans if '₺' in span.text]
                                
                                if len(prices) >= 2:
                                    regular_price = prices[0].replace('₺', '')
                                    regular_price = float(regular_price.replace('.', '').replace(',', '.').strip())
                                    try:
                                        special_price = prices[1].replace('₺', '')
                                        special_price = float(special_price.replace('.', '').replace(',', '.').strip())
                                    except ValueError:
                                        special_price = None
                                        
                                    campaign = "Discount"  
                                elif len(prices) == 1:
                                        special_price = prices[0].replace('₺', '')
                                        special_price = float(special_price.replace('.', '').replace(',', '.').strip())
                            
                            brand = None
                            if product_name and ' ' in product_name:
                                brand = product_name.split(' ')[0]
                            
                            if '/' in category_url:
                                category_name = category_url.split('/')[-2].split('-')[:-1]
                                category_name = ' '.join(category_name)
                                tags = [category_name] if category_name.strip() else []
                            else:
                                tags = []
                            
                            products_dict = {
                                "product_name": product_name.strip(),
                                "brand": brand,
                                "market": self.market,
                                "product_image": product_image,
                                "tags": tags
                            }

                            prices_dict = {
                                "product_name": product_name.strip(),
                                "market": self.market,
                                "special_price": special_price,
                                "regular_price": regular_price,
                                "campaign": campaign
                            }

                            product_data.append(products_dict)
                            price_data.append(prices_dict)
                            
                        except Exception as e:
                            logger.error(f"Product processing error: {e}")
                            continue
                    
                    wait_time = random.uniform(1, 3)
                    logger.info(f"Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    
                except Exception as e:
                    logger.exception(f"Category processing error {category_url}: {e}")
                    continue
            
            logger.info(f"A total of {len(product_data)} products were found")
            logger.info(f"A total of {len(price_data)} prices were found")
            
            yield (self.market, "product", product_data)
            yield (self.market, "price", price_data)
            
        finally:
            self.close_playwright()


if __name__ == "__main__":
    scraper = GetirScraper()
    if scraper.publisher.channel is None:
        logger.error("(✗) Connection failed to RabbitMQ")
    else:
        for market, topic, payload in scraper.scrape():
            scraper.publisher.publish(market, topic, payload)
    scraper.publisher.close()
    