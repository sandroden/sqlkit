
import traceback, sys, os
import psycopg2
sys.path.append ('..')
from config import spawnDSN

def runBatch (path):
  path = os.path.abspath ("batches/" + path)
  f = open (path, 'rb')
  query = str (f.read ())
  try:
    connection = psycopg2.connect (dsn = spawnDSN ())
    cursor = connection.cursor ()
    cursor.execute (query)
    connection.commit ()
  except:
    traceback.print_exc (file = sys.stdout)
  
