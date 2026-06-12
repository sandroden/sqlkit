"""py3 regression: optionparse monkeypatched optparse.Values.__nonzero__,
which Python 3 ignores (the hook is __bool__). Every ``if not opts:`` check
was therefore always False — notably sqledit without arguments crashed
instead of opening the connection dialog.
"""

from sqlkit.misc import optionparse

DOC = """
dummy parser

usage: %prog [options] [argument]
   -u, --url=URL: an url to open
   -t, --table=TABLE: a table
"""


def test_values_falsy_when_no_options_given():
    opts, args = optionparse.parse(DOC, [])
    assert not opts
    assert not args


def test_values_truthy_when_an_option_is_set():
    opts, args = optionparse.parse(DOC, ['-u', 'sqlite:///x.db'])
    assert opts
    assert opts.url == 'sqlite:///x.db'
