from sanic import Sanic
from sanic import response

# from bson.objectid import ObjectId

from pymongo import MongoClient
from umongo import Document,Instance
from umongo.fields import StringField,DateTimeField,EmailField,ReferenceField
from passlib.hash import pbkdf2_sha512

from sanic_jinja2 import SanicJinja2
from sanic_session import RedisSessionInterface
from sanic_auth import Auth, User

from motor.motor_asyncio import AsyncIOMotorClient,AsyncIOMotorDatabase
from datetime import datetime,timedelta

from asyncio_redis import Pool
from bson.objectid import ObjectId


app = Sanic(__name__)

app.static('/static', './static')
app.static('/templates', './')
app.config.AUTH_LOGIN_ENDPOINT = 'hello'

jinja = SanicJinja2(app)

def get_client():
	from motor.motor_asyncio import AsyncIOMotorClient
	# from aiomotorengine.connection import connect

	from sanic import app
	client = AsyncIOMotorClient(host="mongodb://rootuser:passme123@localhost:27045", io_loop=app.get_event_loop())
	return client




class Redis:
	"""
	A simple wrapper class that allows you to share a connection
	pool across your application.
	"""
	_pool = None

	async def get_redis_pool(self):
		if not self._pool:
			self._pool = await Pool.create(
				host='localhost', port=6379, poolsize=10
			)

		return self._pool


redis = Redis()


# pass the getter method for the connection pool into the session
# https://pythonhosted.org/sanic_session/using_the_interfaces.html
session = RedisSessionInterface(redis.get_redis_pool)

sanic_db = get_client().SANIC_TODO
# sanic_db.test_coll.insert({'key':123}) >>> Wokrs
instance = Instance(sanic_db)

'''
MODELS
'''

@instance.register
class User(Document):
	name = StringField(required = True)
	username = StringField(required = True)
	password = StringField(required = True)
	email = EmailField(required = True , unique = True)
	joined_on = DateTimeField(default = datetime.utcnow() + timedelta(hours=5,minutes=30))

	def set_password(self, password):
		self.password = pbkdf2_sha512.hash(password)

	def verify_password(self, password):
		return pbkdf2_sha512.verify(password, self.password)


@instance.register
class Task(Document):
	user = ReferenceField(User)
	title = StringField(required = True, max_length = 100)
	desc = StringField(required = True)
	mark_as = StringField(max_length = 8)

'''
END OF MODELS
'''
@app.middleware('request')
async def add_session_to_request(request):
	await session.open(request)

@app.middleware('response')
async def save_session(request, response):
	await session.save(request, response)

auth = Auth(app)

@auth.serializer
def serializer(user):
	return {'uid':str(user.id),'email':user.email,'name':user.name}

@auth.user_loader
def user_loader(user):
	return user


@app.route('/')
async def hello(request):
	return jinja.render('index.html', request, username = auth.current_user(request))


@app.route('/signup',methods=['POST'])
async def signup(request):
	try:
		data = request.json.get('form',None)
		username = data.get('username',None)
		password = data.get('password',None)
		name = data.get('name',None)
		email = data.get('email',None)

		assert username and name and password and email is not None

		this_user = await User.find_one({'email':email})
		assert this_user is None
		new_user = User(name=name,username=username,email=email)
		new_user.set_password(password)
		await new_user.commit()
		return response.json({'status':True, 'message':"Signup success"})
	except AssertionError as ae:
		raise ae
		return response.json({'status':False, 'message':"Signup failed, email already exist"})
	except Exception as other_e:
		print(other_e)
		return response.json({'status':False, 'message':"Houston we have a problem here!"})

@app.route('/login', methods=['POST','GET'])
async def login(request):
	try:
		data = request.json.get('form',None)
		email = data.get('email',None)
		password = data.get('password',None)

		assert email and password is not None

		this_user = await User.find_one({'email':email})
		if this_user.verify_password(password):
			
			auth.login_user(request, this_user)
			return response.json({'status':True, 'message':"Login success"})
		else:
			# Wrong password actually
			return response.json({'status':False, 'message':"Login failed, Invalid credentials!"})
	except AttributeError as ate:
		# Email doesnt exist
		print(ate)
		return response.json({'status':False, 'message':"Umm, that email seems new to us!"})


	except AssertionError as ae:
		print(ae)
		return response.json({'status':False, 'message':"Login failed due to bad request"}, status=403)


@app.route('/logout')
async def logout(request):
	try:
		auth.logout_user(request)
		return response.json({'status':True, 'message':"Logout success, redirecting you now..."})
	except Exception as e:
		raise e


@app.route('/get_tasks',methods=['GET'])
@auth.login_required
async def get_tasks(request):
	try:
		tasks = []
		current_user = await User.find_one({'email':auth.current_user(request)['email']})

		async for task in Task.find({'user':current_user.id}):
			tasks.append({'title':task.title, 'description':task.desc, 'id':str(task.id)})

		return response.json({'status':True,'tasks':tasks})
	except Exception as e:
		raise e

@app.route('/tasks/add_task',methods=['POST'])
@auth.login_required
async def add_task(request):
	try:
		data = request.json.get('form',None)
		title = data.get('title',None)
		description = data.get('description',None)

		assert title and description is not None

		current_user = await User.find_one({'email':auth.current_user(request)['email']})

		new_task = Task(user = current_user.id, title=title, desc=description)
		await new_task.commit()

		tasks = []
		async for task in Task.find({'user':current_user.id}):
			tasks.append({'title':task.title, 'description':task.desc, 'id':str(task.id)})

		return response.json({'status':True,'tasks':tasks})
	except AssertionError as ae:
		print(ae)
		return response.json({'status':False, 'message':"Could not add the todo"}, status=403)
	except Exception as e:
		print(e)
		return response.json({'status':False, 'message':"Could not add the todo"})


@app.route('/tasks/edit_task',methods=['POST'])
@auth.login_required
async def edit_task(request):
	try:
		data = request.json.get('task',None)
		_id = data.get('id',None)
		title = data.get('title',None)
		description = data.get('description',None)

		assert title and description is not None

		current_user = await User.find_one({'email':auth.current_user(request)['email']})

		this_task = await Task.find_one({'id':ObjectId(_id),'user':current_user.id})
		this_task.update({'title':title,'desc':description})
		await this_task.commit()

		tasks = []
		async for task in Task.find({'user':current_user.id}):
			tasks.append({'title':task.title, 'description':task.desc, 'id':str(task.id)})

		return response.json({'status':True,'tasks':tasks})
	except AssertionError as ae:
		print(ae)
		return response.json({'status':False, 'message':"Could not edit the todo, Empty field"}, status=403)
	except Exception as e:
		print(e)
		return response.json({'status':False, 'message':"Could not edit the todo"})



@app.route('/tasks/remove_task',methods=['POST'])
@auth.login_required
async def remove_task(request):
	try:
		task_id = request.json.get('task',None)
		current_user = await User.find_one({'email':auth.current_user(request)['email']})

		task = await Task.find_one({'id':ObjectId(task_id),'user':current_user.id})
		result = await task.remove()

		tasks = []
		async for task in Task.find({'user':current_user.id}):
			tasks.append({'title':task.title, 'description':task.desc, 'id':str(task.id)})

		return response.json({'status':True,'tasks':tasks})

	except Exception as e:
		print(e)
		return response.json({'status':False, 'message':"Could not remove the todo"})

	
@app.route('/dashboard')
@auth.login_required
async def dashboard(request):
	return response.json({'dashboard':1000})

