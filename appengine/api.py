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

class NewDatabasePage(JsonPage):
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

class DatabasesPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    dbs=Database.all().filter("owner =", user).fetch(10)
    results=[]
    for db in dbs:
      results.append(db.dbid)

#    notify('freefall', 'dbs-'+user.email().lower()+'-newtab', dumps({'name': name, 'id': wave.waveid}))

    return results

  def requireLogin(self):
    return True

class DatabasePage(JsonPage):
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

class DocumentPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    logging.info('document')
    logging.info(method)

    dbid=args[0]
    docid=args[1]

    db=Database.all().filter("owner =", user).filter("dbid =", dbid).get()
    if not db:
      logging.error('Database with that id does not exist '+str(dbid))
      return None

    if method=='GET':
      doc=Document.all().filter("database =", db).filter('docid =', docid).get()
      if not doc:
        logging.error('Document with that id does not exist '+str(docid))
        return None
      return doc.state
    elif method=='POST':
      doc=newDocument(db, obj, docid=docid)
      if not doc:
        logging.error('Document id collision '+str(docid)+', overwriting...')
        doc=Document.all().filter("docid =", docid).get()
        logging.error('state: '+str(doc.state))
        doc.state=dumps(obj)
        doc.save()
        logging.error('state: '+str(doc.state))

        return doc.docid
      else:
        docs=Document.all().filter('database =', db).fetch(10)
        results=[]
        for rdoc in docs:
          results.append(rdoc.docid)

        logging.info('results: '+str(results))

        logging.debug('notifying')
        notify('freefall', 'docs-'+user.email().lower()+'-'+db.dbid, dumps(results))
        logging.debug('notified')

        return doc.docid
    else:
      logging.error('Unknown method '+str(method))

  def requireLogin(self):
    return True

class DeleteWavePage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    waveId=args[0]

    wave=Wave.all().filter("waveid =", waveId).get()
    if not wave:
      return
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return

    tab=Tab.all().filter('user =', user).filter("wave =", wave).get()
    tab.delete()
    notify('wavetabs', 'wave-'+user.email().lower()+'-deltab', dumps(wave.waveid))

    participant.delete()
    participants={}
    ps=Participant.all().filter("wave =", wave).fetch(10)
    for p in ps:
      participants[p.user.email().lower()]={'nickname': p.user.nickname(), 'email': p.user.email().lower()}
    notify('wavetabs', 'wave-'+waveId+'-participants', dumps(participants))

  def requireLogin(self):
    return True

class RenameWavePage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    waveId=args[0]

    wave=Wave.all().filter("waveid =", waveId).get()
    if not wave:
      return
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return

    tab=Tab.all().filter('user =', user).filter("wave =", wave).get()
    tab.name=obj
    tab.save()

    notify('wavetabs', 'wave-'+user.email().lower()+'-renametab', dumps({wave.waveid: tab.name}))

  def requireLogin(self):
    return True

class GadgetStatePage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    logging.debug('WSP')
    gid=args[0]

    state={}

    gadget=Gadget.all().filter('gadgetid =', gid).get()
    if not gadget:
      logging.error('No gadget with id '+str(gadgetid))
      return state
    wave=gadget.wave
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('User is not a participant in this wave')
      return state
    if gadget.scratch:
      state['scratch']=gadget.scratch
    shards=Shard.all().filter("gadget =", gadget).fetch(10)
    if shards:
      for shard in shards:
        if shard.state:
          state[shard.user.email().lower()]=loads(shard.state)

    logging.debug('WSP returning: '+str(state))

    return state

  def requireLogin(self):
    return True

class WaveParticipantsPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    waveId=args[0]
    logging.debug('waveId: '+str(waveId))

    participants={}

    wave=Wave.all().filter("waveid =", waveId).get()
    if not wave:
      return participants
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return participants
    ps=Participant.all().filter("wave =", wave).fetch(10)
    for p in ps:
      participants[p.user.email().lower()]={'nickname': p.user.nickname(), 'email': p.user.email().lower()}

    return participants

  def requireLogin(self):
    return True

class WaveInvitesPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    waveId=args[0]
    logging.debug('waveId: '+str(waveId))

    invites=[]

    wave=Wave.all().filter("waveid =", waveId).get()
    if not wave:
      return invites
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return invites
    ivs=Invitation.all().filter("wave =", wave).fetch(10)
    for i in ivs:
      invites.append(i.email.lower)

    return invites

  def requireLogin(self):
    return True

class InvitesPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    invites=[]
    email=user.email().lower()
    logging.debug('finding invitations for '+str(email))
    ivs=Invitation.all().filter("email =", email).fetch(10)
    for i in ivs:
      invites.append(i.wave.waveid)

    return invites

  def requireLogin(self):
    return True

class ContactsPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    gd_client = gdata.contacts.service.ContactsService()

    auth=AuthToken.all().filter('user =', user).get()
    if not auth:
      return []

    logging.debug('token: '+str(auth.token));
    gd_client.SetAuthSubToken(auth.token)

    contacts=[]
#    feed = gd_client.GetContactsFeed()
    query = gdata.contacts.service.ContactsQuery()
    query.max_results=1000
    feed = gd_client.GetContactsFeed(query.ToUri())
    logging.debug('contacts #:'+str(len(feed.entry)))
    for i, entry in enumerate(feed.entry):
#      logging.debug('entry: '+str(dir(entry)))
      contact={}
      match=False
      if entry.title:
        contact['title']=entry.title.text
      if entry.email:
        for email in entry.email:
          if email.address and '@' in email.address and email.address.split('@')[1]=='gmail.com':
            contact['email']=email.address
            match=True
      if match:
        img = gd_client.GetPhoto(entry)
        if img:
          contact['image']='data:image/jpg;base64,'+base64.b64encode(img)
        else:
          contact['image']=None
        contacts.append(contact)
      else:
        for email in entry.email:
          logging.debug('Rejecting '+str(email.address));

    return sorted(contacts, cmp=self.emailSort)

  def emailSort(self, a, b):
    try:
      ka=a['title']
    except:
      ka=a['email']
    try:
      kb=b['title']
    except:
      kb=b['email']
    return a.__cmp__(b)

  def requireLogin(self):
    return True

class AuthPage(TemplatePage):
  def processContext(self, method, user, req, resp, args, context):
    gd_client = gdata.contacts.service.ContactsService()

    token=req.get('token')
    logging.debug('token: '+str(token))
    if token and token!='':
      gd_client.SetAuthSubToken(token)
      gd_client.UpgradeToSessionToken()
      token=gd_client.GetAuthSubToken()
      a=AuthToken(user=user, token=token)
      a.save()

    contacts=[]
#    feed = gd_client.GetContactsFeed()
    query = gdata.contacts.service.ContactsQuery()
    query.max_results=1000
    feed = gd_client.GetContactsFeed(query.ToUri())
    logging.debug('contacts #:'+str(len(feed.entry)))
    for i, entry in enumerate(feed.entry):
#      logging.debug('entry: '+str(dir(entry)))
      contact={}
      match=False
      if entry.title:
        contact['title']=entry.title.text
      if entry.email:
        for email in entry.email:
          if email.address and '@' in email.address and email.address.split('@')[1]=='gmail.com':
            contact['email']=email.address
            match=True
      if match:
        img = gd_client.GetPhoto(entry)
        if img:
          contact['image']='data:image/jpg;base64,'+base64.b64encode(img)
        else:
          contact['image']=None
        contacts.append(contact)
      else:
        for email in entry.email:
          logging.debug('Rejecting '+str(email.address));

    contacts=sorted(contacts, cmp=self.emailSort)
    notify('wavetabs', 'user-'+user.email()+'-contacts', dumps(contacts))

  def emailSort(self, a, b):
    try:
      ka=a['title']
    except:
      ka=a['email']
    try:
      kb=b['title']
    except:
      kb=b['email']
    return a.__cmp__(b)

  def requireLogin(self):
    return True

class WaveAddParticipantsPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    waveId=args[0]
    logging.debug('waveId: '+str(waveId))
    logging.debug('obj: '+str(obj));

    wave=Wave.all().filter("waveid =", waveId).get()
    if not wave:
      return
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return

    context={'wave': waveId}

    if obj==None:
      logging.error('AddParticipants: client posted nothing')
      return
    email=obj
    if not mail.is_email_valid(email):
      logging.error('Bad email: '+str(email))
      return
    logging.debug('email: '+str(email))

    u=users.User(email=email)
    logging.debug('u: '+str(u))
    if Participant.all().filter("wave =", wave).filter("user =", u).count()==0:
      p=Participant(wave=wave, user=u);
      p.save()

    participants={}
    ps=Participant.all().filter("wave =", wave).fetch(10)
    for p in ps:
      participants[p.user.email().lower()]={'nickname': p.user.nickname(), 'email': p.user.email().lower()}

    logging.debug('ps: '+str(participants))

    notify('wavetabs', 'wave-'+waveId+'-participants', dumps(participants))

    oldtab=Tab.all().filter('wave =', wave).filter('user =', user).get()
    index=Tab.all().filter('user =', u).count()
    newtab=Tab(wave=wave, user=u, name=oldtab.name, index=index)
    newtab.save()
    if u.email():
      logging.debug('adding new tab')
      notify('wavetabs', 'wave-'+u.email().lower()+'-newtab', dumps({'name': oldtab.name, 'id': wave.waveid}))
    else:
      logging.error('No userid: '+str(u))

    context['name']=newtab.name
    sendMail(user.email().lower(), email, 'Invitation to Wavetabs', 'invite', context)

  def requireLogin(self):
    return True

