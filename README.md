# evently

## Goal

We want to develop a framework for microservices.

Our goal is to seamlessly integrate various communication protocols and provide a unified and easy to read interface for the developers

Types of communication protocols we want to support:
- HTTP (REST, SOAP)
- AMQP
- WebSockets
- gRPC (?)


## Users Interface
We want to use similar approach to the one used in chalice, fastapi, flask and other lightweight frameworks

```python
http = HTTPRouter()
rest = RestRouter()
amqp = AMQPRouter('amqp://localhost:5672')
ws = WebSocketRouter()


@http.get("/hello")
async def hello_http():
    return "<html><body><h1>Hello World</h1></body></html>"


@rest.get('/hello') # get, post, put, delete, patch, etc.
async def hello(hello_request: HelloRequest):
    return {"message": f"Hello {hello_request.name}"}


@amqp.consume(queue='hello')
async def hello_amqp(message: dict, consumer) -> None:
    print(message)
    

@amqp.consume(queue='first-queue')
@amqp.produce(name="instant_producer", queue='second-queue', instantly=True)
@amqp.produce(name="once_finished_producer", queue='second-queue', once_finished=True)
async def msg_handler(message: dict, consumer, instant_producer, once_finished_producer) -> None:
    await once_finished_producer.send({"processed": message}) # message is sent once the handler is finished
    await instant_producer.send({"received": message}) # message is sent instantly
    print(message)
    ... # do some processing


@ws.get("/hello")
async def hello_ws(websocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        await websocket.send_json(data)


@ws.get("/hello")
@amqp.consume(queue='hello')
@amqp.produce(queue='received')
async def hello_ws_amqp(websocket, consumer, producer):
    await websocket.accept()
    producer.send({"message": websocket.receive_text()})
    while True:
        yield await consumer.receive() # yield is used to send data to the client over websocket
    

@http.get("/hello")
@amqp.produce(name="producer", queue='hello')
async def hello_http_amqp(query: dict, producer):
    yield "<html><body><h1>Hello World</h1></body></html>" # yield is used to send data to the client over http
    producer.send({"message": "Hello World", "query": query})


@rest.get('/hello')
@amqp.produce(queue='hello')
async def hello_rest_amqp(body: HelloRequest, producer):
    yield {"message": f"Hello {body.name}"} # yield is used to send data to the client over http
    producer.send({"message": f"Hello {body.name}"})


app = App()


app.add_router(http)
app.add_router(rest)
app.add_router(ws)
app.add_router(amqp)
```
