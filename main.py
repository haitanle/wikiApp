import webapp2



class MainHandler(webapp2.RequestHandler):
	def get(self):
		self.response.write("Welcome to askCharlotte99.com")

class Signup(MainHandler):
	def get(self):
		self.render(form)

class Login(MainHandler):
	pass

class Logout(MainHandler):
	pass

class EditPage(MainHandler):
	pass

class WikiPage(MainHandler):
	pass 


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
	('/', MainHandler),
	('/signup', Signup),
	('/login', Login),
	('/logout', Logout),
	('/_edit' + PAGE_RE, EditPage),
	(PAGE_RE, WikiPage)
], debug=True)