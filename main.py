import webapp2
import jinja2
import os 
import logging 
import time
import pickle 
import re

from google.appengine.ext import db

SECRET = 'mySecretKey'   #used to Hash cookie 



template_dir = os.path.join(os.path.dirname(__file__), 'templates')
env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
	def write(self, *a , **kwargs):
		self.response.out.write(*a, **kwargs)  

	def render_str(self, template, **kwargs):
		template = env.get_template(template)   
		return template.render(**kwargs)  
 
	def render(self, template, **kwargs):
		self.write(self.render_str(template, **kwargs))

	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))  #log the user by setting cookie to ID

	def set_secure_cookie(self, name, val):
		val = make_secure_val(val) #hash the value
		self.response.headers.add_header('Set-Cookie', '%s=%s ; path = / ' %(name, val))   #set cookie in header

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name, None)  #get the 'name' cookie from the browswer 
		return cookie_val and check_secure_val(cookie_val) #return value if hashID exist



class DictProperty(db.Property):
  data_type = dict

  def get_value_for_datastore(self, model_instance):
    value = super(DictProperty, self).get_value_for_datastore(model_instance)
    return db.Blob(pickle.dumps(value))

  def make_value_from_datastore(self, value):
    if value is None:
      return dict()
    return pickle.loads(value)

  def default_value(self):
    if self.default is None:
      return dict()
    else:
      return super(DictProperty, self).default_value().copy()

  def validate(self, value):
    if not isinstance(value, dict):
      raise db.BadValueError('Property %s needs to be convertible '
                         'to a dict instance (%s) of class dict' % (self.name, value))
    return super(DictProperty, self).validate(value)

  def empty(self, value):
    return value is None


import random
import string
import hashlib

def make_salt():
    return ''.join(random.choice(string.letters) for x in range(5))   

def make_pw_hash(name, pw, salt = None):
    if salt is None:
        salt = make_salt()   #Make Salt only if there is no Salt 
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(",", 1)[1]
    return make_pw_hash(name, pw, salt) == h


import hmac

#get the Hash output from the value using hmac
def hash_str(s): 
    return hmac.new(SECRET, s).hexdigest()

#Return the value and Hash ouptut, used to Set-Cookie 
def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

#get value from cookie 'value | hashoutput'
def check_secure_val(h):
    value = h.rsplit('|', 1)[0]  #split by the first pip | (max 1), starting from the right side
    if h == make_secure_val(value):
        return value	


class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()
	submission = DictProperty()

	@classmethod
	def by_name(cls, name):  #class method to get the entity by the name, do this instead of GQl query
		return cls.all().filter('username =', name).get()

	@classmethod   #create User object
	def register(cls,username, password, email = ""):
		pw_hash = make_pw_hash(username, password)   #Hash and Salt password
		user = User(username = username, password = pw_hash, email = email) #create username, password, email entry 
		return user

	@classmethod
	def login(cls,username, pw):   #check if user and pw is valid from Login page
		u = cls.by_name(username)
		if u and valid_pw(username, pw, u.password):
			return u 
	


class Vote(db.Model):
	question = db.StringProperty(required = True)
	yes = db.IntegerProperty(default=0)
	no = db.IntegerProperty(default=0)
	discussion = db.StringListProperty()
	link = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add = True)



USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def validate_username(username):
   return USER_RE.match(username)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def validate_email(email):
	return not email or EMAIL_RE.match(email)   #check if only email is present 

def validate_password(password):
	if password:
		return True
	else:
		return False

#Check if username is unique
def unique_username(username):
	q = db.GqlQuery("Select * from User")
	for user in q:
		if username == user.username:
			return False 
	return True 

def username_exist(username):
	q = db.GqlQuery("Select * from User")
	for user in q:
		if username == user.username:
			userID = str(user.key().id())
			return True, userID  
	return False, None

class Signup(Handler):  #form and input checking for registration page

	def get(self):
		self.render("registration.html")

	def post(self):
		have_error = False
		self.user_username = self.request.get("username")
		self.user_password = self.request.get("password")
		self.user_verify_pw = self.request.get("verify")
		self.user_email = self.request.get("email")

		param = dict(username = self.user_username,   #Dictionary constructor
						email = self.user_email)

		if not validate_username(self.user_username):
			param['username_error'] = 'Invalid username'
			have_error = True 

		if not validate_password(self.user_password):
		 	param['password_error'] = 'Invalid password'
			have_error = True 
		elif self.user_password != self.user_verify_pw:
			param['password_verify_error'] = "Your passwords didn't match."
			have_error = True
	
		if not validate_email(self.user_email):
			param['email_error'] = 'Invalid email'
			have_error = True


		if have_error:
			self.render("registration.html", **param)
		else:
			self.done()
			

		def done(self, *a, **kw):   #won't be used, registration implements its own 'done' method
			raise NotImplementedError 

class Registration(Signup):  #uses 'get' and 'post' method of Signup
	
	def done(self):
		u = User.by_name(self.user_username)
		if u:
			msg = 'That user already exist'
			self.render("registration.html", username_error = msg)
		else:
			newUser = User.register(self.user_username,    #register user with class method 
					           self.user_password, self.user_email)
			newUser.put()
			self.login(newUser) 
			self.redirect('/')



class Login(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/')
        else:
            msg = 'Incorrect Login. Check and try again'
            self.render('login.html', error = msg)


class NewPost(Handler):
	def get(self):
		self.render("newpost.html")

	def post(self): 
		question = self.request.get("question")
		questionStr = question.replace(" ","")[:-1]

		if len(questionStr) < 5: 
			error = "You did not define a question. Please try again"
			self.render("newpost.html", error = error)
		else:

			if (question):
				v = Vote(question=question, key_name = questionStr, link = "/"+questionStr)
				v.put()
				self.redirect("/%s" %questionStr)


class MainPage(Handler):
	def get(self):
		polls = Vote.all().order('-created').run(limit=10)
		self.render("front.html", polls= polls)

	def post(self): 
		vote = self.request.get("vote")
		pollKey = self.request.get("key")
		question = db.get(pollKey)

		if not question: 
			self.write("Not able to update this poll")
			return 

		if vote == 'yes':
			question.yes+=1
		else:
			question.no+=1

		question.put()
		time.sleep(1)
		self.redirect('/')

class DiscussPage(Handler):

	def get(self, pLString):
		pLString = pLString[1:]
		key = db.Key.from_path('Vote', pLString)
		question = db.get(key)

		if not question:
			self.write("Retrieval Error")
			return 

		self.render("discussPage.html", question = question)

	def post(self, key):
		comment = self.request.get("comment")
		pLString = key[1:]
		key = db.Key.from_path('Vote', pLString)
		question = db.get(key)

		question.discussion.append(comment)
		question.put()
		self.redirect("/%s" %pLString)


class Logout(Handler):
	pass

class EditPage(Handler):
	pass

class WikiPage(Handler):
	pass 


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
	('/signup', Registration),
	('/', MainPage),
	('/newpost', NewPost),
	('/login', Login),
	('/logout', Logout),
	('/_edit' + PAGE_RE, EditPage),
	(PAGE_RE, DiscussPage)
], debug=True)

