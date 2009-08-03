import gettext
import sys
import os
import gettext
from .misc import utils

__version__ = '0.8.6-rc5'


cwd = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(cwd, 'locale')


# t = gettext.translation('sqlkit', path)
# _ = t.lgettext

gettext.bindtextdomain('sqlkit', path)
gettext.textdomain('sqlkit')
_ = gettext.gettext
   
from db.proxy import DbProxy
import exc


utils.check_sqlalchemy_version('0.5.3')
