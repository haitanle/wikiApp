import webapp2
import jinja2
import os 
import logging 

from google.appengine.ext import db


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

class Vote(db.Model):
	question = db.StringProperty(required = True)
	yes = db.IntegerProperty(default=0)
	no = db.IntegerProperty(default=0)
	discussion = db.StringListProperty()
	created = db.DateTimeProperty(auto_now_add = True)


class NewPost(Handler):
	def get(self):
		self.render("newpost.html")

	def post(self): 
		question = self.request.get("question")
		questionStr = question.split()

		if len(questionStr) < 5: 
			error = "You did not define a question. Please try again"
			self.render("newpost.html", error = error)
		else:
			pLString = "" + questionStr[1] + questionStr[2] + questionStr[4]
			
			if (question):
				v = Vote(question=question, key_name = pLString)
				v.discussion.append("test my new post")
				v.discussion.append("another test")
				v.put()
				self.redirect("/%s" %pLString)


class DiscussPage(Handler):

	def get(self, pLString):
		pLString = pLString[1:]
		key = db.Key.from_path('Vote', pLString)
		question = db.get(key)

		if not question:
			self.write("Retrieval Error")
			return 

		self.render("discussPage.html", question = question)


			


class Signup(Handler):
	def get(self):
		self.render(form)

class MainPage(Handler):
	def get(self):
		self.render("front.html")



class Login(Handler):
	pass

class Logout(Handler):
	pass

class EditPage(Handler):
	pass

class WikiPage(Handler):
	pass 


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
	('/', MainPage),
	('/newpost', NewPost),
	('/signup', Signup),
	('/login', Login),
	('/logout', Logout),
	('/_edit' + PAGE_RE, EditPage),
	(PAGE_RE, DiscussPage)
], debug=True)

