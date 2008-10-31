# $Name:  $ $Revision:  $ $Date: 2005/11/25 12:26:17 $

# Copyright (C) 2005 Sandro Dentella. All rights reserved.
# e-mail: sandro@e-den.it
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import re
#import dateedit   #delayed until needed
#import datetime
import os
import gtk, gobject
#from sqlkit.debug import debug as  dbg

info = {}
class LWidget(object):
    #__metaclass__ = LogTheMethods
    #logMatch = "position*"
    
    gtkClass = None
    transpose = {'w' : 'width_request',
                 'h' : 'height_request'
                 }
    class_properties = {'visible' : True}
    class_pack_properties  = {'y-options' : '0'}

    def __init__(self, el_def, pos, container, elements):
        ## update info for this class
        # print "Lwidget: %s %s" % (el_def,  self.gtkClass)
#         if self.gtkClass == 'GtkAlignment':
#             dbg.show_caller(sfilter='elements')
	
        self.el_def = el_def
        self.lw = {}
        self.container_flag = container
        self.properties = {}
        self.pack_properties = {}
        # By default, widgets do not expand vertically. Those who do can be
        # recognized (and set) by this attribute being True
        self.v_expand = False
        # used to specify order in properties
        self.ordered_properties = []
        if self.gtkClass:
            self.properties.update(LWidget.class_properties)
            self.pack_properties.update(LWidget.class_pack_properties)
            
        self.properties.update(self.class_properties)

        self._parse_cell_def(el_def)
        self.lw.update( {   ## lw : layout widget
           'container' : container,
           'el_def'    : el_def,
           'gtkClass'  : self.gtkClass,
           'children_list' : [],
        } )
        self.position(pos)
        self.pos = pos
        self.elements = elements
        self._labels_and_tips_from_info()
        #dbg.write('class_specific', type(self))
        self._class_specific()
#         if re.match('GtkEventBox', self.gtkClass):
#             dbg.write('ok')            
        self._set_dimentions()
        #dbg.debug("elements[%s] = %s (%s)" % (self.lw['el_key'],
        #                                     self,elements.keys()) )
        elements[self.lw['el_key']] = self

    def position(self, (row, col)):
        ## ask the class of the container which are the pack_properties
        ## apart from Table. Table has position changing, the others pack
        ## widgets as they arrive. I tried with classmethod for Table w/ no luck
        if self.container_flag in ('T'):                  
            self.pack_properties.update( {
                'left_attach'       : col,
                'top_attach'        : row,
                'right_attach'      : col+1,
                'bottom_attach'     : row+1,
                })
        else:
            self.pack_properties.update(
                _W[self.container_flag].class_pack_properties)

    def _debug_pos(self):
        p = self.pack_properties
        if self.container_flag == 'T':
            return "pos: %s : %s" % ((p['top_attach'],p['left_attach']),
                                     (p['bottom_attach'],p['right_attach']))
        else:
            return ''

    def _parse_cell_def(self, el_def):
        pattern = re.compile(r"""
          (?:(?P<flag>\w+)=)?      # ignore if passed the full string
          (?P<val>[^/:<>]*)        # value
          (?:/(?P<var>[^:]+))?     # variable
          (?:(?::(?P<w>[\d]*))?      # width
          \.?
          (?P<h>-?[\d]+)?)?            # height
          (?P<align>[-<>])?         # align, a < or a > at the end of the string
        """, re.VERBOSE)
        match = pattern.search(el_def)
        self.class_flag = match.group("flag")
        self.val = match.group("val")
        self.var = match.group("var")
        self.w = match.group("w")
        self.h = match.group("h")
        self.align = match.group("align")
        #dbg.write("el: %s w=%s h=%s align=%s-" % (el_def,self.w,self.h, self.align))
        #print  "_parse_cell_def: el: %s var=%s val=%s h=%s align=%s" % (
        #    el_def,self.var,self.val, self.h, self.align)
        #print match.groups()
        if not self.var:
            ## radiobutton use self.val as 'group'
            if not re.search("GtkRadioButton",self.gtkClass):
                self.var = self.val

        ## let's set a reasonable key. Strip any width info
        # not sure If I should put all Containers
        cont_pat = "Gtk(Frame|Table|HBox|VBox|Notebook)"
        if not re.search(cont_pat,self.gtkClass):
            self.lw['el_key'] = re.sub('(:.*)|[-<>]$','',el_def)
        else:
            self.lw['el_key'] = re.sub('[-<>|=]$','',el_def)

        ### gtk-stock?
        if re.match('gtk-', self.val):
            if re.match('GtkToolButton', self.gtkClass):
                self.properties['stock_id'] = re.sub('\..+','',self.val)
                self.properties['label'] = None
            elif re.match('GtkButton', self.gtkClass):
                self.properties['label'] = re.sub('\..+','',self.val)
                #dbg.write(self.properties['label'])
                self.properties['use-stock'] = True
            else:
                self.properties['use-stock'] = True


    def _labels_and_tips_from_info(self):
        if not self.class_flag:
            return

        ## try first a less specific (that w/0 'mod=' part)
        if False:
            bd0 = "&lt;b%gt;"
            bd1 = "&lt;/b%gt;"
        else:
            bd0 = ''
            bd1 = ''
            
        name = self.val
        #dbg.write("##1 name = %s - el_def: %s" % (name, self.el_def))
        try:
            self.val = "%s%s%s" % (bd0, info[self.val][0], bd1)
        except:
            pass
        
        try:
            self.properties['tooltip'] = info[name][1]
        except:
            pass

        ## try if there is a more specific entry
        key = "%s=%s" % (self.class_flag, name)
        try:
            self.val = "%s%s%s" % (bd0, info[key][0], bd1)

        except:
            pass
    
        try:
            self.properties['tooltip'] = info[key][1]
        except:
            pass



    def _set_dimentions(self):
        """Give a meaning to dimentions for this object"""
        ## width
        if self.w and  'w' in self.transpose:
            name = self.transpose['w']
            self.properties[name] = self.w
            #self.pack_properties['x_options'] = 'shrink'
        ##  'height'
        if self.h and  'h' in self.transpose:
            name = self.transpose['h']
            self.properties[name] = self.h
            
    def rowspan(self):
        if self.lw['container'] in ('T'):
            self.pack_properties['bottom_attach'] += 1
