"""
Simple relative date algebra
=============================

a function that implements simple relative date algebra so that we can use it
in bookmarks and queries.

Allowed chars are::

  [-+ diwWmMyY @>]

letters refer to a moment of time or period according to use:

  :d: today
  :i: yesterday (ieri in italian, 'y' was already used by year)

  :w: beginning of week
  :W: end of week

  :m: beginning of month
  :M: end of month

  :y: beginning of year
  :Y: end of year

Math signs ``+`` and ``-`` work as you would expect they add and subtract
period of time. Whe used this way the following letter refers to a period::

  m+14d

is the 15rd day of the month (beginning of month + 2 days)
You can also use a short form (compatible with previous syntax)::

  m-1 == m-1m

You can use also > in which case the string is considered 2 dates, each built
as already stated::

  m-1 > M+2

means a 3 months period, starting from beginnig of last month to end of next
month

Persiods
-------------------
@ is a compact way to set a period::

  @m == m > M
  @m-1  == m-1 > M-1


Other examples
--------------

  :m-1: beginnning of last month
  :M+1: end of next month

"""

import re
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
from babel.dates import parse_date

class WrongRelativeDateFormat(Exception): pass

DATE_PATTERN = re.compile("""
    (?P<double>@)?
    (?P<math>[+-][0-9]*)?
    (?P<period>[imMdDyYwW])?
    (?P<math2>[+-][0-9]*)?
    $""",    re.VERBOSE)
CHARS = re.compile('[-+dimMwWyY>]')
TODAY = date.today()

def string2dates(string):
    """
    string is returned as is if no [-+dimMwWyY>] are found otherwise
    math as described in the doctring of the module is applied

    Since a string definition can split into two dates, a tuple is return
    anyhow, a tipical way to call it is::

      start, end = string2dates('whatever')

    if you are sure one date is in the definition, you can use
    string2date instead 
    """
    try:
        # first try a normal parsing via babel
        return parse_date(string), None
    except:
        pass
    
    m = re.search(CHARS, string)
    if not m:
        return string, None

    if '@' in string:
        base = string.replace('@','')
        string = "%s > %s" % (base.lower(), base.upper())

    data = string.split('>')

    if len(data) == 1:
        return (string2date(data[0]), None)
    else:
        return ( string2date(data[0]), string2date(data[1]  ))

def string2date(string):
    """
    return a date represented by a string applying math syntax as described
    in the docstring

    """
    try:
        # first try a normal parsing via babel
        return parse_date(string)
    except:
        pass
    m = re.search(CHARS, string)
    if not m:
        return string
    ## add spaces to math simbols, not in starting position, only if not
    ## preceded by spaces
    PAT_ADD_SPACES = '(?<=[^ ])([-+])'
    data = re.split(' +', re.sub(PAT_ADD_SPACES, r' \1', string).strip())
    ## 
    #print "DATA", data
    computed, last_period = transform(data[0])
    
    for token in data[1:]:
        computed, last_period = transform(
            token, start=computed, last_period=last_period)
        
    return computed
    

def transform(token, start=None, last_period=None):
    """transform token into a date
    Token is the very simple information: m +1m 2d
    if last_period is not none, the period can be missing and 'last_period'
    is used.   This allows to write: m-1 meaning 'beginning of last month'
    """
    if not start:
        start = TODAY
    #print "token", token, start, last_period

    m = re.match(DATE_PATTERN, token)

    if not m:
        raise WrongRelativeDateFormat(
            "Wrong Relative date format: %s" % token)
    else:
        period = m.group('period')

    if not period and last_period:
        period = last_period
        
    last_period = period
    

    if m.group('math'):
        math = m.group('math')
    else:
        math = m.group('math2')
    
    try:
        math = int(math)
    except TypeError:
        math = None
    
    if period == 'd':
        computed = start
        if math is not None:
            computed = computed + relativedelta(days=+math)

    if period == 'i':
        computed = start - timedelta(days=1)

    if period in ('w', 'W'):
        computed = start - timedelta(days=start.isoweekday()-1)
        if math is not None:
            computed = computed + relativedelta(weeks=+math)
        if period == 'W':
            computed = computed + relativedelta(weeks=+1, days=-1)
            

    if period in ('m', 'M'):
        computed =  start.replace(day=1)
        if math is not None:
            computed = computed + relativedelta(months=+math)

        if period == 'M':
            computed = computed + relativedelta(months=+1, days=-1)
            
    if period in ('y', 'Y'):
        j = int(start.strftime('%j'))
        computed = start - timedelta(days=j-1)
        if math is not None:
            computed = computed + relativedelta(years=+math)
        if period == 'Y':
            computed = computed + relativedelta(years=+1, days=-1)
            

    return (computed, last_period)


if __name__ == '__main__':

    
    string = 'd'
#    NOV=date(2007,11,1)

    r = string2dates(string)
    print r, type(r)
#    print transform('y', start=NOV)
