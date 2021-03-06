import re
import logging
import random
import base64
import struct
import time

import urllib
from urllib import urlencode, unquote_plus

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import users
from google.appengine.api import mail
from django.utils.simplejson import loads, dumps

from airspeed import CachingFileLoader

from generic import TemplatePage, GenericPage, FilePage
from models import *
from util import *

class IndexPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    logging.debug("index")
    if not user:
      self.redirect('/welcome')
    else:
      self.redirect('/dashboard')

  def requireLogin(self):
    return False

class WelcomePage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    pass

  def requireLogin(self):
    return False

class LoginPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    self.redirect('/')

  def requireLogin(self):
    return True

class DashboardIndexPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    pass

  def requireLogin(self):
    return True
