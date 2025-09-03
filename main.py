import argparse
from utils.logger import logger
from scrapers.migros import MigrosScraper
from scrapers.a101 import A101Scraper
from scrapers.getir import GetirScraper

SCRAPERS = {
        'migros': MigrosScraper,
        'a101': A101Scraper,
        'getir': GetirScraper 
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    prog='Scraper wrapper',
    description='Run selected scraper. Options: migros, a101, getir'
    )
    
    # Choose a single scraper to run (e.g. --scraper a101)
    parser.add_argument('--scraper', default='getir')

    args = parser.parse_args()

    runner = SCRAPERS[args.scraper]()

    if runner.publisher.channel is None:
        logger.error("(✗) RabbitMQ connection failed")
    else:
        for market, topic, payload in runner.scrape():
            runner.publisher.publish(market, topic, payload)

    runner.publisher.close()