#         else:
#             dbg.warning("Span available only for Table qui: %s" % \
#                       self.lw['container'])

    def colspan(self):
        if self.lw['container'] in ('T'):
            self.pack_properties['right_attach'] += 1
#         else:
#             dbg.write("Span available only for Table qui: %s" % self.lw['container'])


    def _class_specific(self):
        pass
    
    ### Real pack
    def xml(self, ContGtkClass=None):
        return "%s\n%s" % (self._widget_xml(),
                           self._packing_xml(self.pack_properties,ContGtkClass))

    def create(self):
        """ Create the wdget """
        #dbg.write(self.gtkClass)
        #print dbg.dshow(self.properties)
        self.gtkWdg = gobject.new(gobject.type_from_name(self.gtkClass))
        # **self.properties
        for p, val in self.properties.iteritems():
            try:
                self.gtkWdg.set_property(p, val)
            except:
                pass
                #dbg.write("Fail prop %s for %s" % (p, self.gtkClass))

        return self.gtkWdg
                          
    def _packing_xml(self, pack_properties, ContGtkClass):
        # no packing if addind with 'addto'. In that case ContGtkClass
        # is not defined
        if not ContGtkClass:
            return ""

        allowed_pack_properties = ()
        for i in gtk.container_class_list_child_properties(ContGtkClass):
            allowed_pack_properties += (i.name,)

        xml = ["<packing>"]
        for key, value in pack_properties.iteritems():
            ## tabs label are child of notebook but of a type that
            ## is not returned by container_class... funcition above
            if (key == 'type' and ContGtkClass == 'GtkNotebook') \
                   or key.replace('_','-') in allowed_pack_properties:
                 xml.append('  <property name="%s">%s</property>' % (key, value))
        xml.append("</packing>")
       
        return "\n".join(xml)
    
    def _widget_xml(self):
        # If a children is v_expandable, the parent becomes too.
        if 'children_list' in self.lw and self.lw['children_list']:
            if True in [child.v_expand for child in self.lw['children_list']]:
                self.make_v_expandable()
    
        xml = ['<widget class="%(gtkClass)s" id="%(el_key)s">' % self.lw]
        inner_xml = []
        # write properties with order before
        extra_text = ""
        for key in self.ordered_properties:
            value = self.properties[key]
            if key in self.transpose:
                pass
                #print key, self.transpose[key]
            if key in ('text', 'label'):
                extra_text = ' translatable="yes"'
                if value == '':
                    value = None
            else:
                extra_text = ""
                
            if value:
                inner_xml.append('<property name="%s"%s>%s</property>' %\
                                (key, extra_text, value))
        
        # now write everything else
        extra_text = ""
        for item, value in self.properties.iteritems():
            if item not in self.ordered_properties:
                if item in self.transpose:
                    item = self.transpose[item]
                if item in ('text', 'label'):
                    extra_text = ' translatable="yes"'
                else:
                    extra_text = ""
                    
                if value is not None:
                    inner_xml.append('<property name="%s"%s>%s</property>' %\
                                     (item, extra_text, value))

        children = self._children_xml()
        if children:
            inner_xml.append(children)
        xml.append(self._offset_txt("\n".join(inner_xml), 2))
        xml.append("</widget>")
        return "\n".join(xml)

    def _children_xml(self):
        # this is significant only for LContainer
        return None

    def _offset_txt(self, txt, amount):
        ## offset text to get a prettier xml
        p = re.compile("^", re.MULTILINE)
        return p.sub(' ' * amount, txt)

    def make_v_expandable(self):
        """Teach a widget it must expand (vertically); it can be because it has
        a viewing benefit (e.g: a Treeview) or because a child of it has.
        """
        if self.v_expand:
            return
        self.v_expand = True
        # FIXME: (how?!) this expands horizontally if parent is a HBox
        self.pack_properties.update({'expand' : True})
        self.pack_properties.update({'y-options' : 'expand | fill'})


