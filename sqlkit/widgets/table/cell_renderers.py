from datetime import datetime
import gtk, gobject, pango
import dbg

class CellEditableCalendar(gtk.TextView, gtk.CellEditable):
    date = None
    def __init__(self, datetime, pos=None, wdg=None, cell_area=None):

        self.datetime = datetime
        gtk.TextView.__init__(self)
        #self.set_has_window(False)
        self.cal = gtk.Calendar()
        #self.cal.show()
        self.cal.select_month(self.datetime.month - 1, self.datetime.year)
        self.cal.select_day(self.datetime.day)
        self.w = gtk.Window(gtk.WINDOW_POPUP)
        #self.set_editable(False)
        self.w.add(self.cal)
        #self.w.connect("delete_event", self.delete_event)
        self.cal.connect("day-selected-double-click", self.delete_event)
        self.cal.connect("event", self.cal_event)
        self.position_popup(wdg, self.w, cell_area)
        self.show_all()
        self.grab_focus()
        self.w.show_all()
        self.connect('key-press-event', self.keypress_event)
        
    def position_popup(self, widget, popup, ca):
        # the get_origin method returns  the origin comprising the headers
        # the get_cell _area don't!!! (so I add cell_height doing 2*...))

        # you need child to show_all() to get the dimentions correctly
        child = popup.get_children()[0]
        child.show_all()

        popup_width, popup_height = popup.size_request()
        x, y = gtk.gdk.Window.get_origin(widget.window)

        # path, col, x1, y1 = widget.get_path_at_pos(event.x, event.y)
        # ca = widget.get_cell_area(path, col)

        X = x + ca.x
        Y = y + ca.y + 2*ca.height + 4

        # border case: the cell is too close to the border to allow the window
        # I don't want the mouse to be over the popup since an undesired click
        # would change the date...
        if Y + popup_height> gtk.gdk.screen_height():
            Y = y +  ca.y + ca.height - popup_height 
        if X + popup_width> gtk.gdk.screen_width():
            X = gtk.gdk.screen_width() - popup_width 

        popup.move(X, Y)


    def keypress_event(self, w, event):
        accelname = gtk.accelerator_name(event.keyval, event.state)
        if accelname == 'Delete':
            self.date = None
            self.emit('editing-done')
            return True
        
        return False
        
    def cal_event(self, w, e):
        text = self.get_calendar_date().strftime("%d/%m/%y")
        tb = self.get_buffer()
        tb.set_text(text)
        return False
    
    def do_start_editing(self, event):
        pass
    
    def do_remove_widget(self):
        pass
    
    def do_stop_editing(self):
        
        self.w.destroy()
        self.destroy()
    
    def do_editing_done(self):
        self.w.destroy()
        self.destroy()
        pass
    
    def delete_event(self,w = None, e = None):
        date = self.get_calendar_date()
        try:
            self.datetime = datetime.combine(date, self.datetime.time())
        except Exception, e:
            print e
            self.datetime = date
            
        self.emit('editing-done')
        self.w.destroy()
        self.destroy()
        return True

    def get_calendar_date(self):
        """calendare return a tuple: genuary is 0!"""

        calendar_tuple = list(self.cal.get_date())
        calendar_tuple[1] += 1
        return datetime(*tuple(calendar_tuple))
        
    
gobject.type_register(CellEditableCalendar)    

class CellRendererDate(gtk.GenericCellRenderer):
    date = None
