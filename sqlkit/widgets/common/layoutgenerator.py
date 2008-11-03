"""
================
Layoutgenerator
================

LayoutGenerator
================

build up the layout definition suitable for layout.Layout

Building layout from scratch
----------------------------

In case no layout is passed, a simple layout is built consisting of all
fields vertically packed based on fields in field_list


Passing a  layout
-------------------

In case a layout is passed as argument, the content is parsed to add the
labels and to set the type of widget used to represent the data (using
the mapping in map_types) unless a type is passed in the layout

attributes
----------

``fields_in_layout`` is a dict that maps field_names to widget specification
ie: the key to  be used in widgets dictionary

  * {'first_name': 'e=first_name', 'date': 'd=date', 'year': 'e=year'}

*without any specification*


.. Reference to other tables
.. ---------------------------
.. 
.. A name of a field can also be of the form: table.field_name, in which case
.. the table is reflected to get the type of the column, to adjust for the
.. proper widget representation

"""
import sys, re
import datetime
from sqlkit import debug as dbg
import decimal
import sqlkit as sk
from sqlkit.layout.widgets import register, register_alias, Alignment
from sqlalchemy import *

for mod in ('m2m', 'm2o', 'o2m', 'o2o'):
    register_alias(Alignment, mod)

class LayoutGenerator (object):
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
        self.loaders = {}
        self.master = master
        self.fields_in_layout = {}  # {'first_name': 'e=first_name', 'date': 'd=date'}
        self.fields = master.fields
        #self.used_field_dict = {}
        if isinstance(master, sk.SqlMask):
            if not lay:
                lay = "\n".join(self.master.field_list)
            self._look_for_loaders(lay)
            self.layout = self._parse_and_complete(lay)

        else:
            self.layout = self.create_for_table()

        if not naked:
            self._add_default_buttons()

        
        #print self.layout
        #dbg.write(self.layout)

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
        (?<!\S)                # next row must not match if preceded by any str
                               # %string is a qualifier for notebooks
                               # {N is for noteooks and so on
        (?P<field>[a-z_0-9A-Z\.]+)  # the field + a possible table (table.field)
        (?![-=])               # the row above is only matched if not followed
                               # by - o = (b=gtk-save-as *must not* match)
        (?P<spec>:[-<>.,a-zA-Z\d]*)?
        (?P<end>\b)
        """, re.VERBOSE | re.MULTILINE)

        return p2.sub(self._sub, lay)
    
    def _sub(self, m):
        """called from inside regexp
        """
        field_name = m.group('field')
        
#         ## this is for reference of fields defined in other tables: tbl.field
#         if field_name not in self.fields:
#             ## any field that is not explicitly here is mapped into 'str'
#             field_name, t, col_spec = self.register(field_name)
#             if t is None:  # this is not a db field
#                 return field_name

        widget = self.get_widget(field_name)
        spec = m.group('spec') or ''
        
        if self.master.is_loader(field_name):
            self.loaders[field_name] = spec

        if not spec:
            spec = self.create_spec(field_name)

        self.fields_in_layout[field_name] = "%s=%s" % (self.get_edit_string(widget), field_name)
                             
        return "L=%s %s=%s%s" % (field_name, widget, field_name, spec)

    def get_edit_string(self, mod):
        """
        return the real modifier that handle editing
        """
        if mod in ('ae'):
            return 'e'
        else:
            return mod
        
        
    def get_widget(self, field_name):
        """choose appropriate widget to represent this field
        """

        #self.used_field_dict[field_name] = 

        if self.master.is_fkey(field_name):
            ## ForeignKey for foreign key
            return "fk"

        if self.master.is_loader(field_name):
            return "m2m"
        
        ftype = self.master.get_field_type(field_name)
        widget = self.map_types[ftype]
        
        if self.fields[field_name]['col_spec'] == 'TEXT':
            widget = 'TXS'
        return widget

    def create_spec(self, field_name):
        """create a spec string that decides how long en entry must be
           reflects fom db
           """
        length = self.fields[field_name]['length']
        col_spec = self.fields[field_name]['col_spec'] or ''

            
        if self.master.is_fkey(field_name) or self.master.is_loader(field_name):
            ### FIXME: should I set the length of the foreign key?
            return ''
            
        pytype = self.fields[field_name]['type']
        if col_spec == 'INTEGER' or pytype == int:
            return ":8"
        elif col_spec.startswith('FLOAT') or pytype == float:
            return ":8"
        elif col_spec == 'TEXT':
            dim = ":250.100"
        
        else:
            if not length:
                m = re.search('VARCHAR.(\d+).', col_spec)
                if m:
                    length = int(m.group(1))
            if length:
                ## really long field should not eat up all the space
                ## (but you can override this by hand!...
                if length > 50:
                    length = 50
                ## now alignment: this will ensure it will grow
                ##  if more space is given to the window via rezising
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
        {O.tool tb=gtk-save tb=gtk-save-as tb=gtk-delete tb=gtk-new tb=gtk-refresh tb=gtk-quit
        %s}
        {A.external { %s}}
        sb=StBar
        """ % (nav_buttons, self.layout)
    
    def create_for_table(self):
        lay = """
          TVS=tree
        """
        if self.master.icons:
            lay = "%s\n{A.icons {H %s}}" % (lay, self.master.icons)
            
        return lay

    def _look_for_loaders(self, lay):
        """
        Look for names that represent loaders, if any parse it for:

          * rows          (eg: m2m=actors:5)
          * field_list    (eg: m2m=actors:5:first_name,last_name)

        set it in self.loaders['movies'] = {'rows': 5, 'field_list': 'first_name,last_name'}
        """

        pat = re.compile("""
          ((?P<mod>m2m|m2o|o2m|o2o)=)?        # the modifier, but not the = sign
          (?P<loader>[a-zA-Z0-9_\.]+)         # the possible loader:
                                              # genre  genre.movies
          (:(?P<spec>\d*))?                   # number of rows for the table
          (:(?P<field_list>[\w,]+))?             # number of rows for the table
          $
        """, re.VERBOSE | re.MULTILINE)

        for token in lay.split():
            m = pat.match(token)
            if m:
                loader     = m.group('loader')  # to be verified
                mod        = m.group('mod')
                spec       = m.group('spec')
                field_list = m.group('field_list')

                if not self.master.is_loader(loader):
                    continue
                self.loaders[loader] = {}
                if spec:
                    self.loaders[loader]['rows'] = int(spec)
                if field_list:
                    self.loaders[loader]['field_list'] = field_list
                self.fields_in_layout[loader] = "%s=%s" % (mod, loader)

                    
