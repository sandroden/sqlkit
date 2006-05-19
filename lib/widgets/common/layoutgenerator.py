import sys, re
import datetime
import dbg

from sqlalchemy import *


class TableLayoutGenerator (object):

    map_types = {
        datetime.datetime     : 'd',
        datetime.date         : 'd',
        datetime.time         : 'd',
        bool                  : 'c',
        int                   : 'e',
        float                 : 'e',
        str                   : 'e',
        }
    
    def __init__ (self, fields, naked=False, lay=None, target='mask'):
        """fields: an InspectMapper object
        target: mask or table
        """
        self.target = target
        self.fields = fields
        if lay:
            self.layout = self._parse_and_complete(lay)
        else:
            if target == 'mask':
                self.layout = self.create ()
            else:
                self.layout = self.create_for_table()

        if not naked:
            self._add_default_buttons()

    def create (self):
        entries = []
        for field_name in self.fields.keys():
            entries.append( self.add_spec(field_name=field_name ))
        return ''.join (entries)

    
    def add_spec(self, field_name=None):
        ftype = getattr(self.fields, field_name)['type']
        spec = self.map_types[ftype]
        dim=''

        if self.fields[field_name]['col_spec'] == 'TEXT':
            spec = 'TXS'
            dim = ":250.100"
        return "L=%s %s=%s%s\n" % (field_name, spec, field_name, dim)


    def _parse_and_complete(self, lay):
        """parse the layout and substitute all field_name with:

            L=field_name mod=field_name

        where mod is the appropriate modifier ([edc])
        field_name must be preceded and folloed by a space or newline
        """

        return re.sub(r""" ([a-z_A-Z]+)(:[.\d]*)?( |\n)""", self._sub, lay)

    def _sub(self, m):
        ### not using add_spec just becouse of the way args are passed
        field_name = m.group(1)
        fmod = self.map_types[self.fields[field_name]['type']]

        return " L=%s %s=%s%s%s" % (field_name, fmod, field_name,
                                   m.group(2) or '', m.group(3))
    


    def _add_default_buttons (self):
        # a 'naked' mask is a mask w/o buttons. Maybe buttons are define by the
        # programmer inside the layout, maybe are not desired

        if self.target == 'mask':
            nav_buttons="tb=gtk-go-back tb=gtk-go-forward"
        else:
            nav_buttons=""
            
        self.layout = """
        {B m=file m=modifica m=opzioni m=aiuto}
        {O.tool tb=gtk-save tb=gtk-delete tb=gtk-new tb=gtk-refresh tb=gtk-quit
        %s}
        {A { %s}}
        sb=StBar
        """ % (nav_buttons, self.layout)
    
    def create_for_table(self):
        lay = """
          TVS=tree
        """
        return lay
