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

from generic import TemplatePage, JsonPage, GenericPage, FilePage
from models import *

def notify(apikey, channel, msg):
  logging.debug('notify:')
  logging.debug(msg)

  fields={
    'apikey': apikey,
    'channel': channel,
    'data': msg
  }

  url='http://send.w2p.dtdns.net:9323/send'
  result=urlfetch.fetch(url, payload=urlencode(fields), method=urlfetch.POST)
  logging.debug('post result: '+str(result.status_code))

def sendMail(frm, to, subject, templateName, context):
  loader = CachingFileLoader("templates")

  templateNameHTML=templateName+".vm"
  templateHTML = loader.load_template(templateNameHTML)
  bodyHTML=templateHTML.merge(context, loader=loader)

  templateNamePlain=templateName+"_plain.vm"
  templatePlain = loader.load_template(templateNamePlain)
  bodyPlain=templatePlain.merge(context, loader=loader)

  #    resp.headers['Content-Type']='text/html'
  msg=mail.EmailMessage(sender=frm, to=to, subject=subject)
  msg.html=bodyHTML
  msg.body=bodyPlain

  msg.send()

def generateId():
  s=None
  if not (s and s[0].isalpha()):
    i=random.getrandbits(64)
    s=base64.urlsafe_b64encode(struct.pack('L', i))[:-1]
  while s[-1]=='A' or s[-1]=='=':
    s=s[:-1]

  return s

def newDatabase(owner, dbid=None):
  logging.error('nd dbid: '+str(dbid))
  if not dbid:
    logging.debug('no dbid')
    dbid=generateId()
    while Database.all().filter("dbid =", dbid).count()!=0:
      dbid=generateId()
  elif Database.all().filter("owner =", owner).filter("dbid =", dbid).count()!=0:
    return None

  logging.info('using '+str(dbid))
  db=Database(dbid=dbid, owner=owner)
  db.save()
  return db

def newDocument(db, state, docid=None):
  if not docid:
    docid=generateId()
    while Document.all().filter("docid =", docid).count()!=0:
      docid=generateId()
  elif Document.all().filter("docid =", docid).count()!=0:
    return None

  doc=Document(docid=docid, database=db, state=state)
  doc.save()
  return doc