class LContainer(LWidget):
    # the difference with LWidget is it has children
    # and the el_def is not written in the layout but created on the fly
    # (Layout._create_container_label). We use it as label

    def __init__(self, el_def, pos, container, children_list=None,
                 elements=None):
        #super(LContainer, self).__init__(el_def, pos, container, elements)
        LWidget.__init__(self, el_def, pos, container, elements=elements)
        ## the children
        self.lw['children_list'] = children_list
        #self.properties['label'] = el_def
        
    def _children_xml(self):
        txt = ''
        try: 
            for obj in self.lw['children_list']:
                child = self._offset_txt(obj.xml(self.gtkClass), 4)
                txt += "\n<child>\n%s\n</child> <!-- closes %s in %s -->\n" % (
                    child, obj.lw['el_key'], obj.lw['container'])
        except:
            pass
        return txt
    def create(self, visible=None):
        """ Create the wdget """
        if visible is not None:
            self.properties['visible'] = visible
            
        #dbg.write(self.gtkClass)
        self.gtkWdg = gobject.new(gobject.type_from_name(self.gtkClass),
                          **self.properties)

        #dbg.write(gtkWdg)
        self.add_children(self.gtkWdg)
        return self.gtkWdg
                          
    def add_children(self, gtkWdg):

        if not self.lw['children_list']:
            return
        
        for obj in self.lw['children_list']:
            #dbg.write("gtkWdg", gtkWdg, obj.gtkClass)
            child = obj.create()
            pack_props = self.clean_pack_properties(obj.pack_properties, gtkWdg)
            
            if self.gtkClass not in ('GtkTable'):
                #dbg.write('%s.add(%s, %s)' %(gtkWdg, child, pack_props ))
                gtkWdg.add(child)
                for p, val in pack_props.iteritems():
                    #dbg.write("%s.set_property(%s, %s)" % (gtkWdg, p, val))
                    setattr(gtkWdg, p, val)
            if self.gtkClass == 'GtkTable':
                P = pack_props
                #dbg.write("pack_props", P, obj.pack_properties)
                gtkWdg.attach(child,
                           P['left_attach'],
                           P['right_attach'],
                           P['top_attach'],
                           P['bottom_attach'],
                           )

        return 
    def clean_pack_properties(self, pack_props, gtkWdg):
        return pack_props
#         dbg.write(gtkWdg, gtkWdg.name)
#         dbg.write(gtk.container_class_list_child_properties(gtkWdg))
#         props = [p.name for p in gtk.container_class_list_child_properties(gtkWdg)]
#         dbg.write(props)
#         ko = []
#         for p in pack_props:
#             if p not in props:
#                 ko += [p]
#         for p in ko:
#             del pack_props[p]
#         dbg.write(pack_props)
#         return pack_props