class WaveAddInvitePage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    waveId=args[0]
    logging.debug('waveId: '+str(waveId))
    logging.debug('obj: '+str(obj));

    wave=Wave.all().filter("waveid =", waveId).get()
    if not wave:
      return
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return

    context={'wave': waveId}

    if obj==None:
      logging.error('AddInvite: client posted nothing')
      return
    email=obj
    if not mail.is_email_valid(email):
      logging.error('Bad email: '+str(email))
      return
    logging.debug('email: '+str(email))

    dup=False
    if Invitation.all().filter("wave =", wave).filter("email =", email).count()==0:
      ps=Participant.all().filter("wave =", wave).fetch(10)
      for p in ps:
        if p.user.email().lower()==email.lower():
          dup=True
          break
    if not dup:
      invite=Invitation(wave=wave, user=user, email=email)
      invite.save()

      invites=[]
      ivs=Invitation.all().filter("wave =", wave).fetch(10)
      for i in ivs:
        invites.append(i.email)

      oldtab=Tab.all().filter('wave =', wave).filter('user =', invite.user).get()

      notify('wavetabs', 'wave-'+waveId+'-invites', dumps(invites))
      notify('wavetabs', 'user-'+email+'-invite', dumps(waveId))

      context['name']=oldtab.name
      sendMail(user.email().lower(), email, 'Invitation to Wavetabs', 'invite', context)

  def requireLogin(self):
    return True

class GadgetAddLinkPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    gid=args[0]

    logging.debug('adding link '+str(gid)+' '+str(obj))

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      logging.error('No such gadget '+str(gid))
      return
    wave=gadget.wave;
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return

    if obj==None:
      logging.error('AddLink: client posted nothing')
      return
    uri=urllib.unquote(obj)

    if gadget.linkbot:
      logging.debug('linkbot: '+str(gadget.linkbot))
      payload=dumps({'gadget': gadget.gadgetid, 'link': obj})
      result=urlfetch.fetch(url=gadget.linkbot, payload=payload, method=urlfetch.POST)
      if result.status_code==200:
        uri=loads(result.content)
        if not uri:
          logging.info('Linkbot vetoed link '+str(gadget.linkbot))
          return

    if Link.all().filter("gadget =", gadget).filter("uri =", uri).count()==0:
      logging.debug('New link')
      link=Link(gadget=gadget, host=participant, uri=uri)
      link.save()

      links=[]
      ls=Link.all().filter("gadget =", gadget).fetch(10)
      for l in ls:
        links.append(l.uri)

      notify('wavetabs', 'gadget-'+gid+'-links', dumps(links))

  def requireLogin(self):
    return True

class GadgetLinkPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    gid=args[0]

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave;
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return

    links=[]
    ls=Link.all().filter("gadget =", gadget).fetch(10)
    for l in ls:
      links.append(l.uri)

    return links

  def requireLogin(self):
    return True

class TorrentsBotPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    logging.debug('torrents bot: '+str(obj))

    """
    headers={'Authorization': 'Basic '+base64.b64encode('admin:')}

    result=urlfetch.fetch(url='http://blanu.net:8899/gui/token.html', headers=headers)
    if result.status_code==200:
      logging.debug('content: '+str(result.content))
      match=re.search(">([^<]+)</div>", result.content)
      token=match.group(1)
      logging.debug('token: '+str(token))
    else:
      logging.debug('failed status code: '+str(result.status_code))
    """

    tc=transmissionrpc.Client('localhost', port=8899)

    if obj:
      try:
        link=obj['link']
      except:
        return None

    logging.debug('link: '+str(link))

    tc.add_uri(link)
    logging.debug(str(tc.list()))

    """
    params=urllib.urlencode({'action': 'add-url', 's': link})

#    url='http://blanu.net:8899/gui/?token='+token+'&action=add-url&s='+urllib.quote_plus(link)
    url="http://blanu.net:8899/gui/?token="+token+"&%s" % params
    result=urlfetch.fetch(url=url, headers=headers)
    logging.debug('tried to add torrent: '+str(result.status_code))
    """

    return None

  def requireLogin(self):
    return False

class GadgetAttachmentsPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    gid=args[0]

    attachments=[]

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return {}
    ats=Attachment.all().filter("gadget =", gadget).fetch(100)
    for a in ats:
      attachments.append({'name': a.blobid.filename,'id': str(a.blobid.key())})

    return attachments

  def requireLogin(self):
    return True

class GadgetScratchPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    gid=args[0]
    logging.debug('gid: '+str(gid))
    logging.debug('obj: ')
    logging.debug(obj)
    logging.debug(dumps(obj))

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return
    gadget.scratch=dumps(obj)
    gadget.save()

    if gadget.scratch:
      state={'scratch': loads(gadget.scratch)}
    else:
      state={}

    shards=Shard.all().filter("gadget =", gadget).fetch(10)
    for shard in shards:
      if shard.state:
        state[str(shard.user.email().lower())]=loads(shard.state)

    notify('wavetabs', 'gadget-'+gid+'-state', dumps(state))

  def requireLogin(self):
    return True

class GadgetShardPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    gid=args[0]

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave
    if not wave:
      return
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return
    shard=Shard.all().filter("participant =", participant).get()
    if not shard:
      shard=Shard(gadget=gadget, user=user, participant=participant, state=dumps(obj))
      shard.save()
    else:
      shard.state=dumps(obj)
      shard.save()

    if gadget.scratch:
      state={'scratch': loads(gadget.scratch)}
    else:
      state={}

    shards=Shard.all().filter("gadget =", gadget).fetch(10)
    for shard in shards:
      if shard.state:
        state[str(shard.user.email().lower())]=loads(shard.state)

    notify('wavetabs', 'gadget-'+gid+'-state', dumps(state))

  def requireLogin(self):
    return True

class WaveGadgetPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    waveId=args[0]
    logging.debug('waveId: '+str(waveId))
    logging.debug('obj: '+str(obj))

    wave=Wave.all().filter("waveid =", waveId).get()
    if not wave:
      return
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return
    gadget=newGadget(wave=wave, host=participant, url=obj)
    gadget.save()

  def requireLogin(self):
    return True

class GadgetBlobPage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    gid=args[0]

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return
    uploadUrl = blobstore.create_upload_url('/gadget/upload/'+gid)
    return uploadUrl

  def requireLogin(self):
    return True

class GadgetUploadPage(blobstore_handlers.BlobstoreUploadHandler):
  def post(self, gid):
    user = users.get_current_user()

    upload_files = self.get_uploads('file')
    blob_info = upload_files[0]
    logging.debug('blob_info: '+str(blob_info))

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave
    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
    if not participant:
      logging.error('user is not a participant in this wave')
      return
    attachment=Attachment(gadget=gadget, host=participant, blobid=blob_info.key())
    attachment.save()

    attachments=[]
    ats=Attachment.all().filter("gadget =", gadget).fetch(100)
    for a in ats:
      attachments.append({'name': a.blobid.filename,'id': str(a.blobid.key())})

    notify('wavetabs', 'gadget-'+gid+'-attachments', dumps(attachments))

    self.response.set_status(301)

class GadgetAttachmentPage(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, gid, resource):
    resource = str(urllib.unquote(resource))

    blobkey=blobstore.BlobKey(resource)

#    user = users.get_current_user()

#    if not user:
#      self.redirect(users.create_login_url(self.request.uri))

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave
#    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
#    if not participant:
#      logging.error('user is not a participant in this wave')
#      return
    attachment=Attachment.all().filter("gadget =", gadget).filter("blobid =", blobkey).get()
    if not attachment:
      return

    blob_info = blobstore.BlobInfo.get(blobkey)
    self.response.headers.add_header('Content-Disposition', 'attachment; filename='+blob_info.filename)
    self.send_blob(blob_info)

class GadgetAttachmentDeletePage(JsonPage):
  def processJson(self, method, user, req, resp, args, obj):
    logging.debug('delete')
    gid=args[0]
    resource=args[1]
    resource = str(urllib.unquote(resource))

    blobkey=blobstore.BlobKey(resource)

#    user = users.get_current_user()

#    if not user:
#      self.redirect(users.create_login_url(self.request.uri))

#    participant=Participant.all().filter("user =", user).filter("wave =", wave).get()
#    if not participant:
#      logging.error('user is not a participant in this wave')
#      return

    gadget=Gadget.all().filter("gadgetid =", gid).get()
    if not gadget:
      return
    wave=gadget.wave
    attachment=Attachment.all().filter("gadget =", gadget).filter("blobid =", blobkey).get()
    if not attachment:
      return

    logging.debug('deleting: '+str(blobkey))
    blobstore.delete(blobkey)
    logging.debug('deleting: '+str(attachment))
    attachment.delete()

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
