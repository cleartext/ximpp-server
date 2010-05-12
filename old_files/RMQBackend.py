#!/usr/bin/env python

import time
import datetime
import threading

from Backend import Backend, Message, message_compare

import amqplib.client_0_8 as amqp


class RMQBackend (Backend):
  def __init__(self, server, userid, password):
    Backend.__init__(self)

    self.server      = server
    self.password    = password
    self.messages    = {}
    self.contacts    = {}
    self.subscribers = {}
    self.connection  = None
    self.channel     = None

    self.messages = { 
      'peter' : [
          Message(datetime.datetime(2008, 01, 01), 'peter', 'Reading some XMPP specs'),
          Message(datetime.datetime(2008, 01, 03), 'peter', '@kevin Tell me about it')
        ],
      'kevin' : [
          Message(datetime.datetime(2008, 01, 02), 'kevin', 'Too little time to do all the things I want to')
        ],
      'remko' : [
          Message(datetime.datetime(2008, 01, 04), 'remko', 'Woohoow, holidays!')
        ]}
    self.contacts = { 'remko' : ['kevin', 'peter'] }
    self.subscribers = { 'kevin' : ['remko'], 'peter' : ['remko'] }
    self.jidToUser = {
        'remko@wonderland.lit' : 'remko',
        'peter@wonderland.lit' : 'peter',
        'kevin@wonderland.lit' : 'kevin',
      }
    self.userToJID = { 
        'remko' : 'remko@wonderland.lit',
        'peter' : 'peter@wonderland.lit',
        'kevin' : 'kevin@wonderland.lit' 
      }
    self.userPresenceMonitoring = {
        'kevin' : True,
        'remko' : False,
        'peter' : True,
      }

    self.connection = amqp.Connection(server, userid, password, use_threading=False)
    self.channel    = self.connection.channel()
    self.ticket     = self.channel.access_request('/data', active=True, write=True)

    # establish "user" as a Direct exchange
    self.channel.exchange_declare('user', type="topic", durable=False, auto_delete=False)

    #qname, qcount, ccount = self.channel.queue_declare('all', durable=False, exclusive=False, auto_delete=False)
    #self.channel.queue_bind('all', 'user', '#')
    #self.channel.basic_consume('all', callback=self._callback)

    # for debugging - run thru the defined users and create queues for each
    for key in ['peter', 'kevin', 'remko']:
      q = '%s.%d' % (key, time.time())
      print 'creating queue', q
      qname, qcount, ccount = self.channel.queue_declare(q, durable=False, exclusive=True, auto_delete=True)
      print qname, qcount, ccount
      self.channel.queue_bind(q, 'user', '%s' % key)
      self.channel.basic_consume(q, callback=self._callback)
      #for sub in self.subscribers[key]:
      #  print 'subscribing', key, 'to', sub
      #  qname, qcount, ccount = self.channel.queue_declare('%s.2' % sub, durable=False, exclusive=False, auto_delete=False)
      #  print qname, qcount, ccount
      #  self.channel.queue_bind('%s.2' % sub, 'user', '%s#' % sub)
      #  self.channel.basic_consume('%s.2' % sub, callback=self._callback)

    self.__thread = threading.Thread(name='rmqloop', target=self._processRMQ)
    self.__thread.start()

  def _post(self, data, user):
    print 'sending to RMQ', data
    msg = amqp.Message(data)
    msg.properties["delivery_mode"] = 1
    self.channel.basic_publish(msg, 'user', '%s' % user)

  def _processRMQ(self):
    while self.channel and self.channel.callbacks:
      print '\nprocessRMQ loop:top', self.channel.callbacks.keys()
      self.channel.wait()
      print '\nprocessRMQ loop:bottom', self.channel.callbacks.keys()

  def _callback(self, msg):
    print 'callback:', msg.delivery_info['exchange'], msg.delivery_info['routing_key'], msg.body
    data = msg.body.split()
    self._insertMessage(data[1], data[0])
    msg.channel.basic_ack(msg.delivery_tag)

  def getMessages(self, user) :
    messages = []
    if self.messages.has_key(user) :
      messages += self.messages[user]

    for contact in self.contacts.get(user, []) :
      if self.messages.has_key(contact) :
        messages += self.messages[contact]
    messages.sort(reverse=True, cmp=message_compare)
    return messages

  def getLastMessage(self, user) :
    messages = self.getMessages(user)
    if len(messages) > 0 :
      return messages[0]
    else :
      return Message(None, user, '')

  def _insertMessage(self, text, user):
    if len(text) > 0 and self.getLastMessage(user) != text :
      message = Message(datetime.datetime.today(), user, text)
      self.messages.setdefault(user,[]).append(message)
      self.notifyMessage(message)
      return True
    else:
      return False

  def addMessageFromUser(self, text, user):
    print 'addMessageFromUser:', text, user
    if text and user:
      self._post('%s %s' % (user, text), user)

    if text and user is None:
        print 'subscribing kevin to test'
        qname, qcount, ccount = self.channel.queue_declare('test', durable=False, exclusive=False, auto_delete=False)
        print qname, qcount, ccount
        self.channel.queue_bind('test', 'user', 'test')
        self.channel.basic_consume('test', callback=self._callback)
        self.subscribers['kevin'].append('test')
        print self.subscribers

  def getAllUsers(self) :
    return self.messages.keys()
  
  def getContacts(self, user) :
    return self.contacts.get(user, [])
  
  def getJIDForUser(self, user) :
    return self.userToJID[user]

  def getUserHasJID(self, user) :
    return self.userToJID.has_key(user)

  def getShouldMonitorPresenceFromUser(self, user):
    return self.userPresenceMonitoring[user]

  def setShouldMonitorPresenceFromUser(self, user, state):
    self.userPresenceMonitoring[user] = state

  def getSubscriberJIDs(self, user) :
    subscribers = []
    #for subscriber in self.subscribers.get(user, []) + [user] :
    for subscriber in self.subscribers.get(user, []) :
      if self.userToJID.has_key(subscriber) :
        subscribers.append(self.userToJID[subscriber])
    return subscribers
  
  def getUserFromJID(self, user) :
    return self.jidToUser.get(user.split('/',1)[0], None)

  def addContact(self, user, contact) :
    if not self.contacts.has_key(user) :
      self.contacts[user] = []
    self.contacts.setdefault(user, []).append(contact)

  def registerXMPPUser(self, user, password, fulljid) :
    barejid = fulljid.split('/', 1)[0]
    self.jidToUser[barejid] = user
    self.userToJID[user] = barejid
    return True

