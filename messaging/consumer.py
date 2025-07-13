import os
import json
from messaging.connection import rabbitmq_connection
from utils.logger import logger


def get_scraper_list():
    raw_scrapers = os.getenv("QUEUE_KEYS")
    
    scraper_list = []
    for item in raw_scrapers.split(","):
        fixed = item.strip()
        if fixed:
            scraper_list.append(fixed)

    return scraper_list


def callback(user_callback):
    def handler(channel, method, properties, body):
        queue_name = method.routing_key
        try:
            data = json.loads(body)
            user_callback(queue_name, data)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"(✗) Error handling message for {queue_name}: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    return handler


def start_consumers(user_callback):
    connection = rabbitmq_connection()
    if not connection:
        logger.error("(✗) Connection failed to RabbitMQ")
        return

    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) 

    scrapers = get_scraper_list()  

    for name in scrapers:
        queue_name = f"{name}_queue"
        channel.basic_consume(
            queue=queue_name,
            on_message_callback = callback(user_callback),
            auto_ack=False
        )

    try:
        channel.start_consuming()
    except Exception as e:
        logger.error(f"(✗) An error occurred while consuming: {e}")
    finally:
        connection.close()
