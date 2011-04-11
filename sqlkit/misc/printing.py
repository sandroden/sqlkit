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


"""
Sqlkit printing
--------------------
Each sqlwidget has a ``printing`` attribute that manages printer entries that is an instance
of ``PrintTool``.

A standard way should be as easy as just setting a directory where templates
should be found and adding menu entries via ``add_menu_entry``. The default
template dir is a subdir of the current directory named ``templates``.

Templates present in this directory -if named as the nick of the sqlwidget-
will be automatically added, but you will normally want to customize the context
or adding variable to it or adding formatting functions (e.g. to transform numbers
into monetary format), that can be easily done connecting to
:ref:`context-ready signal <psignals>`.

The default way of filling the context wraps each object into an :ref:`ObjectProxy <obj_proxy>`
that uses :ref:`fields` to present each value in a human readable format, that means also that
it tries hard to follow foreign keys and substitute values retrieved by :ref:`description`.


.. autoclass:: PrintTool
   :members: __init__, add_menu_entry, prepare_context, template_dir, server, port, output_dir,
             remote_output_dir, pdf_viewer, odt_viewer, add_to_table

.. autoclass:: ObjProxy
   :members: 


"""
import os
import re
import gtk
import urllib
import subprocess

import gobject

from sqlkit import _
from sqlkit.widgets.common import dialogs
from sqlkit.misc.utils import get_viewer

MENU_ENTRY = """
  <menubar name="Main">
     <menu action="File">
       <placeholder name="Print-ph">
         <menu action="Print">
           <menuitem action="%s"/>
         </menu>
       </placeholder>
     </menu>
  </menubar>
"""

class PrintAbortException(Exception): pass
class DownloadException(Exception): pass

