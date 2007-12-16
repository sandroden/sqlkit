import sys, re
import datetime
import dbg
import decimal
import sqlkit as sk

from sqlalchemy import *


class TableLayoutGenerator (object):

    map_types = {
        datetime.datetime     : 'd',
        datetime.date         : 'd',
        datetime.time         : 'd',
        bool                  : 'c',
        int                   : 'ae',
        float                 : 'ae',
        str                   : 'ae',
        decimal.Decimal       : 'ae',
        }
    
    def __init__ (self, master, naked=False, lay=None):
        """fields: an InspectMapper object
        """
        self.master = master
        self.fields = master.fields
        #print self.fields.keys()
        if lay:
            self.layout = self._parse_and_complete(lay)
            #print self.layout
        else:
            if isinstance(master, sk.SqlMask):
                self.layout = self.create ()
            else:
                self.layout = self.create_for_table()

        if not naked:
            self._add_default_buttons()

    def create (self):
        entries = []
        for field_name in self.master.field_list:
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
        field_name must be preceded and followed by a space or newline
        """
        p = re.compile(r"""^(\s*#.+)""", re.MULTILINE)
        lay = p.sub('', lay)   # strip any comment

#        (?<![\S%{=]\b)   # \b bound of a string <![{] is not preceded by {
#                     # this is to excude  {N   (container + flags)

        p2 = re.compile(r"""
        (?<!\S)                    # next row must not match if preceded by any str
                                   # %string is a qualifier for notebooks
                                   # {N is for noteooks and so on
        (?P<field>[a-z_A-Z\.]+)   # the field + a possible table (table.field)
        (?![-=])                  # the row above is only mathced if not followed
                                  # by - o = (b=gtk-save-as *must not* match)
        (?P<spec>:[-<>.\d]*)?
        (?P<end>\b)
        """, re.VERBOSE | re.MULTILINE)

        return p2.sub(self._sub, lay)
    
    def _sub(self, m):
        ### not using add_spec just becouse of the way args are passed
        field_name = m.group('field')
        #print 'field_name',field_name
        if field_name in self.fields:
            t = self.fields[field_name]['type']
        else:
            ## any field that is not explicitly here is mapped into 'str'
            #dbg.write('field_name', field_name)
            #print "ELSE", field_name
            field_name, t, col_spec = self.register(field_name)
            if t is None:  # this is not a db field
                return field_name

            #dbg.write("t=", t)
        fmod = self.map_types[t]

        spec = m.group('spec') or ''
        try:
            col_spec = self.fields[field_name]['col_spec']
        except:
            col_spec = col_spec
            
        if not spec:
            spec = self.create_spec(field_name, col_spec)
            #print field_name, spec
        return " L=%s %s=%s%s" % (field_name, fmod, field_name,
                                   spec)
    
    def create_spec(self, field_name, col_spec):
        """create a spec string that decides how long en entry must be
           reflects fom db
           """
        #print col_spec
        if col_spec == 'INTEGER':
            return ":8"
        elif col_spec.startswith('FLOAT'):
            return ":8"
        else:
            m = re.search('VARCHAR.(\d+).', col_spec)
            if m:
                length = int(m.group(1))
                ## really long field should not at up all the space
                ## (but you can obverride this by hand!...
                if length > 50:
                    length = 50
                ## now alignment
                spec = ":%s" % length
                if length> 20:
                    spec += "-"
#                 else:
#                     spec += "<"
                return spec
        return ''
                    
        
    def register(self, field_name):
        """regiter field_name as a field_name of a table to be found and reflected
        field_name must be of the form table.field_name
        """

        p = re.compile("""
           ([-_A-Za-z0-9]+)   # table name
           \.                 # separator
           (\S+)             # field_name
        """, re.VERBOSE)
        m = p.search(field_name)
        if not m:
            #dbg.write("%s not of the form table.field" % field_name )
            return (field_name, None, None)
        table_name = m.group(1)
        #dbg.write('table_name:', table_name)
        tbl_field_name = m.group(2)

        table = Table(table_name, self.fields.mapper.local_table.engine,
                      autoload=True)
        t1 = type(table.c[tbl_field_name].type)
        col_spec = table.c[tbl_field_name].type.get_col_spec()
        t = self.fields.pytype[t1]
        return (tbl_field_name, t, col_spec)

    def _add_default_buttons (self):
        # a 'naked' mask is a mask w/o buttons. Maybe buttons are define by the
        # programmer inside the layout, maybe are not desired

        if isinstance(self.master, sk.SqlMask):
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
        if self.master.icons:
            lay = "%s\n{A.icons {H %s}}" % (lay, self.master.icons)
            
        return lay
