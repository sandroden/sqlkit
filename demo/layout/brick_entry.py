"""Bricks/entry-label"""


simple_menu = """
   nome cognome
   indirizzo  -

"""



l = Layout(simple_menu, opts="Ts")

w = l.show()
e = w['e=nome']
l.sem = "OUT"
def show_text(wdg, ev, l):
    print l
    txt = wdg.get_text()
    print "txt: ", txt, "sem", l.sem

    if len(txt) > 5:
        return

    if l.sem == 'OUT':
        l.sem = 'IN'
        print l.sem
        wdg.set_text(txt + '*')
        l.sem = 'OUT'
        
    print "sem: ", l.sem
    return
    
    
e.connect('notify::text', show_text, l)

