"""Trap: strftime('%p') is empty in many locales (e.g. it_IT) so 12h-format
labels collapsed to ambiguous "01:00", "02:00", ... and 12 collided with 0.

Fixed in sqlkit/layout/dateedit.py by rendering AM/PM ourselves in
DateTimeEdit._format_time_label and parsing them in _parse_time_text without
relying on locale-dependent strptime('%p').
"""
from _harness import ensure_path, run_tests
ensure_path()

import datetime
import unittest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402

from sqlkit.layout.dateedit import DateTimeEdit  # noqa: E402


def _make():
    # DateTimeEdit needs a realized parent to fill the combobox model fully,
    # but _format_time_label and _parse_time_text are pure helpers.
    return DateTimeEdit()


def test_format_24h():
    w = _make()
    w._use_24h_format = True
    assert w._format_time_label(0, 0) == '00:00'
    assert w._format_time_label(13, 30) == '13:30'
    assert w._format_time_label(23, 45) == '23:45'


def test_format_12h_includes_ampm():
    w = _make()
    w._use_24h_format = False
    assert w._format_time_label(0, 0) == '12:00 AM'
    assert w._format_time_label(1, 15) == '01:15 AM'
    assert w._format_time_label(11, 0) == '11:00 AM'
    assert w._format_time_label(12, 0) == '12:00 PM'
    assert w._format_time_label(13, 0) == '01:00 PM'
    assert w._format_time_label(23, 45) == '11:45 PM'


def test_format_12h_unique_per_hour():
    # Trap re-check: every hour 0..23 must produce a distinct label.
    w = _make()
    w._use_24h_format = False
    labels = {w._format_time_label(h, 0) for h in range(24)}
    assert len(labels) == 24, labels


def test_parse_24h():
    w = _make()
    assert w._parse_time_text('00:00') == datetime.time(0, 0)
    assert w._parse_time_text('13:30') == datetime.time(13, 30)
    assert w._parse_time_text('23:59') == datetime.time(23, 59)


def test_parse_12h_ampm():
    w = _make()
    assert w._parse_time_text('12:00 AM') == datetime.time(0, 0)
    assert w._parse_time_text('01:00 AM') == datetime.time(1, 0)
    assert w._parse_time_text('12:00 PM') == datetime.time(12, 0)
    assert w._parse_time_text('01:00 PM') == datetime.time(13, 0)
    assert w._parse_time_text('11:45 PM') == datetime.time(23, 45)


def test_parse_12h_case_insensitive():
    w = _make()
    assert w._parse_time_text('03:30 pm') == datetime.time(15, 30)
    assert w._parse_time_text('03:30pm') == datetime.time(15, 30)


def test_parse_dot_separator():
    # get_time previously accepted '03.30' via re.split('[.:]', ...).
    w = _make()
    assert w._parse_time_text('03.30') == datetime.time(3, 30)


def test_parse_invalid_raises():
    w = _make()
    for bad in ('', 'xx', '25:00', '12:60', '13:00 PM'):
        try:
            w._parse_time_text(bad)
        except (ValueError, Exception):
            continue
        raise AssertionError('expected error for %r' % bad)


if __name__ == '__main__':
    run_tests(globals())
