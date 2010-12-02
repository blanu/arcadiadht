from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore

class Database(db.Model):
  dbid=db.StringProperty(required=True)
  owner=db.UserProperty(required=True)

class Document(db.Model):
  docid=db.StringProperty(required=True)
  database=db.ReferenceProperty(Database, required=True)
#  participant=db.ReferenceProperty(Participant)
  state=db.TextProperty()

class View(db.Model):
  viewid=db.StringProperty(required=True)

#class Participant(db.Model):
#  wave=db.ReferenceProperty(Wave, required=True)
#  user=db.UserProperty(required=True)

#class Shard(db.Model):
#  gadget=db.ReferenceProperty(Gadget, required=True)
