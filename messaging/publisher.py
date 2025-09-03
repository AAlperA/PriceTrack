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

    def publish(self, market, topic , data):
        if not self.channel:
            logger.warning(f"(✗) No channel to publish")
            return
        
        routing_key=f"{market}.{topic}"
        
        try:
            payload = json.dumps(data, ensure_ascii=False)
            self.channel.basic_publish(
                exchange="scrapers",
                routing_key=routing_key,
                body=payload,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            logger.info(f"(✓) {topic.title()} collection has been published to {routing_key} queue")
        except Exception as e:
            logger.error(f"(✗) Publish failed for {routing_key}: {e}")

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("(✓) RabbitMQ connection closed.")
            