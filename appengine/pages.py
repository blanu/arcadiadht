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
    logging.debug("dashboard index")
    context['userid']=user.email().lower()

  def requireLogin(self):
    return True

class DashboardDatabasePage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    dbid=args[0]
    logging.debug("dashboard db "+str(dbid))
    context['userid']=user.email().lower()
    context['dbid']=dbid

  def requireLogin(self):
    return True

class DashboardDocumentPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    dbid=args[0]
    docid=args[1]

    logging.debug("dashboard doc "+str(dbid)+'/'+str(docid))
    context['userid']=user.email().lower()
    context['dbid']=dbid
    context['docid']=docid

  def requireLogin(self):
    return True

class WavePage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    waveId=unquote_plus(args[0])
    logging.debug('wave page: '+str(waveId))
    context['userid']=user.email().lower()
    wave=Wave.all().filter("waveid =", waveId).get()
    logging.debug("wave: "+str(wave));
    if not wave:
      return
    context['wave']=wave
    gadgets=Gadget.all().filter("wave =", wave).fetch(10)
    logging.debug('gadgets: '+str(gadgets))
    if not gadgets or len(gadgets)==0:
      context['gadgets']=None
    else:
      context['gadgets']=gadgets

  def requireLogin(self):
    return True

class AdminIndexPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    pass

class AdminCuratedPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    pass

class AdminNewCuratedPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    logging.debug('curated new')
    name=req.get('name')
    url=req.get('url')
    iconUrl=req.get('iconUrl')
    linkbot=req.get('linkbot')
    if linkbot.strip()=='':
      linkbot=None

    c=Curated(name=name, url=url, iconUrl=iconUrl, linkbot=linkbot)
    c.save()
