"""printing/preparing Context

You can customize the context you pass to the PrintTool either by subclassing
and overriding prepare_context or by connecting to the 'context-ready' signal
"""

from sqlkit.misc.printing import PrintTool

class MyPrinter(PrintTool):

    def prepare_context(self, context):
        """
        substitute director's films as table objects
        """
        context.translate['d'] = 'director'
        context.translate['nation'] = 'director.nation'
        return context


t = SqlTable(model.Movie, dbproxy=db, printing_style='ooo')
t.printing = MyPrinter(t)
t.printing.add_menu_entry('Print to pdf', 'oootemplate/movies-translate.odt', mode='pdf',
                          accel="<alt>p",
                          tip="Generate a pdf file with these movies")
t.printing.add_menu_entry('Print to odt', 'oootemplate/movies-translate.odt', mode='odt',
                          tip="Generate an odt file with these movies")
t.reload()
