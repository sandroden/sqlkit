"""
.. _image_widget:

Image Viewer
============

.. autoclass:: ImageWidget
   :members: 

Properties
----------

imageViewer has the following properties:

:image: the image path currently rendered
:scale: possible values AUTOREDUCTION, SCALE. If True the image should autoscale. If value
    is AUTOREDUCTION the image is never enlarged over its natural size
:width: the with of the Gtk.Image widget
:height: the height og the Gtk.Image widget
:scale_factor: the current scale factor between render image and thumbnail

Signals
-------

ImageViewer has the following signals:

:image-selected: The image has been selected for upload. Callback:

   .. function:: on_image_selected(widget, filename, new_filename):

      :param widget: the widget that issued the signal
      :param fielname: the filename that has been selected
      :param new_filename: a preferred filename as suggested by the user if any
     
:image-displayed: The image has been displayed

   .. function:: on_image_displayed(widget, pixbuf_full, pixbuf):

      :param widget: the widget that issued the signal
      :param pixbuf_full: the pixbuf rendered from the file
      :param pixbuf: the scaled pixbuf

:image-deleted: the image has been deleted

   .. function:: on_image_deleted(widget, filename):

      :param widget: the widget that issued the signal
      :param fielname: the filename that has been deleted


"""
import re
import os

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import GdkPixbuf
import weakref

from sqlkit import _

IMAGE_MENU = '''
<popup name="ImagePopup">
    <menuitem action="UploadImage" />
    <menuitem action="DeleteImage" />
    <menuitem action="DetachImage" />
    <menuitem action="SaveImage" />
    <menuitem action="Zoom-in" />
    <menuitem action="Zoom-out" />
    <menuitem action="ShowName" />    
</popup>
'''

IMAGE_FORMATS = ["." + x.get_name() for x in GdkPixbuf.Pixbuf.get_formats()] + ['.jpg']

