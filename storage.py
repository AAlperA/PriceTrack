import os
import json
import pymysql
from utils.logger import logger
from utils.config_loader import config_source, local_config


def connection():
    local_config_path = r"C:/path/to/your/config.json"
    config = local_config(local_config_path)

    try:
        db = pymysql.connect(
            host = os.getenv("DB_HOST") or config.get("DB_LOCAL_HOST"),
            user=config_source("DB_USER", config_path=local_config_path),
            password=config_source("DB_PASSWORD", config_path=local_config_path),
            database=config_source("DB_DATABASE", config_path=local_config_path),
            autocommit=False
        )
        logger.info("(✓) Connected to MySQL database")
        return db, db.cursor()
    except Exception as e:
        logger.error(f"(✗) Connection failed to MySQL database because of: {e}")

    return None, None

def insert_products(product_data):
    db, cursor = connection()

    try:
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
        db.commit()
        logger.info("(✓) All products successfully saved")

    except Exception as e:
        logger.error(f"(✗) Failed to save products because of:{e}")
        db.rollback()
    
    finally:
        cursor.close()
        db.close()

def insert_prices(product_data, price_data):
    db, cursor = connection()

    try:
        product_keys = []
        for p in product_data:
            product_keys.append((p[0], p[2]))

        placeholders = ",".join(["(%s, %s)"] * len(product_keys))
        values = []
        for pair in product_keys:
               values.extend(pair)
               
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
                price_values.append((market, product_name, product_id, regular_price, special_price, campaign))

        if price_values:
            insert_query = """
                INSERT INTO prices (market, product_name, product_id, regular_price, special_price, campaign)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_query, price_values)

        db.commit()
        logger.info("(✓) All prices successfully saved")

    except Exception as e:
        logger.error(f"(✗) Failed to save prices because of: {e}")
        db.rollback()

    finally:
        cursor.close()
        db.close()