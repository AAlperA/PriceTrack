import json
import pika
from .connection import rabbitmq_connection
from utils.logger import logger


class RabbitPublisher:
    def __init__(self):
        self.connection = rabbitmq_connection()
        if not self.connection:
            self.channel = None
        else:
            self.channel = self.connection.channel()

    def publish(self, queue_name, data):
        if not self.channel:
            logger.warning(f"(✗) No channel to publish '{queue_name}'")
            return

        try:
            payload = json.dumps(data, ensure_ascii=False)
            self.channel.basic_publish(
                exchange="scrapers",
                routing_key=queue_name,
                body=payload,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )

            product_name = data.get('product_name', 'Unknown Product')
            market = data.get('market', 'Unknown Market')
            
            logger.info(f"(✓) Message published to {queue_name} << ({market} - {product_name})")

        except Exception as e:
            logger.error(f"(✗) Publishing failed to '{queue_name}': {e}")

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("(✓) RabbitMQ connection closed.")
            