import psycopg2
o = psycopg2.connect("dbname=test")
c = o.cursor()
c.execute("SELECT 1.23 AS foo")
print c.fetchone()
c.execute("SELECT 1.23::float AS foo")
print c.fetchone()
import gtk
c.execute("SELECT 1.23 AS foo")
print c.fetchone()
c.execute("SELECT 1.23::float AS foo")
print c.fetchone()
