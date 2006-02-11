#!/bin/env python

from sqlalchemy import *

from SqlTreeView import *

eng = create_engine('postgres', 
                    {'database':'test', 
                     'user':'test', 
                     })


eng.begin()

users = Table('users', eng,
              Column('user_id', Integer, primary_key = True),
              Column('user_name', String(30), nullable = False),
              Column('user_last_name', String(30), nullable = False))

users.create()

users.insert().execute(
    {'user_id': 1, 'user_name': 'Sam', 'user_last_name': 'Patts'},
    {'user_id': 2, 'user_name': 'Sid', 'user_last_name': 'Watts'},
    {'user_id': 3, 'user_name': 'Axe', 'user_last_name': 'Smith'},
    {'user_id': 4, 'user_name': 'Ted', 'user_last_name': 'Will'})

mails = Table('mails', eng,
              Column('mail_address', String(30), nullable = True,
                     primary_key = True),
              Column('mail_user_id', Integer, ForeignKey("users.user_id")))

mails.create()

mails.insert().execute(
    {'mail_address': 'sam@example.com', 'mail_user_id': 1},
    {'mail_address': 'sid@example.com', 'mail_user_id': 2},
    {'mail_address': 'ted@example.com', 'mail_user_id': 4})
                       


res = join(users, mails).select().execute()

for r in res.fetchall():
    print r
    
class MappedTable(object):
    pass

j = join(users,mails)
#MappedTable.mapper = mapper(MappedTable, j)
assign_mapper(MappedTable, j)

m = MappedTable.mapper



for i in m.select():
    print i.user_id
    #i.user_id = i.user_id + 10

# aggiungo una riga
mT = MappedTable()
mT.user_id = 5
mT.user_name = 'Fat'
mT.user_last_name = 'Joe'
mT.mail_address = 'fjoe@example.com'
mT.mail_user_id = mT.user_id

mT2 = MappedTable()
mT2.user_id = 6
mT2.user_name = 'Jim'
mT2.user_last_name = 'Big'
mT2.mail_address = 'jbig@example.com'
mT2.mail_user_id = mT2.user_id

objectstore.commit()

class User(object):
    pass

class Mail(object):
    pass


assign_mapper(User, users,
              properties = {'emails': relation(Mail, mails)})


#pg_typed = pg2_colspec

    
import gtk
import gtk.glade


def delete_event(widget, event, data=None):
    gtk.main_quit()
    return False

def exit_now(widget, sqlt):
    sqlt.delete_event(widget, None)
    delete_event(widget, None)
    
def main():
    gtk.main()
    

class Scheck(SqlChecker):
    """Sample checker class checking a primary key."""
    
    def rowInsertCheck(self, data):
        """Check if new value in first column is already in liststore."""

        pkeys = [x[0] for x in self.sqltreeview.dbrows]
        if int(data[0]) in pkeys:
            raise RowInsertError('Primary key not unique! Discarding data', data, 0)

    def rowUpdateCheck(self, old_data, data):
        """Check if new value in first column is already in liststore."""
        
        pkeys = [x[0] for x in self.sqltreeview.dbrows]
        if int(data[0]) in pkeys and int(old_data[0])!=int(data[0]):
            raise RowUpdateError('Primary key not unique! Discarding data', data, 0)
        
# create a simple window
xmlg = gtk.glade.XML('glade-example/glade-example.glade')
window = xmlg.get_widget('window1')
window.set_title("ListStorage TreeView")
#window.set_size_request(500, 200)
window.connect("delete_event", delete_event)
accel_group = gtk.AccelGroup()

window.add_accel_group(accel_group)
#get a treeview obj
tv = xmlg.get_widget('tv')
#
#
# create obj passing the mapper
#
# Mapped class must be patched with assign_mapper function see above!

sqlt = SqlTreeView(tv, User)


insert_button = xmlg.get_widget('insert')
insert_button.connect("pressed", sqlt.insertRow)
delete_button = xmlg.get_widget('delete')
delete_button.connect("pressed", sqlt.deleteRow)
exit_button = xmlg.get_widget('exit')
exit_button.connect("pressed", exit_now, sqlt)

window.show_all()
eng.echo='debug'
main()




for i in m.select():
    for c in m.columns.keys():
        print c, i.__getattribute__(c),
    print

for i in User.select():
    for c in User.c.keys():
        print c, i.__getattribute__(c),
    print
    
eng.rollback()
