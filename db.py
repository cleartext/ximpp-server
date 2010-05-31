import logging
from pdb import set_trace
from functools import wraps
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.interfaces import PoolListener

Session = sessionmaker()


class DebugListener(PoolListener):
    def __init__(self):
        self._log = logging.getLogger('pool-status')

    def connect(self, dbapi_con, con_record):
        self._log.debug('connect: ' + con_record._ConnectionRecord__pool.status())

    def checkin(self, dbapi_con, con_record):
        self._log.debug('checkin: ' + con_record._ConnectionRecord__pool.status())

    def checkout(self, dbapi_con, con_record, con_proxy):
        self._log.debug('checkout: ' + con_record._ConnectionRecord__pool.status())



def init(database_uri):
    """ This function should be called before Session use. """
    engine = create_engine(
        database_uri,
        pool_recycle = 3600,
        pool_size = 5,
        max_overflow = 0,
        echo = True,
        listeners = [DebugListener()],
    )
    Session.configure(bind = engine)



def db_session(func):
    """ Passes db session object to the function. """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'session' not in kwargs:
            session = Session()
            kwargs['session'] = session
            try:
                result = func(*args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
            finally:
                session.close()

    return wrapper

