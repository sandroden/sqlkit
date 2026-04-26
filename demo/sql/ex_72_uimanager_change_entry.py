"""uimanager/substituting an action (entry)

You can substitute an entry using standard GTK. I add the example here just because it may
not be obvious if you're not an experienced GTK developer...

The idea is that you add a group of actions (ActionGroup) to the manager of the
User Interface (UIManager). If that is inserted *before* the others (position 0) it will
be picked up instead of the other.

You can click on 'File' and see that Export has been changed into "I'm not the original Export"
and you can right-click on the table and you will notice that "I'm not the other one" has appeared.

"""

from gi.repository import Gtk


def test(item):
    print("Here I am!")

t = SqlTable('movie',    dbproxy=db, order_by='title', )
t.actiongroup_mag = Gtk.ActionGroup(name='Demo')
t.actiongroup_mag.add_actions([
    ('MaskView', Gtk.STOCK_LEAVE_FULLSCREEN,  "I'm not the other one!", '<Control>m', None, test),
    ('Export', Gtk.STOCK_LEAVE_FULLSCREEN,  "I'm not the original Export!", None, None, test),
])
# a change in the main UIManager
t.ui_manager.insert_action_group(t.actiongroup_mag, 0)

# a change in the View UIManager
t.views['main'].ui_manager.insert_action_group(t.actiongroup_mag, 0)

t.reload()
