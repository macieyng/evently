from consumer import Consumer
from publisher import Publisher
import logging
import asyncio

async def main():
    eventloop = asyncio.get_event_loop()
    if not eventloop.is_running():
        print("Starting event loop")
        eventloop.run_forever()
    
    logging.basicConfig(level=logging.INFO)
    amqp_url = 'amqp://guest:guest@rabbitmq:5672/%2F'
    consumer = Consumer(amqp_url)
    publisher = Publisher(
        'amqp://guest:guest@localhost:5672/%2F?connection_attempts=3&heartbeat=3600'
    )
    asyncio.gather(await consumer.run(), await publisher.run())


if __name__ == '__main__':
    
    asyncio.run(main())