import os
import sys
import gettext
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Pango', '1.0')

from sqlkit.misc import utils

# single-sourced from the installed package metadata (pyproject version);
# the literal fallback only matters for unusual setups (e.g. pyinstaller)
try:
    from importlib.metadata import version as _dist_version
    __version__ = _dist_version('sqlkit')
except Exception:
    __version__ = '1.1.0'


cwd = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(cwd, 'locale')
if not os.path.exists(path):
    # this is true when we are in the pyinstaller executable
    path = os.path.join(os.path.dirname(sys.executable), 'sqlkit', 'locale')

# t = gettext.translation('sqlkit', path)
# _ = t.lgettext

gettext.bindtextdomain('sqlkit', path)
gettext.textdomain('sqlkit')
_ = gettext.gettext

from .db.proxy import DbProxy
from . import exc


utils.check_sqlalchemy_version('0.6.1')
