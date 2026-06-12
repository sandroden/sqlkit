"""Relative-date algebra (sqlkit.misc.datetools).

Mirrors the historic behaviour captured in test/doctest/dates.txt, but as
pytest with the ``frozen_date`` fixture (TODAY = 2007-06-02).
"""
import datetime

import pytest

from sqlkit.misc import datetools as dt

D = datetime.date


@pytest.mark.parametrize(
    "spec, expected",
    [
        # day
        ("d", D(2007, 6, 2)),
        ("-1d", D(2007, 6, 1)),
        ("i", D(2007, 6, 1)),       # 'i' = yesterday
        ("d-5", D(2007, 5, 28)),
        ("d+9", D(2007, 6, 11)),
        # week (european: monday based)
        ("w", D(2007, 5, 28)),
        ("W", D(2007, 6, 3)),
        ("w-1", D(2007, 5, 21)),
        ("W-1", D(2007, 5, 27)),
        ("w+1", D(2007, 6, 4)),
        ("W+1", D(2007, 6, 10)),
        # month
        ("m", D(2007, 6, 1)),
        ("M", D(2007, 6, 30)),
        ("m-1", D(2007, 5, 1)),
        ("M-1", D(2007, 5, 31)),
        ("M-1m", D(2007, 5, 31)),
        ("M-2d-1m", D(2007, 5, 28)),
        ("M-1m-2d", D(2007, 5, 29)),
        ("m+1", D(2007, 7, 1)),
        ("M+1", D(2007, 7, 31)),
        # year
        ("y", D(2007, 1, 1)),
        ("Y", D(2007, 12, 31)),
        ("y-1", D(2006, 1, 1)),
        ("Y-1", D(2006, 12, 31)),
        ("y+1", D(2008, 1, 1)),
        ("Y+1", D(2008, 12, 31)),
        # mixing
        ("y +2m", D(2007, 3, 1)),
        ("y+2m", D(2007, 3, 1)),
        ("m+15d", D(2007, 6, 16)),
        ("Y -2m", D(2007, 10, 31)),
        ("Y -1m", D(2007, 11, 30)),
        ("Y -m", D(2007, 11, 30)),
    ],
)
def test_string2date(frozen_date, spec, expected):
    assert dt.string2date(spec) == expected


def test_string2date_with_shift(frozen_date):
    # m+15d -> 2007-06-16 (saturday), shift to next allowed weekday {1..5}
    assert dt.string2date("m+15d {12345}") == D(2007, 6, 18)


@pytest.mark.parametrize(
    "spec, expected",
    [
        ("y > Y", (D(2007, 1, 1), D(2007, 12, 31))),
        ("y+3m > Y-3m", (D(2007, 4, 1), D(2007, 9, 30))),
        ("@m", (D(2007, 6, 1), D(2007, 6, 30))),
        ("@2m", (D(2007, 6, 1), D(2007, 7, 31))),
        ("@2m-1", (D(2007, 5, 1), D(2007, 6, 30))),
        ("@w", (D(2007, 5, 28), D(2007, 6, 3))),
        ("@w+2", (D(2007, 6, 11), D(2007, 6, 17))),
        ("@m-1", (D(2007, 5, 1), D(2007, 5, 31))),
        ("@y", (D(2007, 1, 1), D(2007, 12, 31))),
        ("@y-1", (D(2006, 1, 1), D(2006, 12, 31))),
        ("@y +1", (D(2008, 1, 1), D(2008, 12, 31))),
        ("@d", (D(2007, 6, 2), D(2007, 6, 3))),
        ("@d+1", (D(2007, 6, 3), D(2007, 6, 4))),
        ("@2d-1", (D(2007, 6, 1), D(2007, 6, 3))),
    ],
)
def test_string2dates_periods(frozen_date, spec, expected):
    assert dt.string2dates(spec) == expected


def test_string2dates_single_date_has_none_end(frozen_date):
    start, end = dt.string2dates("m")
    assert start == D(2007, 6, 1)
    assert end is None


def test_today_respects_test_flag(frozen_date):
    assert dt.today() == D(2007, 6, 2)
