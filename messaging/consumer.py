import os
import json
from messaging.connection import rabbitmq_connection
from utils.logger import logger


def get_markets():
    markets = os.getenv("MARKETS")
    
    market_list = []
    for market in markets.split(","):
        fixed = market.strip()
        if fixed:
            market_list.append(fixed)

    return market_list


def callback(user_callback):
    def handler(channel, method, properties, body):
        rk = method.routing_key
        try:
            market, topic = rk.split(".", 1)
        except ValueError:
            logger.warning(f"(?) Invalid routing_key: {rk}")
            channel.basic_ack(method.delivery_tag)
            return
        try:
            data = json.loads(body)
            user_callback(market, topic, data)
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"(✗) Handling {rk} failed: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    return handler


def start_consumers(user_callback):
    connection = rabbitmq_connection()
    if not connection:
        logger.error("(✗) RabbitMQ connection failed")
        return

    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) 

    for market in get_markets():
        for topic in ("product", "price"):
            routing_key = f"{market}.{topic}"
            queue_name  = f"{market}_{topic}_queue"

            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(
                exchange="scrapers",
                queue=queue_name,
                routing_key=routing_key
            )

            channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback(user_callback),
                auto_ack=False
            )

    try:
        channel.start_consuming()
    except Exception as e:
        logger.error(f"(✗) Consuming failed because of: {e}")
    finally:
        connection.close()
