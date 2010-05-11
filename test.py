#!/usr/bin/env python

import os, sys
import time
import datetime
import threading

import amqplib.client_0_8 as amqp


class RMQBackend():
  def __init__(self, server, userid, password):
    self.server      = server
    self.password    = password
    self.connection  = None
    self.channel     = None

    self.connection = amqp.Connection(server, userid, password, use_threading=False)
    self.channel    = self.connection.channel()
    self.ticket     = self.channel.access_request('/data', active=True, write=True)

    # establish "user" as a Direct exchange
    self.channel.exchange_declare('user', type="topic", durable=False, auto_delete=False)

    self.__thread = threading.Thread(name='rmqloop', target=self._processRMQ)

  def start(self):
    self.__thread.start()

  def listen(self, user):
    print 'listen', user
    q = '%s.%d' % (user, time.time())
    qname, qcount, ccount = self.channel.queue_declare(q, durable=False, exclusive=True, auto_delete=True)
    print qname, qcount, ccount
    self.channel.queue_bind(q, 'user', '%s' % user)
    self.channel.basic_consume(q, callback=self._callback)

  def _processRMQ(self):
    while self.channel and self.channel.callbacks:
      print 'processRMQ loop:top', self.channel.callbacks.keys()
      self.channel.wait()
      print 'processRMQ loop:bottom', self.channel.callbacks.keys()

  def _callback(self, msg):
    print 'callback:', msg.delivery_info['exchange'], msg.delivery_info['routing_key'], msg.body
    data = msg.body.split()
    self._insertMessage(data[1], data[0])
    print msg.channel.basic_ack(msg.delivery_tag) 
    print '======'

  def _post(self, data, user):
    print 'sending to RMQ', data
    msg = amqp.Message(data)
    msg.properties["delivery_mode"] = 1
    self.channel.basic_publish(msg, 'user', user)
    self.channel.basic_publish(msg, 'public', 'post')

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
      print 'insert', user, text

  def addMessageFromUser(self, text, user):
    print 'addMessageFromUser:', text, user
    if text and user:
      self._post('%s %s' % (user, text), user)

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



if __name__ == '__main__':
    backend = RMQBackend('palala.org', 'guest', 'JfMxYJnb9zc4vHmBBXJp')
    backend.listen(sys.argv[1])
    backend.start()

    print '----'

    while True:
        time.sleep(1)
