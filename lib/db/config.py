import os
import dbg
from ConfigParser import ConfigParser

class MissingConfigFileError(Exception): pass

def searchFile(file):
    """ first search in cwd, then it's parent or config.py directory """
    places = [os.getcwd(),
	      os.path.dirname(os.getcwd() ),
	      os.path.dirname(__file__)]
    for d in places:
        filename = os.path.join(d, file)
        if os.path.exists(filename ):
            #dbg.write("file:", file)
            return filename
    
def spawnEngine(file='config.ini', echo=False, globalconn=False):
    import sqlalchemy
    if globalconn:
        #dbg.write("GLOBAL connect")
        from sqlalchemy import global_connect as connect
    else:
        from sqlalchemy import create_engine as connect
    
    c = ConfigParser ()
    file = searchFile(file)
    if not os.path.exists(file):
        raise MissingConfigFileError("looking for: %s" % file)
    
    c.read (file)
    engine = connect (c.get ('database', 'dbapi'),
                          {'database' : c.get ('database', 'dbname'),
                           'host' : c.get ('database', 'host'),
                           'user' : c.get ('database', 'user'),
                           'port' : c.get ('database', 'port'),
                           'password' : c.get ('database', 'password')},
                          echo=echo)
    if engine:
        return engine
    else:
        return sqlalchemy.schema.default_engine.get_engine()


def spawnDSN (file='config.ini'):
    c = ConfigParser ()
    db = None
    if not file:
        file = searchFile(file)
        c.read (file)
        db = "host=%s dbname=%s user=%s password=%s port=%s" % (
            c.get ('database', 'host'),
            c.get ('database', 'dbname'),
            c.get ('database', 'user'),
            c.get ('database', 'password'),
            c.get ('database', 'port'))
    return db 

