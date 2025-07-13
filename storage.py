import os
import json
import pymysql
from utils.logger import logger
from messaging.consumer import start_consumers
from dotenv import load_dotenv

def connection():

    load_dotenv()
    try:
        db = pymysql.connect(
            host = os.getenv("DB_HOST"),
            user= os.getenv("DB_USER"),
            password= os.getenv("DB_PASSWORD"),
            database= os.getenv("DB_DATABASE"),
            autocommit=False
        )
        logger.info("(✓) Connected to MySQL database")
        return db, db.cursor()
    except Exception as e:
        logger.error(f"(✗) Connection failed to MySQL database because of: {e}")

    return None, None

def process_message(queue_name, data: dict, db, cursor):
    try:
        if queue_name == "migros_product":
            insert_products([(
                data["product_name"],
                data["brand"],
                data["market"],
                data["product_image"],
                data["tags"]
            )], cursor)
            logger.info(f"(✓)📦 Product inserted: {data['market']} - {data['product_name']}")

        elif queue_name == "migros_price":
            product_keys = [(data["product_name"], data["market"])]
            price_rows = [(
                data["market"],
                data["product_name"],
                data["special_price"],
                data["regular_price"],
                data["campaign"]
            )]
            insert_prices(product_keys, price_rows, cursor)
            logger.info(f"(✓)💸 Price inserted: {data['market']} - {data['product_name']}")

        else:
            logger.warning(f"(?) Unknown queue: {queue_name}, data: {data}")

        db.commit()  
    except Exception as e:
        logger.error(f"(✗) Error inserting data from {queue_name}: {e}")
        db.rollback()  

def insert_products(product_data, cursor):

    for product_name, brand, market, product_image, tags in product_data:
        insert_query = """
            INSERT INTO products (product_name, brand, market, product_image, tags)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                brand = VALUES(brand),
                product_image = VALUES(product_image),
                tags = VALUES(tags)
        """
        tags_json = json.dumps(tags, ensure_ascii=False)
        cursor.execute(insert_query, (
            product_name,
            brand,
            market,
            product_image,
            tags_json
        ))

def insert_prices(product_data, price_data, cursor):

    placeholders = ",".join(["(%s, %s)"] * len(product_data))
    values = []
    for product_name, market in product_data:
        values.extend([product_name, market])

    query = f"""
        SELECT product_name, market, product_id
        FROM products
        WHERE (product_name, market) IN ({placeholders})
    """
    cursor.execute(query, values)
    results = cursor.fetchall()

    pairs = {}
    for product_name, market, product_id in results:
        pairs[(product_name, market)] = product_id  
    
    price_values = []
    for market, product_name, special_price, regular_price, campaign in price_data:
        product_id = pairs.get((product_name, market))
        if product_id is not None:
            price_values.append((
                market,
                product_name,
                product_id,
                regular_price,
                special_price,
                campaign
            ))

    if price_values:
        insert_query = """
            INSERT INTO prices (market, product_name, product_id, regular_price, special_price, campaign)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, price_values)

if __name__ == "__main__":
    
    db, cursor = connection()
    if db is None or cursor is None:
        logger.error("(✗) Consumers cannot be started without a database connection.")
    else:
        def wrapper(queue_name, data):
            return process_message(queue_name, data, db, cursor)
        
        start_consumers(wrapper)

        cursor.close()
        db.close()
        