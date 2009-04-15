import gettext
import sys
import os
import gettext

__version__ = '0.8.6-rc3'


cwd = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(cwd, 'locale')


# t = gettext.translation('sqlkit', path)
# _ = t.lgettext

gettext.bindtextdomain('sqlkit', path)
gettext.textdomain('sqlkit')
_ = gettext.gettext
   
from db.proxy import DbProxy
import exc
