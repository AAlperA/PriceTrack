import argparse
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
        parser.add_argument('--migros_categories_url', default='https://www.migros.com.tr/rest/categories')
        parser.add_argument('--migros_api_url', default='https://www.migros.com.tr/rest/search/screens/')

        args = parser.parse_args()

        SCRAPERS[args.scraper](**args.__dict__).scrape()
