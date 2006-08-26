#!/usr/bin/env python
# coding: latin1

import sys, re, datetime

sys.path.append ('../../')

from ooffice import opop
import tempfile, os

page = opop.Sxw(file='eurotest.sxw', verbose=True)

for i in range(8):
    page.add({
        'filo' : "filo%s" % i,
        'titolo' : "titolo %s" % i,
        'colore' : "colore %s" % i
        })

for i in range(5):
    page.add({
        'art' : "art%s" % i,
        'descr' : "descrizione %s" % i
        })
    
page.add({'user' : 'sandro dentella'})

page.lod[3]['titolo'] = """
      Piu' che un titolo questa e' una lunga dissertazione su cosa 
      convenga fare quando si vuole tutto nella vita perché devo fare
      una prova di un paragrafo lungo"""


outfile = os.path.join(tempfile.gettempdir(), 'euro.sxw')
outfile_pdf = os.path.join(tempfile.gettempdir(), 'euro.pdf')
outfile_rml = os.path.join(tempfile.gettempdir(), 'euro.rml')

#page.make_sxw(outfile=outfile)
#page.make_sxw(outfile=None)
#page.make_rml(outfile=outfile_rml)
#page.make_pdf3(outfile=outfile_pdf)
page.make_pdf(outfile=outfile_pdf)
# page.clean()
