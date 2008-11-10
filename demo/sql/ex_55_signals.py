"""signals/record_selected

'record_selected' is define both fr SqlTable and SqlMask

"""


t = SqlTable(Class=model.Director, dbproxy=db, )
t2 = SqlTable(Class=model.Movie, dbproxy=db,  )

def show_movies(widget):
    if widget.current:
        t2.set_records(widget.current.movies)
    
t.connect('record_selected', show_movies)
          
t.reload()

