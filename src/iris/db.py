# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Session = None
dict_cursor = None
engine = None


def init(config):
    global engine
    global dict_cursor
    global Session

    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])
    dict_cursor = engine.dialect.dbapi.cursors.DictCursor
    Session = sessionmaker(bind=engine)