class AlignmentEntry(LContainer):
    gtkClass = 'GtkAlignment'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        #dbg.write("EventLabel ", el_def)
        el_def = el_def.replace('ae=','A=')
        super(LContainer, self).__init__(el_def, pos, container, elements=elements)
        ## prepare the names...

        entry_str   = "e=%s" % (el_def.replace('A=',''))
        #print "ENTRY_STR", entry_str
        ## and create the children
        #print "EventLabel elements: ", elements.keys()
        wdg = Entry(entry_str,(0,0),    'A', elements=elements)
        self.lw['children_list'] = [ wdg ]
        if self.align == '-':
            self.properties['xscale'] = 1
        else:
            self.properties['xscale'] = 0

        if self.align == '>':
            self.properties['xalign'] = 1
        else:
            self.properties['xalign'] = 0

    def _class_specific(self):
        self.pack_properties.update({
            'x_options' : 'expand|fill',
            })

class Entry(LWidget):
    gtkClass = 'GtkEntry'
    transpose = {
        'w' : 'width_chars',
        }
    def _class_specific(self):

        if self.w:
            self.properties['max-length'] = self.w

#         if self.align:
#             ## !!! really I don't have 'elements' here, but the entry has already
#             ##     been registered...
#             align = Alignment(el_def.replace('e=','A='), pos, container,
#                               children_list=self, elements=None)
#             if self.align in '<':
#                 align.properties['xalign'] = 0
#             else:
#                 align.properties['xalign'] = 1
#             self = align
            
class DateEdit(LWidget):
    gtkClass = 'Custom'
    ## this widget is provided by dateedit module
    ## it's a pity set_custom_handler should only use str1, str2, int1, int2
    transpose = {
        'time' : 'string1',
        'show-time' : 'string2',
        }
    class_properties = {
        'creation_function' : 'lay_dateedit',
#        'int1' : '',
#        'int2' : '',
        'time' : None,
        'lower-hour' : 10,
        'upper-hour' : 23,
        'show-time' : None,
        'use-24h-format' : False
        }
            
class FkEdit(LWidget):
    gtkClass = 'Custom'
    class_properties = {
        'creation_function' : 'fk_edit',
        }
            
class Calendar(LWidget):
    # TODO: add a constructor to pass dates in a friendly way
    gtkClass = 'GtkCalendar'
    def _class_specific(self):
        self.pack_properties.update({'y_options': ""})
    #class_properties = {
        #'visible'     : True,
        #'day'     : 7,
        #'month'     : 3,
        #'year'     : 1963,
        #}
    

class TreeView(LWidget):
    gtkClass = 'GtkTreeView'
    transpose = {
        'w' : 'width_request',
        'h' : 'height_request',
        }
    class_properties = {
        'width_request'  : '300',
        'height_request'  : '-1',
        }

    def _class_specific(self):
        self.make_v_expandable()

class TextView(LWidget):
    gtkClass = 'GtkTextView'

class Statusbar(LWidget):
    gtkClass = 'GtkStatusbar'
    
    def _class_specific(self):
        if self.container_flag == "T":
            self.pack_properties.update({'y_options': ''})
        elif self.container_flag == "V":
            self.pack_properties.update({'pack_type': 'GTK_PACK_END'})


class Label(LWidget):
    gtkClass = 'GtkLabel'
    transpose = {
        'w' : 'width_chars',
        }
    def _class_specific(self):
        self.properties.update({
            'xalign' : '1',
            'label'  : self.val.replace('_',' ')+ ':',
            'xpad'   : 10,
            'use-markup' : True,
            })
        self.pack_properties.update({
            'y_options' : 'fill',
            'x_options' : 'fill',
            })
        if self.align:
            #dbg.debug("SELF ALIGN for ", self.lw['el_key'])
            if self.align in '<':
                #dbg.debug("""properties['xalign'] = 0""")
                self.properties['xalign'] = 0
            else:
                self.properties['xalign'] = 1

class LabelFill(LWidget):
    gtkClass = 'GtkLabel'
    
    def _class_specific(self):
        self.properties.update({
            'xalign' : '0',
            'label'  : self.val,
            'xpad'   : 10,
            })
        self.pack_properties.update({
            'y_options' : 'expand|shrink|fill',
            })

class NotebookLabel(Label):
    """This is for the tab of a notebook"""
    gtkClass = 'GtkLabel'
    
    def _class_specific(self):
        ## must overwrite any other info
        self.pack_properties = {
            'type' : 'tab',
            }

class FrameLabel(Label):
    """This is for the tab of a notebook"""
    gtkClass = 'GtkLabel'
    class_properties = {
        'xpad' : 5,
        }    
    def _class_specific(self):
        ## must overwrite any other info
        self.pack_properties = {
            'type' : 'label_item',
            }

