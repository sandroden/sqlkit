class Container(object):
    """
    a container for other object that allows iteration and dict-like access
    """
    def __init__(self, cdict=None):
        """
        cdict may be a dictionary that will be used to initialize the Container
        """
        self._attrs = []
        self._n = 0
        if cdict:
            for key, value in cdict.iteritems():
                self.add_element(key, value)

    def add_element(self, key, value):
        setattr(self, key, value)
        if not key in self._attrs:
            self._attrs += [key]

    def keys(self):
        return self._attrs

    def __contains__(self, key):
        return key in self._attrs
 
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        return self.add_element(key, value)
    
    def __iter__(self):
        return self

    def next(self):
        """return the next item in the data set or raise StopIteration"""

        try:
            r = getattr(self, self._attrs[self._n])
            self._n += 1
        except:
            self._n = 0
            raise StopIteration
      
        return r

    def __repr__(self):
        return "%s" % self._attrs

if __name__ == '__main__' :

    c = Container()
    c.add_element('uno', 1)
    print c.keys()
    print 'uno' in c
    c['due'] = 2
    print c.due
    for x in c:
        print x
