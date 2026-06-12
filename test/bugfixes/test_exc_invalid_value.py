"""Finding #10: exc.InvalidValue must have a usable __str__ (like
NotNullableFieldError) returning self.message."""
from sqlkit import exc


def test_invalid_value_str_returns_message():
    e = exc.InvalidValue('age', 999)
    assert str(e) == e.message
    assert 'age' in str(e)


def test_invalid_value_custom_message():
    e = exc.InvalidValue('age', 999, message="boom")
    assert str(e) == "boom"
