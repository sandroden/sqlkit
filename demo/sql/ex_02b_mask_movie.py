"""base/different layout

a different layout with ReadOnly widgets and an example of == syntax that
prevents generation of the label: in this case the label is created
separately to force a different layout.
"""

lay = """
    ro=title
    date_release
    ro=director_id
    L=description
    TXS==description -
    """
from sqlkit.fields import VarcharField

t = SqlMask('movie', dbproxy=db, layout=lay)
t.reload()
