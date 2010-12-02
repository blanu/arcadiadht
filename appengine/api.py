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

class DataPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    logging.info('new database')
    logging.info(obj)
    if obj:
      try:
        dbid=obj['dbid']
      except:
        dbid=None
    else:
      dbid=None

    logging.info('dbid: '+str(dbid))

    try:
      db=newDatabase(user, dbid=dbid)
    except Exception, e:
      logging.error(str(e))
    if not db:
      logging.error('Database with that id already exists '+str(dbid))
      return None
    else:
      logging.error('db: '+str(db))
      logging.info('dbid: '+str(db.dbid))

      dbs=Database.all().filter("owner =", user).fetch(10)
      results=[]
      for rdb in dbs:
        results.append(rdb.dbid)

      logging.info('results: '+str(results))

      notify('freefall', 'dbs-'+user.email().lower(), dumps(results))

      return db.dbid

  def requireLogin(self):
    return True

class ChallengePage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    dbs=Database.all().filter("owner =", user).fetch(10)
    results=[]
    for db in dbs:
      results.append(db.dbid)

#    notify('freefall', 'dbs-'+user.email().lower()+'-newtab', dumps({'name': name, 'id': wave.waveid}))

    return results

  def requireLogin(self):
    return True

class AddPeerPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    dbid=args[0]

    if method=='GET':
      db=Database.all().filter("owner =", user).filter("dbid =", dbid).get()
      if not db:
        logging.error('Database with that id does not exist '+str(dbid))
        return

#    notify('freefall', 'dbs-'+user.email().lower()+'-newtab', dumps({'name': name, 'id': wave.waveid}))

      results=[]
      docs=Document.all().filter("database =", db).fetch(10)
      for doc in docs:
        results.append(doc.docid)

      return results
    elif method=='POST':
      doc=newDocument(db, obj)
      if not doc:
        logging.error('Document id collision '+str(docid)+', overwriting...')
        doc.state=obj
        doc.save()
        return None
      else:
        docs=Document.all().filter('database =', db).fetch(10)
        results=[]
        for rdoc in docs:
          results.append(rdoc.docid)

        logging.info('results: '+str(results))

        notify('freefall', 'docs-'+user.email().lower()+'-'+db.dbid, dumps(results))

        return doc.docid
    else:
      logging.error('Unknown method '+str(method))

  def requireLogin(self):
    return True
