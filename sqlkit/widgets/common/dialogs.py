# Copyright (C) 2009-2010, Sandro Dentella <sandro@e-den.it>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re

from gi.repository import Gtk
from gi.repository import GdkPixbuf

from sqlkit import _

class SaveDialog(object):

    FILTER_FILES = (
        (_('All files'), '*.*'),
    )
    ACTION = Gtk.FileChooserAction.SAVE
    ACTION_BUTTON = Gtk.STOCK_SAVE

    def __init__(self,  title="Save dialog", default_filename='export.csv', run=True):
        """
        A dialog to export data into a csv file

        :param default_filename: the default
        """

        self.dialog = Gtk.FileChooserDialog(title,
                                            None,
                                            self.ACTION,
                                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                             self.ACTION_BUTTON, Gtk.ResponseType.OK))
        self.dialog.set_default_response(Gtk.ResponseType.OK)
        if self.ACTION in (Gtk.FileChooserAction.SAVE, Gtk.FileChooserAction.SAVE):
            self.dialog.set_current_name(default_filename)
        self.filename = None

        self.add_filters()
        self.customize()
        if run:
            self.run()

    def run(self):
        self.dialog.set_current_folder(self.current_folder())
        ret = self.dialog.run()
        if ret == Gtk.ResponseType.OK:
            self.write()
        self.dialog.destroy()

    def customize(self):
        pass

    def add_filters(self):

        for name, pattern in self.FILTER_FILES:
            file_filter = Gtk.FileFilter()
            file_filter.set_name(name)
            file_filter.add_pattern(pattern)
            self.dialog.add_filter(file_filter)

    def current_folder(self):

        import platform
        import os

        CURRENT_FOLDER = ''
        if 'HOME' in os.environ:
            CURRENT_FOLDER = os.environ['HOME']
        elif platform.system() == "Windows":
            CURRENT_FOLDER = os.path.join(os.environ['USERPROFILE'], 'Desktop')

        return CURRENT_FOLDER

    def write(self):
        self.filename = self.dialog.get_filename()
        return

class OpenDialog(SaveDialog):

    ACTION = Gtk.FileChooserAction.OPEN
    ACTION_BUTTON = Gtk.STOCK_OPEN
    FILTER_FILES = (
        (_('All files'), '*.*'),
    )

    def add_filters(self):
        SaveDialog.add_filters(self)
        image_filter = Gtk.FileFilter()
        image_filter.set_name(_('Images'))
        image_filter.add_pixbuf_formats()
        self.dialog.add_filter(image_filter)
        self.dialog.set_filter(image_filter)

        file_filter = Gtk.FileFilter()
        file_filter.set_name(_('Documents'))
        for ext in ('odt', 'ods', 'odp', 'ott', 'ots', 'doc', 'dot',
                    'xls', 'xlsx', 'ppt', 'pps'):
            file_filter.add_pattern("*." + ext)
        self.dialog.add_filter(file_filter)

    def customize(self):

        preview = Gtk.Image()
        preview.show()
        self.dialog.set_preview_widget(preview)
        self.dialog.connect("update-preview", self.update_preview_cb, preview)

        tbl = Gtk.Grid()
        self.entry = Gtk.Entry()
        # TIP: possible new name for an uploaded file
        label = Gtk.Label(label=_('Preferred new filename:') + "  ")
        label.set_tooltip_text(_('If not empty, the file will be uploaded with this new name'))
        # Gtk.Grid.attach(child, left, top, width, height): label at (0,0), entry at (1,0)
        tbl.attach(label, 0, 0, 1, 1)
        tbl.attach(self.entry, 1, 0, 1, 1)
        tbl.show_all()
        self.dialog.set_extra_widget(tbl)

    def update_preview_cb(self, file_chooser, preview):
        filename = file_chooser.get_preview_filename()
        if not filename:
            file_chooser.set_preview_widget_active(False)
            return
        ext = os.path.splitext(filename)[1]

        ## openoffice previewer
        if filename and re.match(r'\.(odt|odp|ods|odg|ots|ott)', ext):
            return self.openoffice_preview(filename, file_chooser, preview)

        ##  image previewer
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, 128, 128)
            preview.set_from_pixbuf(pixbuf)
            have_preview = True
        except Exception as e:
            have_preview = False
        file_chooser.set_preview_widget_active(have_preview)
        return

    def openoffice_preview(self, filename, file_chooser, preview):

        import zipfile
        import tempfile

        oozip = zipfile.ZipFile(filename, 'r')
        thumb = oozip.read('Thumbnails/thumbnail.png')
        fh, fname = tempfile.mkstemp(suffix='.png', prefix='thumb-')
        ## thumb is bytes: wrap the fd returned by mkstemp in binary mode so we
        ## neither open a second file descriptor nor try to write bytes to a
        ## text-mode stream (which raised TypeError under Py3).
        with os.fdopen(fh, 'wb') as f:
            f.write(thumb)
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(fname)
            preview.set_from_pixbuf(pixbuf)
            file_chooser.set_preview_widget_active(True)
        finally:
            os.remove(fname)

    def write(self):
        self.filename = self.dialog.get_filename()
        self.new_filename = self.entry.get_text()
