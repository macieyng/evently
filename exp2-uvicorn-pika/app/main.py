from fastapi import FastAPI
from typing import Any
from functools import partial
from aio_pika import Message, connect
from aio_pika.abc import AbstractIncomingMessage
import logging
import asyncio
from pydantic import BaseModel
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s ||| %(filename)s:%(lineno)d %(name)s ||| %(message)s')


def transform(message: dict | BaseModel | str) -> bytes:
    if isinstance(message, str):
        return message.encode()
    if isinstance(message, dict):
        return str(message).encode()
    if isinstance(message, BaseModel):
        return message.model_dump_json().encode()
    raise ValueError(f"Cannot transform message of type {type(message)}")

class Publisher:
    def __init__(self, queue: str, amqp_url: str):
        self.queue = queue
        self.amqp_url = amqp_url
        # self.loop = asyncio.get_event_loop()
        
    async def _send(self, message: Any, delay: float = 0.0):
        await asyncio.sleep(delay)
        connection = await connect(self.amqp_url)
        
        msg = transform(message)
        
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(self.queue)
            message = Message(body=msg)
            await channel.default_exchange.publish(message, routing_key=queue.name)

        logging.info(f"Sending message {message.body} to queue {self.queue} at {self.amqp_url}")
    
    async def send(self, message: Any, delay: float = 0.0):
        while True:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._send(message, delay=delay))
                break
            asyncio.sleep(0.1)



class Consumer:
    def __init__(self, queue: str, amqp_url: str):
        self.queue = queue
        self.amqp_url = amqp_url
        
    async def on_message(self, message: AbstractIncomingMessage, func) -> None:
        async with message.process():
            logging.info(f"✨ Received message {message!r}")
            await func(message=message)
            logging.info(f"     Message body is: {message.body!r}")
        
    async def consume(self, func):
        connection = await connect(self.amqp_url)
        async with connection:
            # Creating a channel
            channel = await connection.channel()

            # Declaring queue
            queue = await channel.declare_queue(self.queue)

            # Start listening the queue with name 'hello'
            on_message = partial(self.on_message, func=func)
            await queue.consume(on_message, no_ack=True)


class App(FastAPI):
    
    def publish(self, queue, amqp_url, publisher: str = "publisher"):
        def decorator(func):
            logging.info(f"Adding publisher to {func}")
            pub = Publisher(queue, amqp_url)
            return partial(func, **{publisher: pub})
        return decorator
    
    def consume(self, queue, amqp_url):
        logging.info(f"Adding consumer to {queue} at {amqp_url}")
        consumer = Consumer(queue, amqp_url)
        def decorator(func):
            # something must ping this function to start the consumer :(
            return func
        return decorator


app = App()


@app.get("/")
@app.publish(queue="test", amqp_url="amqp://guest:guest@rabbitmq:5672/%2F")
async def root(publisher):
    logging.info("Publishing message")
    msg = {"message": "Hello World"}
    await publisher.send(msg)
    logging.info(f"Published message {msg}")
    return msg


@app.get("/health")
@app.publish(queue="health", amqp_url="amqp://guest:guest@rabbitmq:5672/%2F", publisher="health_publisher")
@app.publish(queue="test", amqp_url="amqp://guest:guest@rabbitmq:5672/%2F", publisher="test_publisher")
async def root(health_publisher, test_publisher):
    logging.info("Publishing message")
    msg = {"status": "OK"}
    await health_publisher.send(msg)
    await test_publisher.send(msg, delay=10.0)
    logging.info(f"Published message {msg}")
    return msg


@app.consume(queue="test", amqp_url="amqp://guest:guest@rabbitmq:5672/%2F")
async def consume_test(message: Message):
    # does not work
    logging.info(f"Receiving message {message.body}.")
    # yet


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
