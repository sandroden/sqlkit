import os
from ConfigParser import ConfigParser
from sqlalchemy import *

def searchFile():
	""" firt search in cwd, then it's parent or config.py directory """
	places = [os.getcwd(),
			os.path.dirname(os.getcwd() ),
			os.path.dirname(__file__)]
	for d in places:
		filename = os.path.join(d, 'config.ini')
		if os.path.exists(filename ):
			return filename
						

def spawnEngine (conf_file=None):
	c = ConfigParser ()
	if not conf_file:
		conf_file = searchFile()
		c.read (conf_file)
	return create_engine (c.get ('database', 'dbapi'),
						{'database' : c.get ('database', 'dbname'),
						'host' : c.get ('database', 'host'),
						'user' : c.get ('database', 'user'),
						'port' : c.get ('database', 'port'),
						'password' : c.get ('database', 'password')})


def spawnDSN (conf_file=None):
	c = ConfigParser ()
	db = None
	if not conf_file:
		conf_file = searchFile()
		print conf_file
		c.read (conf_file)
		db = "host=%s dbname=%s user=%s password=%s port=%s" % (
		c.get ('database', 'host'),
		c.get ('database', 'dbname'),
		c.get ('database', 'user'),
		c.get ('database', 'password'),
		c.get ('database', 'port'))
	return db 