class ImageWidget(Gtk.VBox):

    """
    Image Widget suitable for basic image viewing. Inherits from VBox
    """

    __gtype_name__ = 'ImageWidget'

    __gproperties__ = {
        'image-path': (GObject.TYPE_PYOBJECT,                      # type
                       'Image',                                   # nick name
                       'The Image currently rendered',            # description
                       GObject.PARAM_READWRITE),                  # flags

        'scale': (GObject.TYPE_STRING,                        # type
                  'Autoscale',                               # nick name
                  'True if the image should autoscale',      # description
                  'AUTOREDUCTION',                           # default value
                  GObject.PARAM_READWRITE),                  # flags

        'width': (GObject.TYPE_INT,                           # type
                  'width',                                   # nick name
                  'The width of the image area',             # description
                  1, 10000, 250,
                  GObject.PARAM_READWRITE),                  # flags

        'height': (GObject.TYPE_INT,                          # type
                   'height',                                  # nick name
                   'The height of the image area',            # description
                   1, 10000, 250,
                   GObject.PARAM_READWRITE),                  # flags

        'scale-factor': (GObject.TYPE_FLOAT,                           # type
                         'scale-factor',                                   # nick name
                         'The scale factor for the pixbuf ',             # description
                         0, 1000, 1,
                         GObject.PARAM_READABLE),                  # flags
        'show-name': (GObject.TYPE_BOOLEAN,                           # type
                      'show-name',                                   # nick name
                      'The scale factor for the pixbuf ',             # description
                      False,
                      GObject.PARAM_READWRITE),                  # flags

        'strip-dir': (GObject.TYPE_STRING,                           # type
                      'strip-dir',                                   # nick name
                      'A dir name to strip from image name when writing in status bar ',
                      '',
                      GObject.PARAM_READWRITE),                  # flags

    }

    __gsignals__ = {
        'image-selected': (GObject.SignalFlags.RUN_LAST, None,
                           (GObject.TYPE_STRING, GObject.TYPE_STRING),
                           ),
        'image-displayed': (GObject.SignalFlags.RUN_LAST, None,
                            (GObject.TYPE_STRING,  GObject.TYPE_PYOBJECT,
                             GObject.TYPE_PYOBJECT),
                            ),
        'image-deleted': (GObject.SignalFlags.RUN_LAST, None,
                          (GObject.TYPE_STRING,))
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        event = Gtk.EventBox()
        self.status_bar = Gtk.Statusbar()
        self._image = Gtk.Image()
        self._image.set_tooltip_text(_("Right click on the image area\n to upload an image"))
        self.add(event)
        event.add(self._image)
        self.props.scale = 'AUTOREDUCTION'
        self._image.set_size_request(self.props.width, self.props.height)
        event.connect('button-press-event', self.button_press_event_cb, self._image)
        self.prepare_actions()
        self.show_all()
        self.add(self.status_bar)

    def set_image(self, image_path):
        """
        set rendered image

        :param image_path: the path of the image
        """
        self.sb(image_path)
        if not image_path:
            pixbuf = None
            pixbuf_full = None
        else:
            ext = os.path.splitext(image_path)[1]
            if not ext.lower() in IMAGE_FORMATS:
                self._image.set_property('stock', Gtk.STOCK_FILE)
                self.scale_factor = 1
                self.image_path = image_path
                self.emit('image-displayed', image_path, None, None)
                return
            else:
                if not os.path.exists(image_path):
                    self._image.set_property('stock', Gtk.STOCK_MISSING_IMAGE)
                    self.image_path = image_path
                    return
                pixbuf_full = GdkPixbuf.Pixbuf.new_from_file(image_path)

                if self.props.scale in ('AUTOREDUCTION', 'AUTOSCALE'):
                    pixbuf, scale = self.scale_pixbuf(pixbuf_full, w=self.props.width,
                                                      h=self.props.height)
                else:
                    self.scale_factor = 1

        self.image_path = image_path
        self._image.set_from_pixbuf(pixbuf)
        self.emit('image-displayed', image_path, pixbuf_full, pixbuf)

    def scale_pixbuf(self, pixbuf, w=None, h=None):
        """
        scale pixbuf image with the same ratio so that it fits into self.w/self.h

        :param pixbuf: a GdkPixbuf.Pixbuf object
        :param w: the desired width
        :param h: the desired height
        """
        pw, ph = pixbuf.get_width(), pixbuf.get_height()
        w, h = w or self.get_property('width'), h or self.get_property('height')
        ratio = min(w/float(pw), h/float(ph))
        if ratio >= 1 and self.props.scale == 'AUTOREDUCTION':
            self.scale_factor = 1
            return pixbuf, 1
        self.scale_factor = ratio
        return pixbuf.scale_simple(int(pw*ratio), int(ph*ratio), GdkPixbuf.InterpType.BILINEAR), ratio

    def set_pixbuf(self, pixbuf):
        """
        Set the image via the pixbuf

        :param pixbuf: the GdkPixbuf.Pixbuf
        """

        self._image.set_from_pixbuf(pixbuf)

    def set_stock(self, stock_id, size=Gtk.IconSize.DIALOG):
        """
        Set the image via the stock-id

        :param stock-id: a stock-id
        :param size: the desired image (default: ICON_SIZE_DIALOG)
        """

        self._image.set_from_stock(stock_id, size)

    def do_set_property(self, property, value):

        if property.name == 'width':
            self.width = value
            self._image.set_size_request(value, self.props.height)
        elif property.name == 'height':
            self.height = value
            self._image.set_size_request(self.props.width, value)
        elif property.name == 'scale':
            self.scale = value
        elif property.name == 'image-path':
            self.set_image(value)
            self.image_path = value
        elif property.name == 'show-name':
            self.status_bar.pros.visibile = value
        elif property.name == 'strip-dir':
            self.status_bar.strip_dir = value
        else:
            raise AttributeError('unknown property %s' % property.name)

    def do_get_property(self, property):

        if property.name == 'width':
            return self.width if hasattr(self, "width") else 250
        elif property.name == 'height':
            return self.height if hasattr(self, "height") else 250
        elif property.name == 'scale':
            return self.scale
        elif property.name == 'image-path':
            return self.image_path
        elif property.name == 'scale-factor':
            return self.scale_factor
        elif property.name == 'show-name':
            return self.status_bar.props.visible
        elif property.name == 'strip-dir':
            return self.status_bar.strip_dir or ''
        else:
            raise AttributeError('unknown property %s' % property.name)

    def button_press_event_cb(self, eventbox, event, image):

        if event.button == 3:
            self.popup_menu(event)

    def prepare_actions(self):

        self.ui_manager = Gtk.UIManager()

        self.actiongroup = Gtk.ActionGroup(name='Image')
        self.actiongroup.add_actions([
            ('UploadImage', None, _('Upload image'), None,
             _('Upload or modify an image'), self.upload_image),
            ('DeleteImage', None, _('Delete image'), None,
             _('Delete the image'), self.delete_image),
            ('DetachImage', None, _('Image viewer'), None,
             _('Open separate image viewer'), self.show_image),
            ('SaveImage', None, _('Save image as'), None, _('Save image as'), self.save_image),
            ('Zoom-in', Gtk.STOCK_ZOOM_IN, None, None, None, self.zoom_in),
            ('Zoom-out', Gtk.STOCK_ZOOM_OUT, None, None, None, self.zoom_out),
            ('ShowName', None, _("Show/Hide image name"), None, None, self.toggle_status_bar),
        ],)
        self.ui_manager.insert_action_group(self.actiongroup, 10)
        self.ui_manager.add_ui_from_string(IMAGE_MENU)

    def show_image(self, action=None):
        """
        Open another window that will show the same image with at a
        different zooming. Setup callback to keep the new window updated by
        the first one.
        """

        w = Gtk.Window()
        image2 = ImageWidget()
        w.add(image2)
        image2.props.width = 700
        image2.props.height = 700
        w.show_all()
        #self.imgref = weakref.ref(image2)
        #self.winref= weakref.ref(w)

        def update_image(widget, image_path, pixbuf_full, pixbuf):
            image2.set_pixbuf(pixbuf_full)
            image2.sb(image_path)

        self.connect('image-displayed', update_image)
        image2.props.strip_dir = self.props.strip_dir
        image2.set_image(self.props.image_path)

    def popup_menu(self, event):

        menu = self.ui_manager.get_widget('/ImagePopup')
        menu.popup(None, None, None, None, event.button, event.time)

    def upload_image(self, action):

        from sqlkit.widgets.common import dialogs

        dialog = dialogs.OpenDialog(title=_('upload image'), default_filename='')
        filename = dialog.filename
        if not filename:
            return
        self.set_image(str(filename))
        self.emit('image-selected', filename, str(dialog.new_filename or ''))

    def save_image(self, action):

        import shutil
        from sqlkit.widgets.common import dialogs

        orig_filename = self.props.image_path
        if not orig_filename:
            # TODO: should communicate that no file was found...
            return

        dialog = dialogs.SaveDialog(default_filename=os.path.basename(orig_filename))
        if dialog.filename:
            shutil.copyfile(orig_filename, dialog.filename)

    def delete_image(self, action):
        self.emit('image-deleted', self.props.image_path)
        self.set_image(None)

    def zoom_in(self, action):
        w, h = self.props.width, self.props.height
        self.props.width = int(w * 1.2)
        self.props.height = int(h * 1.2)
        self.set_image(self.props.image_path)

    def zoom_out(self, action):
        w, h = self.props.width, self.props.height
        self.props.width = int(w / 1.2)
        self.props.height = int(h / 1.2)
        self.set_image(self.props.image_path)

    def toggle_status_bar(self, action):

        self.status_bar.props.visible = not self.status_bar.props.visible

    def sb(self, txt):
        """
        Push info on Status Bar
        """
        if not isinstance(self.status_bar.get_toplevel(), Gtk.Window):
            return
        if not txt:
            txt = ''
        txt = re.sub("^%s" % self.props.strip_dir, '', txt)
        idx = self.status_bar.get_context_id(txt)
        msg_id = self.status_bar.push(idx, txt)

GObject.type_register(ImageWidget)


if __name__ == '__main__':

    w = Gtk.Window()
    i = ImageWidget()
    w.add(i)
    w.show_all()
#    i.set_image('cal15.png')
    i.set_image('/tmp/la-ragazza-sul-ponte2.jpg')

    def dbg(widget, filename):
        print(filename)
    i.connect('image-selected', dbg)
    Gtk.main()
