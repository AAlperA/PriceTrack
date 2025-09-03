import os
import json
import pymysql
from utils.logger import logger
from messaging.consumer import start_consumers
from dotenv import load_dotenv

load_dotenv()

def connection():
    """
    Establish a connection to the MySQL database using environment variables.
    """
    try:
        db = pymysql.connect(
            host = os.getenv("DB_HOST"),
            user= os.getenv("DB_USER"),
            password= os.getenv("DB_PASSWORD"),
            database= os.getenv("DB_DATABASE"),
            charset=os.getenv("MYSQL_CHARSET"),
            collation=os.getenv("MYSQL_COLLATION"),
            autocommit=False,
            init_command='SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
        )
        logger.info("(✓) Connected to MySQL database")
        return db, db.cursor()
    except Exception as e:
        logger.error(f"(✗) Connection failed to MySQL database because of: {e}")

    return None, None

def process_message(market, topic, data: dict, db, cursor):
    """
    Process RabbitMQ messages and insert data into MySQL.

    Args:
        market (str): Market name
        topic (str): 'product' or 'price'
        data (dict): Messages
        db (pymysql): Database connection
        cursor (pymysql): Database cursor
    """
    try:
        if topic == "product":
            product_data = []
            for item in data:
                product_data.append((
                   item["product_name"],
                   item["brand"],
                   item["market"],
                   item["product_image"],
                   item["tags"]
                ))
            insert_products(product_data, cursor)
            logger.info(f"(✓)📦 Product inserted: {market} - count={len(product_data)}")

        elif topic == "price":
            product_keys = []
            price_rows = []
            for item in data:

                if item.get("campaign"):
                    campaign = json.dumps(item["campaign"], ensure_ascii=False)
                else:
                    campaign = None

                product_keys.append((item["product_name"], item["market"]))
                price_rows.append((
                    item["special_price"],
                    item["regular_price"],
                    campaign
                ))
            insert_prices(product_keys, price_rows, cursor)
            logger.info(f"(✓)💸 Prices inserted: {market} - count={len(price_rows)}")

        else:
            logger.warning(f"(?) Unknown queue: {topic}, data: {data}")

        db.commit()  
    except Exception as e:
        logger.error(f"(✗) Error inserting data from {topic}: {e}")
        db.rollback()  

def insert_products(product_data, cursor):
    """
    Insert or update products in the 'products' table.

    Args:
    product_data (list of tuple): Each tuple contains:
        (product_name, brand, market, product_image, tags)
    """
    insert_query = """
        INSERT INTO products (product_name, brand, market, product_image, tags)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            brand = VALUES(brand),
            product_image = VALUES(product_image),
            tags = VALUES(tags)
    """
    
    values = []
    for product_name, brand, market, product_image, tags in product_data:
        values.append((
            product_name,
            brand,
            market,
            product_image,
            json.dumps(tags, ensure_ascii=False)
        ))

    cursor.executemany(insert_query, values)

def insert_prices(product_data, price_data, cursor):
    """
    Insert prices for products into the 'prices' table.

    Args:
        product_data (list of tuple): Each tuple contains (product_name, market)
        price_data (list of tuple): Each tuple contains (special_price, regular_price, campaign)

    Maps product_name and market to product_id in the 'products' table.
    Only inserts prices for products that exist in the database.
    """

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
    for (product_name, market), (special_price, regular_price, campaign) in zip(product_data, price_data):
        product_id = pairs.get((product_name, market))
        if product_id is not None:
            price_values.append((
                product_id,
                special_price,
                regular_price,
                campaign
            ))

    if price_values:
        insert_query = """
            INSERT INTO prices (product_id, special_price, regular_price, campaign)
            VALUES (%s, %s, %s, %s)
        """
        cursor.executemany(insert_query, price_values)

if __name__ == "__main__":
    
    db, cursor = connection()
    if db is None or cursor is None:
        logger.error("(✗) Consumers cannot be started without a database connection.")
    else:
        def wrapper(market, topic, data):
            return process_message(market, topic, data, db, cursor)
        
        start_consumers(wrapper)

        cursor.close()
        db.close()
        