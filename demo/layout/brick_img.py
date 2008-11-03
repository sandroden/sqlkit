"""Bricks/images

A simple image. You can reset the image file locations as in:
l.elements['i=img'].properties['pixbuf'] = os.path.join(os.getvwd(), 'img.jpg')
"""


lay = """
   i=logo.jpg
"""


l = Layout(lay)

w = l.show()


        
    
