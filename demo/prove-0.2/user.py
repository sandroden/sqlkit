#!/usr/bin/env python

import sys, re, datetime

sys.path.append ('../../../')
import sqlkit as sk
import sqlalchemy as sa

engine = sk.config.new_engine(echo=False, globalconn=True)
meta = sa.default_metadata
session = sa.create_session()

user_table = sa.Table ('euro_user', engine, autoload=True)

class User(object): pass
m = sa.mapper(User, user_table, )
ret = session.query(m).select()
M = sk.minspect.InspectMapper(m)
d = sk.sqldata.SqlData(ret, M, session)
d.printall()

R=ret[0]
R.user_name = 'Pippo3'
engine.echo=True
d.set({'user_name':'XXX'},index=1)
session.flush()

sys.exit()


