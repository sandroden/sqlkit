"""printing/related

You can also loop on related rows


"""

def prepare_context(printtool, context, template_name, sqlwidget):
    """
    inject the director's movies as table objects
    """
    context['Table1'] = (sqlwidget.related.movies.records,)


lay = """
  first_name last_name
  nation
  o2m=movies - - -

"""

t = SqlMask(model.Director, layout=lay, dbproxy=db)
t.printing.add_menu_entry('Print to pdf', 'appy/director-movies.odt', mode='pdf')
t.printing.add_menu_entry('Print to odt', 'appy/director-movies.odt', mode='odt')
t.printing.connect('context-ready', prepare_context)
t.reload()
