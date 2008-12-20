"""base/base import

these are the base import. All other examples skip the imports that are
granted by the way execfile is done in 'demo.py'.

The proxy is not needed, is just a way to pass several in a single
parameter metadata and session

Table
-----
base editing mode: table view
passing the tablename triggers the reflection of the table fom the database


"""

from sqlkit.widgets import SqlTable
from sqlkit.db import proxy
import model

db = proxy.DbProxy(bind="sqlite:///model/movies.sqlite")


t = SqlTable(table='movie',    dbproxy=db, order_by='title', )
t.reload()

