import os
import sys

Dir = os.path.dirname(__file__)

dirs = [
    'lib/db',
    'lib/validation',
#    'lib/config',
    'lib/widgets',
    'lib/widgets/mask',
    'lib/widgets/table',
    'lib/widgets/common',
    ]


__path__ = [os.path.join(Dir, *d.split('/')) for d in dirs]
#print __path__


#from mask import *
import mask
import common
#from common import sqlfilter
#import widgets
#import widgets.table as table
import table
import inspect
import validator
import config
import parseopts

from mask import SqlMask
from table import SqlTreeView, SqlLayoutTreeView
