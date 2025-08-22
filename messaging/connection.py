import pika
import os
from utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

def rabbitmq_connection():
    try:
        host = os.getenv("RMQ_HOST")
        port = int(os.getenv("RMQ_PORT"))
        user = os.getenv("RMQ_USER")
        password = os.getenv("RMQ_PASSWORD")
        credentials = pika.PlainCredentials(user, password)
        params = pika.ConnectionParameters(host, port, "/", credentials)
        
        connection = pika.BlockingConnection(params)
        return connection
    except:
        logger.error(f"(✗) An error occurred while loading environments")
