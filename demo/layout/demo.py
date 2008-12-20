#!/usr/bin/env python
# -*- coding: utf-8 -*-   -*- mode: python -*-



import gtk
import sys
import os

pdir = os.path.dirname(os.getcwd())
ppdir = os.path.dirname(pdir)
sys.path.append(pdir)    
sys.path.append(ppdir)    

from demo_tour import Demo

d = Demo()

gtk.main()

