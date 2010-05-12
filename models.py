from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Unicode, UnicodeText, DateTime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    username = Column(Unicode, primary_key = True)
    password = Column(UnicodeText)
    created_at = Column(DateTime)

