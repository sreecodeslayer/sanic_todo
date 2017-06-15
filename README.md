Todo Application
===

This is a simple todo example of using [Sanic](https://github.com/channelcat/sanic) with [MongoDB Motor](https://github.com/mongodb/motor) and User session management with [Sanic-auth](https://github.com/pyx/sanic-auth)

### Usage
1. Clone this repository
2. Install the requirements from `requirements.txt` by `$ pip install -r requirements.txt`
3. Serve using gunicorn : `$ gunicorn app:app --worker-class sanic.worker.GunicornWorker`

> You might want to change Mongo Auth in `app.py`
```
def get_client():
	from motor.motor_asyncio import AsyncIOMotorClient

	from sanic import app
	client = AsyncIOMotorClient(host="mongodb://rootuser:passme123@localhost:27045", io_loop=app.get_event_loop())
	return client ```