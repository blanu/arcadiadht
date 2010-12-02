from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from pages import *

application = webapp.WSGIApplication([
#  ('/admin', AdminIndexPage),
#  ('/admin/curated', AdminCuratedPage),
#  ('/admin/curated/new', AdminNewCuratedPage),
], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
