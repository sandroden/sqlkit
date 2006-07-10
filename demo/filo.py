#!/usr/bin/env python

import sys, re, datetime
import gtk

sys.path.append ('../../')
import dbg
import layout
dbg.debug(True)

from sqlalchemy import *
import sqlkit as sk
import layout

engine = sk.config.new_engine(file='eurotex.ini', echo=False, globalconn=True)
tables = ['art_var_filo', 'filo_art', 'filo_uso', 'filo_fibra', 'filo']
#tables = ['filo_art', 'filo_uso', 'filo_fibra']

t = {}
tbls = []
for tbl in tables:
    #print t
    t[tbl] = Table(tbl, engine, autoload=True)
    tbls.append(t[tbl])
    
#mapper = sk.parseopts.get_mapper(engine, None, tbls)

j = outerjoin(t['filo_art'], t['filo_uso'])
j2 = outerjoin(j, t['filo_fibra']) 
j3 = outerjoin(j2, t['art_var_filo'])
j4 = outerjoin(j3, t['filo'])

j = outerjoin( t['filo_art'] , t['art_var_filo'] )
#j = outerjoin(t['art_var_filo'], t['filo_art'] )
j2 = outerjoin(j, t['filo']) 
j3 = outerjoin(j2, t['filo_uso'])
j4 = outerjoin(j3, t['filo_fibra'],
            t['filo_fibra'].c.ff_id == t['filo_art'].c.ff_id)

class Join(object): pass
m = mapper(Join, j4,
           primary_key=[t['filo_art'].c.fa_id,
#                        t['art_var_filo'].c.fa_id,
                        ])

layout.map_labels("../../../eurotex/traduzioni.txt")

#fields1='fu_descr,ff_descr,fa_titolo,fa_colore,fa_numfili,fa_peso,fa_imborso,'
fields1='fu_descr,ff_id,fa_titolo,fa_colore,fa_numfili,fa_peso,fa_imborso,'
                 
fields2 = 'f_marca, f_tipo, f_torsione'
fields= fields1 + 'f_id,' + fields2


format = "%(f_marca)s %(f_tipo)s %(f_titolo)s/%(f_num_bave)s "

sk.completion.set_description_fields(
    'filo', 'f_marca', 'f_titolo, f_tipo, f_num_bave, f_torsione', format)

fields1='fu_descr,fa_titolo,fa_colore,fa_numfili,fa_peso,fa_imborso,'
noup = fields1 + fields2

class ActFilo(sk.sqlwidget.Actions):
    def on_update(self, new={}, old={}):
        dbg.write(new)
        dbg.write(old)
        t = self.master.engine.text(
            "INSERT INTO art_var_filo (f_id, fa_id) VALUES ( :f_id, :fa_id)")
        t.execute(fa_id=old['fa_id'], f_id=new['f_id'])
        
engine.echo=True
zz = sk.SqlTable(field_list=fields, mapper=m, single=True, geom=(650,250),
                 noup=noup, actions=ActFilo, nick='filo')
#zz = sk.SqlTable(table='art_var_filo', single=True)
zz.reload(sql=("""art_var_filo.avct_id = :avct_id OR (filo_art.a_id = :a_id AND art_var_filo.avct_id IS NULL)
""", {'avct_id':2, 'a_id' : 2}), reload_constraint=True)

zz.actions = ActFilo(zz)
engine.echo = True


gtk.main()


