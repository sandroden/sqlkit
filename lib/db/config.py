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
    
def new_engine(file='config.ini', echo=False, globalconn=False):
    import sqlalchemy
    if globalconn:
        from sqlalchemy import global_connect as connect
    else:
        from sqlalchemy import create_engine as connect
    
    c = ConfigParser ()
    file = searchFile(file)
    if not file or not os.path.exists(file):
        raise MissingConfigFileError("looking for: %s" % file)
    
    c.read (file)
    db = {}
    
    for tup in c.items('database'):
        key, val = tup
        db[key] = val
    print db
    try:
        eng_str = db['url']
    except:
        eng_str = "%(dbapi)s://%(user)s:%(password)s@%(host)s:%(port)s/%(dbname)s" % db
    engine = connect(eng_str, echo=echo)

    if engine:
        return engine
    else:
        return sqlalchemy.schema.default_metadata.engine


#new_engine = spawnEngine

def spawnDSN (file='config.ini'):
    c = ConfigParser ()
    db = None
    file = searchFile(file)
    if not file or not os.path.exists(file):
        raise MissingConfigFileError("looking for: %s" % file)
    c.read (file)
    db = "host=%s dbname=%s user=%s password=%s port=%s" % (
        c.get ('database', 'host'),
        c.get ('database', 'dbname'),
        c.get ('database', 'user'),
        c.get ('database', 'password'),
        c.get ('database', 'port'))
    return db 

