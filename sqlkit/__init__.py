import os
import sys

# Dir = os.path.dirname(__file__)
# dirs = [
#     './db',
#     './validation',
# #    .b/config',
#     './widgets',
#     './widgets/mask',
#     './widgets/table',
#     './widgets/common',
#     ]


# __path__ = [os.path.join(Dir, *d.split('/')) for d in dirs]
# #print __path__

#from mask import *

from widgets import common
from widgets.common import sqlfilter, completion
from widgets import mask
from widgets.common import sqlwidget

from validation import validator
#from common import sqlfilter
#import widgets
#import widgets.table as table
from widgets import table
from db import minspect 
#import validator
from db import config
#import parseopts

from widgets.mask import SqlMask
from widgets.mask import Combo
from widgets.common.sqlwidget import SqlWidget
from widgets.table import  SqlTable, SqlTable2
#from SqlTreeView import  SqlTable
