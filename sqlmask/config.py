
import os
from ConfigParser import ConfigParser
from sqlalchemy import *


def spawnEngine ():
  c = ConfigParser ()
  c.read (os.path.dirname (__file__) + '/config.ini')
  return create_engine (c.get ('database', 'dbapi'),
      {'database' : c.get ('database', 'dbname'),
      'host' : c.get ('database', 'host'),
      'user' : c.get ('database', 'user'),
      'port' : c.get ('database', 'port'),
      'password' : c.get ('database', 'password')})


def spawnDSN ():
  c = ConfigParser ()
  c.read (os.path.dirname (__file__) + '/config.ini')
  return "host=%s dbname=%s user=%s" % (
      c.get ('database', 'host'),
      c.get ('database', 'dbname'),
      c.get ('database', 'user'))
