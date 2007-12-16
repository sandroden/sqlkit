#
# SqlChecker -- Abstract Class for checking tabular to sql conversions.
#
#
# Copyright (C) 2005, Michele Comitini <mcm@glisco.it>
# 

from warnings import warn

class SqlCheckError(Exception):
    pass
    
class RowInsertError(SqlCheckError):
    mesg = 'Error on data to be inserted'
    data = None
    idx = None
    
    def __init__(self, s = None, d = None, i = None):

        if s is not None:
            self.mesg = s
        if d is not None:
            self.data = d
        if i is not None:
            self.idx = i

        exmesg = ""
        if self.data:
            if self.idx is None:
                exmesg = str(self.mesg) + '\nData:' + str(self.data)
            else:
                exmesg = str(self.mesg) + '\nData:' + str(self.data) + '\nIndex:' + str(self.idx) + \
                       '\nValue:' + str(self.data[self.idx])
            

        SqlCheckError.__init__(self, exmesg)
 
class RowUpdateError(SqlCheckError):
    mesg = 'Error on data to be updated'
    data = None
    odata = None
    idx = None
    oidx = None
    
    def __init__(self, s = None, d = None, i = None, od = None, oi = None):

        if s is not None:
            self.mesg = s
        if d is not None:
            self.data = d
        if i is not None:
            self.idx = i
        if od is not None:
            self.odata = od
        if oi is not None:
            self.oidx = oi

        exmesg = ""
        if self.data is not None:
            if self.idx is None:
                exmesg = str(self.mesg) + '\nData:' + str(self.data)
            else:
                exmesg = str(self.mesg) + '\nData:' + str(self.data) + '\nIndex:' + str(self.idx) + \
                       '\nValue:' + str(self.data[self.idx])
        else:
            exmesg = str(self.mesg)

        SqlCheckError.__init__(self, exmesg)
        

class SqlChecker(object):

    sqltreeview = None

    def __init__(self, sqltreeview):
        self.sqltreeview = sqltreeview

    def rowUpdateCheck(self, old_data, new_data):
        warn('rowUpdateCheck() needs to be implemented')

    def rowInsertCheck(self, data):
        warn('rowInsertCheck() needs to be implemented')

    def rowDeleteCheck(self, data):
        warn('rowDeleteCheck() needs to be implemented')

