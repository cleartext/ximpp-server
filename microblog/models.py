from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Unicode, UnicodeText, \
                       DateTime, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from pdb import set_trace

Base = declarative_base()

subscribers = Table('subscribers', Base.metadata,
    Column('user', Unicode, ForeignKey('users.username')),
    Column('subscriber', Unicode, ForeignKey('users.username'))
)

class VCard(Base):
    __tablename__ = 'vcard'

    username = Column(Unicode, primary_key = True)
    vcard = Column(UnicodeText)
    created_at = Column(DateTime)


class User(Base):
    __tablename__ = 'users'

    username = Column(Unicode, ForeignKey('vcard.username'), primary_key = True)
    password = Column(UnicodeText)
    created_at = Column(DateTime)
    jid = Column(Unicode, unique = True)
    presence = Column(Boolean)

    subscribers = relationship(
        'User',
        secondary = subscribers,
        backref = 'contacts',
        primaryjoin = 'User.username == subscribers.c.user',
        secondaryjoin = 'subscribers.c.subscriber == User.username',
    )

    _vcard = relationship('VCard', backref = 'user')

    @property
    def vcard(self):
        from microblog.et_accessor import Accessor
        from microblog.bot import ET
        if self._vcard:
            return Accessor(ET.fromstring(self._vcard.vcard))
        return None



class SearchTerm(Base):
    __tablename__ = 'search_terms'
    term = Column(Unicode, primary_key = True)
    username = Column(Unicode, primary_key = True)

    def __init__(self, term, username):
        self.term = term
        self.username = username


class Message(object):
    def __init__(self, date, user, text):
        self.date = date
        self.user = user
        self.text = text

