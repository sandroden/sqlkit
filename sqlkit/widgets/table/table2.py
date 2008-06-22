from table import SqlTable
import sys
sys.path.append ('../../../')
#from sqlalchemy import *
#import layout
from datetime import datetime
import sqlalchemy.types as sqltypes
from sqlkit.widgets.common import sqlwidget, CommitError, ValidationError
import sqlalchemy
import dbg
import decimal
from  layout import widgets
import re
import gobject
import gtk
from  cell_renderers import CellRendererDate, CellRendererDatetime
#sys.path.append('../gdl')

class SqlTable2(SqlTable):
    """A class that implements a different approach to record management and
    uses a listore with one single object (the instance) and a function to
    set the value in the cell via
                   column.set_cell_data_func
    """


    __metaclass__ = dbg.LogTheMethods

    