##     editable = None

    __gproperties__ = {
        'date': (gobject.TYPE_PYOBJECT,
                 'date of cell',
                 'date object contained in cell',
                 gobject.PARAM_READWRITE)
        }

    __gsignals__ = {
        'date-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                         (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
                          )
        }    
    def __init__(self, *args, **kwargs):
        #dbg.write()
        self.date = None

        return gtk.CellRenderer.__gobject_init__(self, *args, **kwargs)
    
    def do_pango_layout(self, widget):
        pc = widget.get_pango_context()
        pl = pango.Layout(pc)
        pl.set_text(self.date_formatter(self.date))
        return pl
    
    def do_get_size(self, widget, cell_area):

        #dbg.show_caller()
        xpad = self.get_property('xpad')
        ypad = self.get_property('ypad')


        xalign = self.get_property('xalign')
        yalign = self.get_property('yalign')


        layout = self.do_pango_layout(widget)
        width, height = layout.get_pixel_size()


        x_offset = xpad
        y_offset = ypad


        if cell_area:

            x_offset = xalign * (cell_area.width - width)
            x_offset = max(x_offset, xpad)
            x_offset = int(round(x_offset, 0))


            y_offset = yalign * (cell_area.height - height)
            y_offset = max(y_offset, ypad)
            y_offset = int(round(y_offset, 0))


        width  = width  + (xpad * 2)
        height = height + (ypad * 2)


        return x_offset, y_offset, width, height
    
    
    def date_formatter(self, date):
        if date is None:
            return "--/--/--"

        return date.strftime("%d/%m/%y")
    
    
    def do_start_editing(self, event, widget, path, background_area,
                         cell_area, flags):

        if self.date is None:
            date = datetime.now()
        else:
            date = self.date
        #dbg.ddir(cell_area)
        ce = CellEditableCalendar(datetime = date, cell_area=cell_area,
                                  wdg=widget)
#        ce = CellEditableCalendar(date = date, pos=(event.x, event.y))
        ce.show()
        ce.grab_focus()
        ce.connect('editing-done', self.editing_done, widget, path)
        
        return ce
    
    def editing_done(self, widget, treeview, path):

        self.stop_editing(True)
        self.emit('date-changed', path, widget.datetime)
        print "NUOVA", widget.datetime
        return True
    
    def do_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):
        
        #dbg.write()
        
        x_offset, y_offset, width, height = self.do_get_size(widget, cell_area)
        pl = self.do_pango_layout(widget)
        widget.get_style().paint_layout(window,
                                        gtk.STATE_NORMAL,
                                        True,
                                        cell_area,
                                        widget,
                                        'foo',
                                        cell_area.x + x_offset,
                                        cell_area.y + y_offset,
                                        pl)
    
    def do_set_property(self, gprop, value):
        setattr(self, gprop.name, value)
        
if gobject.pygtk_version < (2, 8):
    gobject.type_register(CellRendererDate)


class CellRendererDatetime(CellRendererDate):
    datetime = None
##     editable = None

    __gproperties__ = {
        'datetime': (gobject.TYPE_PYOBJECT,
                 'datetime of cell',
                 'datetime object contained in cell',
                 gobject.PARAM_READWRITE)
        }

    __gsignals__ = {
        'datetime-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                         (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
                          )
        }    

    def __init__(self, *args, **kwargs):
        #dbg.write()
        self.datetime = None

        return gtk.CellRenderer.__gobject_init__(self, *args, **kwargs)
    
    def do_pango_layout(self, widget):
        pc = widget.get_pango_context()
        pl = pango.Layout(pc)
        pl.set_text(self.date_formatter(self.datetime))
        return pl
    
    
    def date_formatter(self, date_time):
        if date_time is None:
            return "--/--/-- --:--"
        ## FIXME: should be read from some settings...
        return date_time.strftime('%d/%m/%Y %H:%M')

    def do_start_editing(self, event, widget, path, background_area,
                         cell_area, flags):

        if self.datetime is None:
            date_time = datetime.now()
        else:
            date_time = self.datetime
        #dbg.ddir(cell_area)
        ce = CellEditableCalendar(datetime = date_time, cell_area=cell_area,
                                  wdg=widget)

#        ce = CellEditableCalendar(date = date, pos=(event.x, event.y))

        ce.show()
        ce.grab_focus()
        ce.connect('editing-done', self.editing_done, widget, path)
        
        return ce
    
    def editing_done(self, widget, treeview, path):
            
        self.stop_editing(True)
        self.emit('datetime-changed', path, widget.datetime)
        return True
    