class Button(LWidget):
    gtkClass = 'GtkButton'
#     transpose = {
#         'w' : 'width_chars',
#         }
    class_pack_properties = {
        'expand' : False,
        'fill'   : True,
        }

    def _class_specific(self):
        self.properties.update({
            'xalign' : '0',
            'label'  : re.sub('\..+','',self.val)
            })        
        
        self.pack_properties.update({'y_options': ""})


class ToolButton(LWidget):
    gtkClass = 'GtkToolButton'

    def _class_specific(self):
        if re.match("gtk-",self.val):
            del self.properties['label'] 
            #self.properties['stock_id'] = self.val

class RadioButton(Button):
    gtkClass = 'GtkRadioButton'
    def _class_specific(self):
        if self.var:
            ## this puts this radioButton in the same group as the radiobutton
            ## written after the '/'
            self.properties['group'] = 'r=' + self.var

class ToggleButton(Button):
    gtkClass = 'GtkToggleButton'
    
class CheckButton(Button):
    gtkClass = 'GtkCheckButton'
    def _class_specific(self):
        self.properties['label'] = ''

class ComboBox(Entry):
    gtkClass = 'GtkComboBox'

class ComboBoxEntry(Entry):
    gtkClass = 'GtkComboBoxEntry'

class SpinButton(LContainer):
    gtkClass = 'GtkSpinButton'
    class_properties = {
        "can_focus"     : True,
        "climb_rate"    : 1,
        "digits"        : 0,
        "numeric"       : True,
        "update_policy" : 'GTK_UPDATE_ALWAYS',
        "snap_to_ticks" : False,
        "wrap"          : False,
        "adjustment"    : '0 0 1000 1 10 10',
        }

class ToolSpinButton(LContainer):
    gtkClass = 'GtkToolItem'
    def __init__(self, el_def, pos, container, elements):
        el_def = el_def.replace('ts=', 'ti=')
        #super(LContainer, self).__init__(el_def, pos, container=container, elements=elements)
        super(ToolSpinButton, self).__init__(el_def, pos, container=container, elements=elements)
        ## if spinbutton in toolbar, we need to encapsulate in a ToolItem
        spin_def = el_def.replace('ti=','s=')
        spin = SpinButton("%s" % (spin_def), (0,0), 'ti', elements=elements)
        self.lw['children_list'] = [ spin  ]
        #self.el_def = "ti=%s" % (self.var)
            
class Image(LWidget):
    gtkClass = 'GtkImage'

    def _class_specific(self):
        ## self.var is probably the name of a image file
        ## let's check, look for it and set it with a full path
        cdir = os.getcwd()
        filename = os.path.join(cdir,self.var)
        if os.stat(filename):
            self.properties['pixbuf'] = filename
        else:
            print "Missing image: " + filename

class Window(LContainer):
    gtkClass = 'GtkWindow'
    ## secondo me questo non dovrebbe essere necessario
    class_pack_properties  = {  }
    class_properties = {
        'visible' :            True,
        'title' :              'window1',
        'type' :               'GTK_WINDOW_TOPLEVEL',
        'window_position' :    'GTK_WIN_POS_NONE',
        'modal' :              False,
        'resizable' :          True,
        'destroy_with_parent' : False,
        'decorated' :          True,
        'skip_taskbar_hint' :  False,
        'skip_pager_hint' :    False,
        'type_hint' :          'GDK_WINDOW_TYPE_HINT_NORMAL',
        'gravity' :            'GDK_GRAVITY_NORTH_WEST',
        }    


    def _packing_xml(self, packing_info, ContGtkClass):
        return ''

class Table(LContainer):
    gtkClass = 'GtkTable'
    class_pack_properties = {
        'homogeneous' : False,
#        'expand'       : True,
        'y_options' : 'shrink',
#        'y_options' : 'expand|fill',
        'x_options' : 'shrink',
        }
    #def _class_specific(self):
        #self.pack_properties.update({"y_options": ""})

class VBox(LContainer):
    gtkClass = 'GtkVBox'
    class_pack_properties = {
        'padding' : '0',
        'expand'  : False,
        'fill'    : False,
        }
    
    class_properties = {
        'homogeneous' : False,
        'spacing' : 0,
        }
    
class HBox(VBox):
    gtkClass = 'GtkHBox'
    
class Layout(LContainer):
    gtkClass = 'GtkLayout'
    
