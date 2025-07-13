import argparse
from utils.logger import logger
from scrapers.migros import MigrosScraper


SCRAPERS = {
        'migros': MigrosScraper,
}

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
    prog='Scraper wrapper',
    description='Run selected scrapers for the PriceTrack project'
    )
    
    parser.add_argument('--scraper', default='migros')


    args = parser.parse_args()

    runner = SCRAPERS[args.scraper]()

    if runner.publisher.channel is None:
        logger.error("(✗) Connection failed to RabbitMQ")
    else:
        for topic, payload in runner.scrape():
            runner.publisher.publish(topic, payload)

    runner.publisher.close()
