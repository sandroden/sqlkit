#!/usr/bin/env python
# -*- coding: utf-8 -*-   -*- mode: python -*-


import sys
import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

PY2 = sys.version_info[0] == 2
if PY2:
    # This hack fixes some UnicodDecode Errors caused pygi not making
    # magic hidden automatic unicode conversion pygtk did
    reload(sys)
    sys.setdefaultencoding("utf-8")

pdir = os.path.dirname(os.getcwd())
ppdir = os.path.dirname(pdir)
sys.path.insert(0, pdir)
sys.path.insert(0, ppdir)

from demo_tour import Demo

class LayoutDemo(Demo):
    example_pattern = '\d\d.*.py'

d = LayoutDemo()

Gtk.main()