class Fixed(LContainer):
    gtkClass = 'GtkFixed'
    
class ScrolledWindow(LContainer):
    gtkClass = 'GtkScrolledWindow'
    def _class_specific(self):
        self.properties.update({
            'hscrollbar_policy' : 'GTK_POLICY_AUTOMATIC',
            'vscrollbar_policy' : 'GTK_POLICY_AUTOMATIC',
            'shadow_type'       : 'GTK_SHADOW_IN',

        })

        self.pack_properties.update({
            'expand' : True,
            'fill' : True,
            #'y_options' : 'GTK_EXPAND|GTK_FILL',
            #'y_options' : 'GTK_EXPAND|GTK_FILL',
            })
    

class Notebook(LContainer):
    gtkClass = 'GtkNotebook'
    def _class_specific(self):
        self.make_v_expandable()

class VPaned(LContainer):
    gtkClass = 'GtkVPaned'
    class_pack_properties = {
        'resize' : False,
        }
    def _class_specific(self):
        self.make_v_expandable()

class HPaned(VPaned):
    gtkClass = 'GtkHPaned'
    #class_pack_properties = VPaned.class_pack_properties

class DrawingArea(LWidget):
    gtkClass = 'GtkDrawingArea'
    
class HandleBox(LContainer):
    gtkClass = 'GtkHandleBox'
    
class Expander(VPaned):
    gtkClass = 'GtkExpander'
    class_properties = {
        'expanded' : False,
        'border_width' : 3,
        }
    def _class_specific(self):
        label = self.el_def.replace('X.','').replace('_',' ')
        self.properties['label'] = label
    
class ViewPort(LContainer):
    gtkClass = 'GtkViewport'
    
class Frame(LContainer):
    # a frame conta
    gtkClass = 'GtkFrame'
    class_properties = {
        'label_xalign' : 0,
        'border_width' : 6,
        'label_yalign' : 0.5,
        'shadow_type' : 'GTK_SHADOW_ETCHED_IN',
        }
    
class FrameWithLabel(LContainer):
    # a frame conta
    gtkClass = 'GtkFrame'
    class_properties = {
        'label_xalign' : 0,
        'label_yalign' : 0.5,
        'border_width' : 6,
        'shadow_type' : 'GTK_SHADOW_ETCHED_IN',
        }
    
    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        super(LContainer, self).__init__(el_def, pos, container, elements)
        ## prepare the names...
        al_str = "A=%s" % (self.val.replace('F','') )
        ## and create the children. We pass the child over to Alignment
        alignment = Alignment(al_str,(0,0),    'F' ,
                              children_list=children_list, elements=elements)
        self.lw['children_list'] = [ alignment ]
        ## correct the parent_container of the child
        alignment.lw['container_flag'] = 'A'
        
class Alignment(LContainer):
    gtkClass = 'GtkAlignment'
    class_properties = {
        'xalign' : 0.5,
        'yalign' : 0,
        'xscale' : 1,
        'yscale' : 1,
        'top_padding' : 4,
        'bottom_padding' : 4,
        'left_padding' : 8,
        'right_padding' : 4,
        }
    
class EventBox(LContainer):
    gtkClass = 'GtkEventBox'
    class_properties = {
        'visible_window'  : True,
        'above_child' : False,
        }
    def _class_specific(self):
        ## not executed frm EventLabel
        pass

class EventLabel(LContainer):
    gtkClass = 'GtkEventBox'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        #dbg.write("EventLabel ", el_def)
        el_def = el_def.replace('L=','E=')
        super(LContainer, self).__init__(el_def, pos, container, elements=elements)
        ## prepare the names...

        lbl_str   = "l=%s:.%s" % (el_def.replace('E=',''), self.w or '')
        ## and create the children
        #print "EventLabel elements: ", elements.keys()
        label = Label(lbl_str,(0,0),    'E', elements=elements)
        self.lw['children_list'] = [ label ]
        
    def _class_specific(self):
        self.pack_properties.update({
            'x_options' : 'fill',
            })


