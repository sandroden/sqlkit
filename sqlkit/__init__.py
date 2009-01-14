from db.proxy import DbProxy
import exc
__version__ = '0.8.4'


import gettext
import sys
import os

cwd = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(cwd, 'locale')

import gettext

# t = gettext.translation('sqlkit', path)
# _ = t.lgettext

gettext.bindtextdomain('sqlkit', path)
gettext.textdomain('sqlkit')
_ = gettext.gettext
   
