import webapp2
import jinja2
import os 




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



class MainPage(Handler):
	def get(self):
		self.render("front.html")

class Signup(Handler):
	def get(self):
		self.render(form)

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
	('/signup', Signup),
	('/login', Login),
	('/logout', Logout),
	('/_edit' + PAGE_RE, EditPage),
	(PAGE_RE, WikiPage)
], debug=True)