class ComboLE(LContainer):
    # it'a HBox/VBox with a label and an entry
    gtkClass = 'GtkVBox'

    def __init__(self,  el_def, pos, container, children_list=[], elements=None):
        super(ComboLE, self).__init__(el_def, pos, container, elements=elements)
        ## prepare the names...
        lbl_str   = "E=%s:%s%s" % (self.val, self.w or '', self.align or '')
        entry_str = "e=%s:%s%s" % (self.var, self.h or '', self.align or '')
        #dbg.debug(entry_str, lbl_str, self.w, self.h)
        ## and create the children
        label = EventLabel(lbl_str,(0,0),    'V', elements=elements)
        entry = Entry(entry_str,(0,1),  'V', elements=elements)
        self.lw['children_list'] = [ label, entry ]
        ### w and h are there only to propagate to label & entry
        self.w = None
        self.h = None
        try:
            del self.properties['height_request']
        except:
            pass
    
    def _class_specific(self):
        self.pack_properties.update({"y_options": ""})

class Tollerance(LContainer):
    gtkClass = 'GtkFixed'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        el_def = el_def.replace('Toll=','Fix=')
        super(LContainer, self).__init__(el_def, pos, container, elements)
        ## prepare the names...
        #lbl = "L=%s" % (self.val)
        wdg1 = "e=%s" % (self.el_def.replace('Fix=',''))
        wdg2 = "e=%s_toll_op" % (self.el_def.replace('Fix=',''))
        wdg3 = "e=%s_toll" %    (self.el_def.replace('Fix=',''))
        

        ## and create the children
        w1 = Entry(wdg1, (0,0),    container='Fix', elements=elements)
        w2 = Entry(wdg2, (0,0),    container='Fix', elements=elements)
        w3 = Entry(wdg3, (0,0),    container='Fix', elements=elements)
        self.lw['children_list'] = [ w1, w2, w3  ]
        w1.pack_properties['x'] = 0
        w1.pack_properties['y'] = 0
        w1.properties['width_request'] = 60

        w2.pack_properties['x'] = 70
        w2.pack_properties['y'] = 0
        w2.properties['width_request'] = 40

        w3.pack_properties['x'] = 120
        w3.pack_properties['y'] = 0
        w3.properties['width_request'] = 60

    def _class_specific(self):
        self.pack_properties.update({
            'expand' : True,
            'fill' : True,
            })
        
class ScrolledTreeView(LContainer):
    gtkClass = 'GtkScrolledWindow'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        el_def = el_def.replace('TVS=','S=')
        super(LContainer, self).__init__(el_def, pos, container, elements)
        ## prepare the names...
        tree = "TV=%s:%s.%s" % (self.val, self.h or '', self.w or '')

        ## and create the children
        new = TreeView(tree,(0,0),    'S', elements)
        self.lw['children_list'] = [ new  ]
    def _class_specific(self):
        self.pack_properties.update({
            'expand' : True,
            'fill' : True,
            })
        

class ScrolledLayout(ScrolledWindow):
    gtkClass = 'GtkScrolledWindow'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        el_def = el_def.replace('LS=', 'S=')
        super(LContainer, self).__init__(el_def, pos, container=container, elements=elements)
        ## prepare the names...
        tree = "Lay=%s:%s.%s" % (self.val, self.h or '', self.w or '')

        ## and create the children
        new = Layout(tree,(0,0),    'S', elements=elements)
        self.lw['children_list'] = [ new  ]
    def _class_specific(self):
        self.pack_properties.update({
            'expand' : True,
            'fill' : True,
            })
        

class ScrolledTextView(ScrolledWindow):
    gtkClass = 'GtkScrolledWindow'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        el_def = el_def.replace('TXS=','S=')
        #super(LContainer, self).__init__(el_def, pos, container, elements)
        ScrolledWindow.__init__(self, el_def, pos, container=container, elements=elements)
        ## prepare the names...
        tree = "TX=%s:%s.%s" % (el_def.replace('S=',''), self.h or '', self.w or '')

        ## and create the children
        new = TextView(tree,(0,0),    'S', elements=elements)
        self.lw['children_list'] = [ new  ]
        
class ScrolledDrawingArea(ScrolledWindow):
    gtkClass = 'GtkScrolledWindow'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        el_def = el_def.replace('daS=','S=')
        #super(LContainer, self).__init__(el_def, pos, container, elements)
        ScrolledWindow.__init__(self, el_def, pos, container=container, elements=elements)
        ## prepare the names...
        wdg = "da=%s:%s.%s" % (self.val, self.h or '', self.w or '')
        #dbg.write('wdg', wdg)
        ## and create the children
        new = DrawingArea(wdg,(0,0),    'S', elements=elements)
        self.lw['children_list'] = [ new  ]
        

