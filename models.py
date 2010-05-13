from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Unicode, UnicodeText, DateTime, Table, ForeignKey
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

    subscribers = relationship(
        'User',
        secondary = subscribers,
        backref = 'contacts',
        primaryjoin = 'User.username == subscribers.c.user',
        secondaryjoin = 'subscribers.c.subscriber == User.username',
    )
