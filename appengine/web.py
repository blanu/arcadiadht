from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from pages import *
from api import *

application = webapp.WSGIApplication([
  ('/', IndexPage),
  ('/index.html', IndexPage),
  ('/welcome', WelcomePage),
  ('/login', LoginPage),

  ('/data/(.)', DataPage),
  ('/challenge', ChallengePage),
  ('/addPeer', AddPeerPage),
], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
