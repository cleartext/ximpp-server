from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Unicode, UnicodeText, \
                       DateTime, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship

Base = declarative_base()

subscribers = Table('subscribers', Base.metadata,
    Column('user', Unicode, ForeignKey('users.username')),
    Column('subscriber', Unicode, ForeignKey('users.username'))
)

class User(Base):
    __tablename__ = 'users'

    username = Column(Unicode, primary_key = True)
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

