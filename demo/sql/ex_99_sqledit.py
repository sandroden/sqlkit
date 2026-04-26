"""sqledit/the script


sqledit is the script that lets you browse which tables are present in the
database and open Masks/Tables.

It's normally called directly from the command line with the name 'sqledit'
"""

from sqlkit.misc.table_browser import TableBrowser
t = TableBrowser(db, title="Sqledit: the script")
