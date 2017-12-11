# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .validators import IrisValidationException
from falcon import HTTPBadRequest, HTTPNotFound, HTTPForbidden, HTTPUnauthorized
import logging

logger = logging.getLogger(__name__)


Session = None
dict_cursor = None
ss_dict_cursor = None
engine = None


def init(config):
    global engine
    global dict_cursor
    global ss_dict_cursor
    global Session

    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])
    dict_cursor = engine.dialect.dbapi.cursors.DictCursor
    ss_dict_cursor = engine.dialect.dbapi.cursors.SSDictCursor
    Session = sessionmaker(bind=engine)


@contextmanager
def guarded_session():
    '''
    Context manager that will automatically close session on exceptions
    '''
    try:
        session = Session()
        yield session
    except IrisValidationException as e:
        session.close()
        raise HTTPBadRequest('Validation error', str(e))
    except (HTTPForbidden, HTTPUnauthorized, HTTPNotFound, HTTPBadRequest):
        session.close()
        raise
    except Exception:
        session.close()
        logger.exception('SERVER ERROR')
        raise