class MenuBar(LContainer):
    gtkClass = 'GtkMenuBar'
    class_pack_properties = {
        'y_options' : 'fill'
        }
    def _class_specific(self):
        if self.container_flag == "T":
            #self.pack_properties.update({'y_options': ''})
            self.pack_properties.update({'y_options': 'fill'})

class Menu(LContainer):
    gtkClass = 'GtkMenu'
    # I don't mean to fill it up with MenuItems. I'll 

class ToolItem(LContainer):
    gtkClass = 'GtkToolItem'

class MenuItem(LContainer):
    gtkClass = 'GtkMenuItem'
    parent = 'm'

    def __init__(self,  el_def, pos, container, children_list=[], elements={}):
        super(MenuItem, self).__init__(el_def, pos, container, [], elements)
        #print "MENU: " + el_def
        ## prepare the names...
        menu = "M=%s" % (self.val)

        ## and create the children
        new = Menu(menu,(0,0), self.parent, children_list=[], elements=elements)
        #print "new menu ", new, menu, self.parent
        self.lw['children_list'] = [ new  ]

    def _class_specific(self):
        self.properties['label'] = self.val
        self.properties['use_underline'] = True
        
        # specify that we want write label before use_underline
        self.ordered_properties = ["label", "use_underline"]
        
#         for f in self.lw['children_list']:
#             dbg.debug("%s %s" % (self, self.lw['children_list']))

class MenuToolButton(MenuItem):
    gtkClass = 'GtkMenuToolButton'
    parent = 'tm'
#     transpose = {'var' : 'label',
#                  }
#     # I don't mean to fill it up with MenuItems. I'll 

class Toolbar(LContainer):
    gtkClass = 'GtkToolbar'
    # fixme; transpose does nos seem to work...
    transpose = {'width' : 'width_request',
                 'height' : 'height_request'
                 }
    def _class_specific(self):
        if self.container_flag == "T":
            self.pack_properties.update({'y_options': ''})


class ColorSelection(LWidget):
    gtkClass = 'GtkColorSelection'
    
class ColorButton(LWidget):
    gtkClass = 'GtkColorButton'
    

_W = {
    'l'   : Label,
    'lf'  : LabelFill,
    'L'   : EventLabel,
    'nl'  : NotebookLabel,
    'fl'  : FrameLabel,
    'e'   : Entry,
    'ae'   : AlignmentEntry,
    'd'   : DateEdit,
    'da'   : DrawingArea,
    'i'   : Image,
    'b'   : Button,
    'r'   : RadioButton,
    't'   : ToggleButton,
    'ti'  : ToolItem,
    'tb'  : ToolButton,
    'c'   : CheckButton,
    's'   : SpinButton,
    'ts'  : ToolSpinButton,
    'Toll'   : Tollerance,
    'C'   : ComboBox,
    'Ce'  : ComboBoxEntry,
    'fk'  : FkEdit,
    'TV'  : TreeView,
    'TX'  : TextView,
    'daS' : ScrolledDrawingArea,
    'TVS' : ScrolledTreeView,
    'TXS' : ScrolledTextView,
    'cal' : Calendar,
    'sb'  : Statusbar,
    'Col' : ColorSelection,
    'ColB': ColorButton,

    # containers
    'T': Table,
    'W': Window,
    'E': EventBox,
    'X': Expander,
    'V': VBox,
    'H': HBox,
    'le': ComboLE,
    'S' : ScrolledWindow,
    'N' : Notebook,
    'h' : HPaned,
    'v' : VPaned,
    'p' : ViewPort,
    'f' : Frame,
    'Fix' : Fixed,
    'F' : FrameWithLabel,
    'A' : Alignment,
    'm2m' : Alignment,  # used in sqlkit m2m, m2o layout definition
    'm2o' : Alignment,
    'o2m' : Alignment,
    'o2o' : Alignment,
    'Lay' : Layout,
    'LS' : ScrolledLayout,
    


    'B': MenuBar,
    'M': Menu,
    'm': MenuItem,
    'tm': MenuToolButton,
    'O': Toolbar,
    'Z': HandleBox,
    'cont_regexp' : '[EXTHVNPSvhpOBmMFfAZ]',
    }


def custom_widget(glade, function_name, widget_name,
                  str1=None, str2=None, int1=None , int2=None):

    if function_name == 'lay_dateedit':
        import dateedit
        d = dateedit.DateEdit()
        d.set_property('show-time', False)
        d.show()
        return d

    if function_name == 'fk_edit':
        import fk_entry
        fk = fk_entry.FkEdit()
        fk.show()
        return fk



