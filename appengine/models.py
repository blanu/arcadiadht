from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore

class Challenge(db.Model):
  pubkey=db.StringProperty(required=True)
  challenge=db.StringProperty(required=True)

class Node(db.Model):
  pubkey=db.StringProperty(required=True)
  privkey=db.StringProperty(required=True)

class Neighbor(db.Model):
  pubkey=db.StringProperty(required=True)
  distance=db.IntegerProperty(required=True)

class Data(db.Model):
  datakey=db.StringProperty(required=True)
  value=db.TextProperty()