class PrintTool(gobject.GObject):
    """
    a print obj that is able to create a default context to handle to
    oootemplate 
    """

    template_dir = None
    """The directory where templates are searched for. Default is cwd/templates.
       It's a path significant for the openoffice server
    """
    server = '127.0.0.1'
    """the openoffice server to connect to for printing"""

    port = 8100
    """the port to use to connect to the server"""

    output_dir = None
    """the output dir when server is remote as viewed from client (may be an URL)"""
    
    remote_output_dir = None
    """the output dir when server is remote as viewed from server (a local file for the server)"""
    
    pdf_viewer = get_viewer('pdf')
    """the preferred viewer for pdf files"""

    odt_viewer = get_viewer('odt')
    """the preferred viewer for openoffice templates"""

    server_dir_separator = '/'
    """The server dir separator / (default) or \\: determines how the remote path is built for
    templates and output files. Only used if server is remote (not 127.0.0.1 nor localhost)"""
    
    proxies = {}
    """the proxies passed to urllib.FancyURLopener (see urllib module documentation)"""
    
    __gsignals__ = {
        'context-ready' : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_BOOLEAN,
                           # context, template_name, sqlwidget, 
                           (gobject.TYPE_PYOBJECT , gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT ),
                           ),
        }

    def __init__(self, master):
        """
        Initializes the printing tool setting a default template dir and checks for
        availability of module 'uno' from openoffice. If uno is missing the printing
        capabilities are made invisible.

        If templates are found with the name ``nick.odt``  where the nick is the nick of
        the sqlwidget, entries are automatically added. This way you can generate templates
        and use them w/o even the need for a single line of code (unless you need to
        customize the context, of course)
        
        :param master: the table or mask instance of which this is a printing tool
        """
        gobject.GObject.__init__(self)
        self.master = master
        self.template_dir = self.template_dir or os.path.abspath(os.path.join(os.curdir, 'templates'))
        try:
            import uno
            self.disabled = False
        except ImportError:
            self.master.sb(_('Disabling printing for lack of "uno" module'), seconds=20)
            self.disabled = True
            self.hide()

        self.look_for_automatic_templates()
        
    def hide(self):
        self.master.actiongroup_print.set_visible(False)
        
    def show(self):
        self.master.actiongroup_print.set_visible(True)
        self.master.actiongroup_print.set_sensitive(True)
        
    def add_menu_entry(self, description, template_name, server=None, port=None, mode='pdf',
                       output_name=None, accel=None, tip=None, action_name=None):
        """
        Add menu entry with 'description' using 'template'
        Both are fake printers in the sense that are 'printer to file'

        :param description: the description that will appear in the menu entry
        :param template_name: the template name to be used
        :param mode: the mode of the printer: pdf or odt
        :param output_name: the output name. Can be a callable that
              will receive ``template_name`` as parameter. If ``self.output_dir`` is defined
              ``output_name`` will be joined with ``self.ouput_dir`` to retrieve it from the client
        :param accel: accelerator to be used with this
        :param tip: tip for the entry
        :param action_name: action name (defaults to templ\_ + template_name)
        
        """
        assert template_name is not None, "Template name must be defined"
        output_name = output_name or "%s.%s" % ((os.path.splitext(os.path.split(template_name)[1])[0]), mode)

        if not self.disabled:
            self.show()
        dir_name, template_name, template_path = self.split_template_name(template_name)
        if not action_name:
            action_name = 'templ_%s_%s' % (template_name, mode)
        path = '/Main/File/Print-ph/Print/%s' % action_name
        action = self.master.ui_manager.get_action(path)
        if not action:
            self.master.actiongroup_print.add_actions([
                (action_name, None, description, accel, tip, self.use_template,),
                ], (template_path, mode, server, port, output_name))

            self.master.ui_manager.add_ui_from_string(MENU_ENTRY % action_name)

    def split_template_name(self, template_name):
        """
        return a tuple (dir, template_name, template_path)
        if templatename does not contain a path, self.template_dir is used if that leads
        to an existent filename, otherwise it'd be set no None

        :param template_name: a template name possibly with a complete path
        """

        template_path = template_name
        dirname, template_name = os.path.split(template_name)
        if not dirname:
            dirname = self.template_dir
            template_path = os.path.join(dirname, template_name)
            if not os.path.exists(template_path):
                dirname = None

        return dirname, template_name, template_path

        
    def use_template(self, menuItem, template_path, mode, server, port, output_path):
        """
        create a context from master and call template

        :param menuItem:   the entry that was clicked
        :param tempate_name: the template_path to be used on the server
        :param mode:  currently ``pdf`` or ``odt``
        :param server: the name or ip of the openoffice server
        :param port:  the port on which the server runs
        :param output_path: the output name. It can be a callable that will receive 2 args:

                * this PrintTool instance
                * the template_path
        
        """
        import oootemplate as oo

        server = server or self.server 
        port = port or self.port 
        
        ## Context
        context = oo.Context({})
        if self.master.is_mask():
            context['obj'] = ObjProxy(self.master.current, self.master)
        else:
            self.add_to_table(context, 'Table1', self.master.records)

        for rel in self.master.related.keys():
            self.add_to_table(context, rel, self.master.related[rel].records,
                              master=self.master.related[rel])

        self.emit('context-ready', context, os.path.split(template_path)[1], self.master)

        ## Template & output
        templ = oo.Template(unicode(template_path), server=server, port=port)
        missing_keys = templ.render(self.prepare_context(context))
        if missing_keys:
            self.debug_missing(missing_keys, templ, context)

        ## Output
        # when the server is remote, the output file is created remotely (remote_output_path)
        # downloaded  and saved (local_output_path) via http, and opened locally

        if callable(output_path):
            output_path = output_path(self, template_path)


        remote_output_path = self.get_remote_output_path(output_path, server)
        local_output_path = self.get_local_output_path(template_path, mode, output_path)

        if not local_output_path:
            return

        if server in ('localhost', '127.0.0.1'):
            if local_output_path == template_path:
                self.master.message(_("Template name (%s) cannot be same as output_path (%s)") % (
                    template_path, output_path), type='ok')
                return
            remote_output_path = local_output_path

        templ.save_as(remote_output_path)
        templ.close()

        ## Show Result
        self.show_result(remote_output_path, local_output_path)

    def get_remote_output_path(self, output_path, server):
        """
        return the name the remote server must use to save the file
        """
        
        if self.remote_output_dir and not server in  ('localhost', '127.0.0.1'):
            return "%s%s%s" % (self.remote_output_dir, self.server_dir_separator, output_path)
        return output_path

    def show_result(self, remote_output_path, local_output_path):
        """
        Open the resulting file with the best possible viewer/editor
        """
        ## NOTE: please read the note in function get_viewer to understand why I don't
        ## use 'start' under windows for remote viewing.

        if self.output_dir and  re.search('http://', self.output_dir):
            remote_path = "%s/%s" % (self.output_dir, os.path.split(remote_output_path)[1])
            opener = Opener(self.proxies)
            try:
                opener.retrieve(remote_path, local_output_path)
            except DownloadException, e:
                self.master.dialog(text=str(e), type="ok")
                return

        if not os.path.exists(local_output_path):
            self.master.dialog(text="Manca il file '%s'" % local_output_path, type="ok")
            return

        self.open_local_file(local_output_path)

    def debug_missing(self, missing_keys, template, context):
        """
        Communicate that some keys are missing

        :param missing_keys: the dict of missing keys
        :param template: the oootemplate.Template
        :param context: the oootemplate.Context
        """
        msg = _("The following variable are missing in the context")
        # default table name has not been changed and is not present in the .odt file
        # chances are that a localized .odt file names table in a localized way...
        if 'Table1' in context and not 'Table1' in template.tables:
            msg += _("\nA possible error is that I don't see 'Table1' in your template\n" \
                   + "but I see %s" % " ".join(template.tables))
        for key, where in missing_keys.iteritems():
            if where:
                msg += "\n'%s' (%s)" % (key, where or '')
            else:
                msg += "\n'%s'" % key
        self.master.dialog(text=msg, type='ok')

    def prepare_context(self, context):
        """
        This function is meant to be overridden by a customized one

        :param context: the automatically prepared ``oootemplate.Context``.
               It contains 2 keys:

               * 'obj': the current object for mask and normally *None* for tables
                     (unless an object was edited, in which case it will pooint to that object)
               * 'Table1' : the list of record currently loaded in this sqlwidget
        
        You can add any keys but remember to use the correct syntax for tables (a dict
        with lists as <values).

        This is normally used to set totals or arrange so that related table's record
        are used in Tables. Read example 76.

        """
        return context

    def add_to_table(self, context, table_name, obj_list, master=None, reset=True, format=None):
        """
        Add to an openoffice table a list of objects wrapped in ObjProxy

        :param context: the context to be manipulated
        :param table_name: the table_name where objects list must be added
        :param master: the master where to retrieve fields
        :param obj_list: the list of objects to be added
        :param reset: boolean. If True the list becomes the only list, otherwise it's added.
                      Defaults to True
        """
        
        new_list = [ObjProxy(o, master or self.master) for o in obj_list]
        if reset:
            context[table_name] = [new_list]
        else:
            context[table_name] += [new_list]
        
    def get_local_output_path(self, template_path, mode, output_name):
        """
        return the name of the output file on the local machine
        """

        if output_name:
            dir_name, file_name = os.path.split(output_name)
        else:
            dir_name, file_name = os.path.split(template_path)

        base, ext = os.path.splitext(file_name)
        default_filename = "%s.%s" % (output_name and base or base+'-output', mode)

        dialog = PrintDialog(title=_('Print to file'), default_filename=default_filename)

        filename = dialog.filename
        if filename and  not filename.endswith('.%s' % mode):
            filename = '%s.%s' % (filename, mode)
        return filename
        
    def look_for_automatic_templates(self):
        """
        Look if some templates are available and add entries for them
        """

        if not os.path.exists(self.template_dir):
            return
        for f in os.listdir(self.template_dir):
            if f == "%s.odt" % self.master.nick:
                self.add_menu_entry("Print to pdf file", f, mode='pdf', action_name=self.master.nick)
                self.add_menu_entry("Print to odt file", f, mode='odt', action_name=self.master.nick +'pdf')
                
    def open_local_file(self, filename):
        """
        Open file filename with the default application

        :param filename: the name of the file to be opened
        """
        if os.name in ('posix', 'mac'):
            if filename.endswith('pdf'):
                p =  subprocess.call((self.pdf_viewer, filename)) 
            else:
                p =  subprocess.call((self.odt_viewer, filename))
        else:
            # I made some test with call(('start', filename)) but in several
            # occasion I coudn't get the start command to find the
            # file. os.startfile() doesn't suffer the same problem.
            os.startfile(filename)
                                
