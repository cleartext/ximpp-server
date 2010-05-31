from functools import wraps
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Session = sessionmaker()

def init(database_uri):
    """ This function should be called before Session use. """
    engine = create_engine(database_uri, pool_recycle = 3600)
    Session.configure(bind = engine)

def db_session(func):
    """ Passes db session object to the function. """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'session' not in kwargs:
            kwargs['session'] = Session()
        return func(*args, **kwargs)
    return wrapper

