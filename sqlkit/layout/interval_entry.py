"""
Very very minimal widget to edit intervals in 4 entry
Mainly used to make test  pass. I gues anybody that need to work with intervals
should work out a bettere widget an possibly contribute it...


"""
import gobject
import gtk
from datetime import timedelta

class IntervalEdit(gtk.Alignment):
    __gtype_name__ = 'IntervalEntry'

    __gproperties__ = {
        'interval' : (gobject.TYPE_PYOBJECT,             # type
                    'Interval',                          # nick name
                    'The interval currently selected',   # description
                    gobject.PARAM_READWRITE),            # flags

        }
    def __init__(self):
        gtk.Alignment.__init__(self)
        self.hbox = gtk.HBox()
        self.days = gtk.Entry()
        self.hours = gtk.Entry()
        self.minutes = gtk.Entry()
        self.seconds = gtk.Entry()
        
        self._align = gtk.Alignment(0,0,0,0)

        self.add(self.hbox)
        for name in ('days', 'hours', 'minutes', 'seconds'):
            widget = getattr(self, name)
            widget.set_property('width_chars', 3)
            self.hbox.add(widget)

        self.show_all()
        
        self.connect('realize', self.set_packing)

    def set_packing(self, other):
        parent = self.get_parent()
        props = [prop.name for prop in parent.list_child_properties()]
        if 'y-options' in props:
            parent.child_set_property(self, 'y-options', 0)

    def split_interval(self, interval):
        if interval is None:
            return [''] * 4
        days = interval.days
        hours, spare = divmod(interval.seconds, 3600)
        minutes, seconds = divmod(spare, 60)
        return days, hours, minutes, seconds
        
    def do_set_property(self, property, value):
        if property.name == 'interval':
            days, hours, minutes, seconds = self.split_interval(value)
            self.days.set_text(str(days) or '')
            self.hours.set_text(str(hours))
            self.minutes.set_text(str(minutes))
            self.seconds.set_text(str(seconds))
            
    def do_get_property(self, property):
        if property.name == 'interval':
            
            days = self.days.get_text() or 0
            hours = self.hours.get_text() or 0
            minutes = self.minutes.get_text() or 0 
            seconds = self.seconds.get_text() or 0
            
            value = timedelta(days=int(days), hours=int(hours),
                                      minutes=int(minutes), seconds=int(seconds))
            return value
            
