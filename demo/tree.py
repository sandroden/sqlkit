#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import sys, re, datetime
sys.path.append ('../../')
import dbg 
dbg.conf_class_trace(ok='SqlTable|Completion')

from sqlalchemy import *
import sqlkit as sk
import layout
import gtk
dbg.debug(True)
#dbg.debug(False)
import sqlalchemy
#import sqlalchemy.mods
#import sqlalchemy.mods.threadlocal
#from flogger import *

eng = sk.config.new_engine(globalconn=True)
meta = default_metadata
session = create_session()
dbg.write(session)
#eng = create_engine('postgres://test:vicie@localhost:5433/test')

#meta =  BoundMetaData(eng)

table='euro_user'
#table='euro_mail'
#table='jobs'
fields='user_id, user_name, user_last_name, user_sex, user_birth_date, user_age'
fields=None

lgm = dbg.ShowLogs(show=True)
lgm.conf(but='lookup_value|set_fkey_descr')
#lgm.log(sk.SqlTable)


class act(sk.sqlwidget.Actions):
    def key_entry_F1(self, wdg, event, field_name):
        if field_name == 'user_name':
            self.dialog, self.lay = self.master.lay_obj.dialog(
                lay="e=parola", 
                type='ok-apply-cancel')
            self.dialog.connect('response', self.response_cb, field_name)
            self.dialog.run()
            
        return False

    def response_cb(self, dialog, response_id, field_name):

        Entry = self.master.editable

        InTxt = Entry.get_text()
        txt = self.lay.widgets['e=parola'].get_text()

        dbg.write('txt: %s - inTxt: %s' % (txt, InTxt))
        
        if response_id == gtk.RESPONSE_APPLY:
            dbg.write('APPLY')
            Entry.set_text(txt)
            self.master.set_value(field_name, txt)

        if response_id == gtk.RESPONSE_OK:
            dbg.write('OK')
            self.master.set_value(field_name, txt)
            dialog.destroy()

        if response_id == gtk.RESPONSE_CANCEL:
            dbg.write('CANCEL', 'InTxt', InTxt)
            self.master.set_value(field_name, InTxt)
            dialog.destroy()
            

#     def set_entry_connect(self, entry, field_name):
#         entry.connect('key-press-event', self.ciao, field_name)
        
#     def on_completion(self, new, field_name):
#         if field_name == 'mail_user_id':
#             #SQL= "AND filo.f_titolo = :f_titolo AND filo.ft_id = :ft_id"
#             SQL = "AND mail_address ~ :mail_addr"
#             params = {'mail_addr' : '[2y]'}
#             return (SQL, params)

zz = sqlt = sk.SqlTable(table=table, session=session, #field_list=fields,
                        single=True, dev=True, nick='tree',
                        icons='b=gtk-new b=gtk-delete b=gtk-refresh',
                        order_by='user_name', actions=act())
#zz.actions = act(zz)
zz.print_template_dir = 'template_dir'

# , noup=['user_age']
#zz.w['Window'].set_geometry_hints(None, base_width=300, base_height=200)
zz.w['Window'].set_geometry_hints(None, min_width=400, min_height=600)

gtk.main()


