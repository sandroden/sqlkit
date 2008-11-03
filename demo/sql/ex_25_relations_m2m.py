"""relation/m2m 

To add a relation is as easy as adding the relation name to the layout
note that in this case the table name is not sufficient, we need to know
the mapping so we pass a Class attribute that is realy a class build with
declarative layer
"""

lay = """
         title       year
         director_id - - -
         m2m=genres -  m2m=actors -
         """
t = SqlMask(Class=model.Movie, dbproxy=db , layout=lay)


