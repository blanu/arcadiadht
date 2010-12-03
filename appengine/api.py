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

from generic import JsonPage
from models import *
from util import *

# Peer API
class ChallengePage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    pubkey=args[0]

    chal=Challenge.all().filter("pubkey =", pubkey).get()
    if chal:
      print('Already issued a challenge for '+str(pubkey)+': '+str(chal.challenge))
    else:
      chal=Challenge(pubkey=pubkey, challenge=generateId())
      chal.save()
      print('New challenge for '+str(pubkey)+': '+str(chal.challenge))

    return chal.challenge

  def requireLogin(self):
    return False

class AddPeerPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    pubkey=args[0]

    print('Add peer '+str(pubkey)+': '+str(obj))

    chal=Challenge.all().filter('pubkey =', pubkey).get()
    if chal.challenge!=obj['challenge']:
      print('Challenges do not match '+str(obj['challenge'])+', '+str(chal.challenge))
      return
    if not verify(chal.challenge, obj['response'], pubkey):
      print('Signature does not verify '+str(obj['response']))
      return

    # Add peer locally or pass on to nearest neighbor

  def requireLogin(self):
    return False

class DataPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    key=args[0]

    if method=='GET':
      data=Data.all().filter("datakey =", key).get()
      if not data:
        logging.error('Data with that key does not exist '+str(key))
        return
      else:
        return data.value
    elif method=='POST':
      data=Data.all().filter("datakey =", key).get()
      if not data:
        logging.error('Writing data to new key: '+str(key))
        return
      else:
        data=Data(datakey=key, value=obj)
        data.save()
    else:
      logging.debug('Unknown method: '+str(method))

  def requireLogin(self):
    return False

# Client API
class ClientDataPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    key=args[0]

    if method=='GET':
      data=Data.all().filter("datakey =", key).get()
      if not data:
        logging.error('Data with that key does not exist '+str(key))
        return
      else:
        logging.error('Found value '+str(data.value))
        return loads(data.value)
    elif method=='POST':
      value=req.get('value')
      data=Data.all().filter("datakey =", key).get()
      if not data:
        logging.error('Writing data to new key: '+str(key)+' '+dumps(obj))
        data=Data(datakey=key, value=value)
        data.save()
        logging.error('Wrote data: '+str(data.datakey)+' '+str(data.value))
      else:
        data.value=value
        data.save()
        logging.error('Wrote data: '+str(data.datakey)+' '+str(data.value))
    else:
      logging.debug('Unknown method: '+str(method))

  def requireLogin(self):
    return False
