from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Session = sessionmaker()

def init(database_uri):
    """ This function should be called before Session use. """
    engine = create_engine(database_uri)
    Session.configure(bind = engine)