class PrintDialog(dialogs.SaveDialog):

    FILTER_FILES = (
        ( _('Pdf files'), '*.pdf'),
        ( _('Odt files'), '*.odt'),
        ( _('All files'), '*.*'),
        )


class ObjProxy(object):
    """
    .. _obj_proxy:
    
    A proxy that knows how to retrieve the field.human_value of attributes
    """
    def __init__(self, obj, master=None):
        if master:
            self.gui_fields = master.gui_fields
        else:
            self.gui_fields = setup_field_validation(obj)

        self.obj = obj
        
    def __getattr__(self, key):

        value = getattr(self.obj, key)
        if key in self.gui_fields:
            return self.gui_fields[key].get_human_value(value)
        else:
            # at present LoaderProperties don't have a gui_field
            return value


class Opener(urllib.FancyURLopener):
    
    def http_error_default(self, filename, sock, status, message, response):
        msg = "Error while retrieving file %s.\nStatus code: %s (%s)" % (filename, status, message)
        raise DownloadException(msg)


def setup_field_validation(obj):
    """
    Create ``sqlkit.fields.Field`` object: one for each handled field
    """
    
    from sqlkit.fields import FieldChooser
    from sqlkit.db.minspect import InspectMapper
    from sqlalchemy import orm
    
    mapper = orm.class_mapper(obj.__class__)

    gui_fields = {}
    info = InspectMapper(mapper)
    field_chooser = FieldChooser(info)

    for field_name in mapper.c.keys():
        Field = field_chooser.get_field(field_name, info.fields[field_name])
        field = Field(field_name, info.fields[field_name])
        gui_fields[field_name] = field

    return gui_fields
        


