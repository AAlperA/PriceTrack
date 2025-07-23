import argparse
from utils.logger import logger
from scrapers.migros import MigrosScraper
from scrapers.a101 import A101Scraper


SCRAPERS = {
        'migros': MigrosScraper,
        'a101': A101Scraper 
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    prog='Scraper wrapper',
    description='Run selected scraper. Options: migros, a101'
    )
    
    # Choose a single scraper to run (e.g. --scraper a101)
    parser.add_argument('--scraper', default='migros')

    args = parser.parse_args()

    runner = SCRAPERS[args.scraper]()

    if runner.publisher.channel is None:
        logger.error("(✗) RabbitMQ connection failed")
    else:
        for market, topic, payload in runner.scrape():
            runner.publisher.publish(market, topic, payload)

    runner.publisher.close()
