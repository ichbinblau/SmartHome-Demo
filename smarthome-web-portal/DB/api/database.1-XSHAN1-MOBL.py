# -*- coding: utf-8 -*-
"""
Provider interfaces to manipulate database.
"""
import functools
import logging
import sqlalchemy
from threading import local
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.pool import QueuePool
from sqlalchemy.pool import SingletonThreadPool
from sqlalchemy.pool import StaticPool

from DB import models, exception
from utils.config import config

logger = logging.getLogger(__name__)

ENGINE = None
SESSION = sessionmaker(autocommit=False, autoflush=False)
SCOPED_SESSION = None
SESSION_HOLDER = local()

POOL_MAPPING = {
    'instant': NullPool,
    'static': StaticPool,
    'queued': QueuePool,
    'thread_single': SingletonThreadPool
}

TABLES = ['user',
          'fan',
          'motion',
          'button',
          'gas',
          'solar',
          'illuminance',
          'temperature',
          'buzzer',
          'rgbled',
          'led',
          'eventlog',
          'energy',
          'environment',
          'power',
          'gateway',
          'resource',
          'sensor_type',
          'sms_history',
          ]


def get_session():
    if in_session():
        return SESSION
    else:
        init()


def init(database_url=None):
    """Initialize database.

    :param database_url: string, database url.
    """
    global ENGINE
    global SCOPED_SESSION
    if not database_url:
        database_url = config.get_connection_url()
    logging.info('init database %s', database_url)
    #print database_url
    #root_logger = logging.getLogger()
    #fine_debug = root_logger.isEnabledFor(logsetting.LOGLEVEL_MAPPING['fine'])
    #if fine_debug:
    #    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    #finest_debug = root_logger.isEnabledFor(
    #    logsetting.LOGLEVEL_MAPPING['finest']
    #)
    #if finest_debug:
    #    logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
    #    logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
    #    logging.getLogger('sqlalchemy.orm').setLevel(logging.INFO)
    poolclass = POOL_MAPPING[config.get_database_pool_type()]
    ENGINE = create_engine(
        database_url, convert_unicode=True,
        poolclass=poolclass, echo=False,
    )
    SESSION.configure(bind=ENGINE)
    SCOPED_SESSION = scoped_session(SESSION)
    models.Base.query = SCOPED_SESSION.query_property()


def in_session():
    #check if in database session scope.#
    if hasattr(SESSION_HOLDER, 'session'):
        return True
    else:
        return False


@contextmanager
def session():
    """database session scope.

       .. note::
       To operate database, it should be called in database session.
    """

    if not ENGINE:
        init()

    if hasattr(SESSION_HOLDER, 'session'):
        logging.error('we are already in session')
        raise exception.DatabaseException('session already exist')
    else:
        new_session = SCOPED_SESSION()
        setattr(SESSION_HOLDER, 'session', new_session)

    try:

        yield new_session
        new_session.commit()

    except Exception as error:
        new_session.rollback()
        logging.error('failed to commit session')
        print error
        logging.exception(error)
        if isinstance(error, IntegrityError):
            raise exception.NotAcceptable(
                'operation error in database'
            )
        elif isinstance(error, OperationalError):
            raise exception.DatabaseException(
                'operation error in database'
            )
        elif isinstance(error, exception.DatabaseException):
            raise error
        else:
            raise exception.DatabaseException(str(error))
            # pass
    finally:
        new_session.close()
        SCOPED_SESSION.remove()
        delattr(SESSION_HOLDER, 'session')


def current_session():
    """Get the current session scope when it is called.

       :return: database session.
    """
    try:
        return SESSION_HOLDER.session
    except Exception as error:
        logging.error('It is not in the session scope')
        logging.exception(error)
        if isinstance(error, exception.DatabaseException):
            raise error
        else:
            raise exception.DatabaseException(str(error))


def run_in_session():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with session() as my_session:
                return func(my_session, *args, **kwargs)
        return wrapper
    return decorator


@run_in_session()
def create_db(session):
    #Create database.#
    models.Base.metadata.create_all(bind=ENGINE)


@run_in_session()
def drop_db(session):
    #Drop database.#
    models.Base.metadata.drop_all(bind=ENGINE)


def check_tables():
    #check tables exist or not
    logging.info('check table info')
    if not ENGINE:
        init()
    md = sqlalchemy.MetaData(ENGINE)
    md.reflect()
    for table in TABLES:
        if table not in md.tables.keys():
            logging.info('table %s does not exist' % table)
            return False
    return True


if __name__ == '__main__':
    init()
    models.Base.metadata.tables["fan"].create(bind=ENGINE)










