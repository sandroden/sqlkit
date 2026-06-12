"""Finding #1: in Field.validate's except block the error message referenced
an undefined `field_name`, raising NameError that masked the real validation
error.  It must use self.field_name (and now also includes the offending
value).  The original format string had three %s placeholders but only two
args, which would itself have raised TypeError.
"""
from sqlkit import exc
from sqlkit.fields import Field


class _BoomField(Field):
    """Minimal Field subclass whose clean_value always blows up, so we can
    exercise the except branch in validate() without a real widget/master."""
    type = str

    def __init__(self):
        # bypass the heavy Field.__init__: set just what validate() touches
        self.field_name = 'myfield'
        self.nullable = True
        self.default = None

    def clean_value(self, value, obj=None):
        raise ValueError("kaboom")


def test_validate_raises_validationerror_not_nameerror():
    f = _BoomField()
    try:
        f.validate('some-bad-value', clean=False)
    except exc.ValidationError as e:
        msg = str(e)
        # the real field name and value must appear, no NameError leaked
        assert 'myfield' in msg
        assert 'some-bad-value' in msg
        assert 'kaboom' in msg
    except NameError:
        raise AssertionError("validate() leaked a NameError (field_name unbound)")
    else:
        raise AssertionError("expected a ValidationError to be raised")
