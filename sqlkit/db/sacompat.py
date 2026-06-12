# Copyright (C) 2008-2010, Sandro Dentella <sandro@e-den.it>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
SQLAlchemy compatibility helpers shared between the 1.4 and 2.x branches.

Everything that differs between the two SA versions is funnelled through
this module so that the rest of sqlkit stays version-agnostic.
"""

import sqlalchemy
from sqlalchemy.sql import expression

#: Major version of the running SQLAlchemy (1 or 2)
SA_MAJOR = int(sqlalchemy.__version__.split('.')[0])

# ---------------------------------------------------------------------------
# Classical/imperative mapping
# ---------------------------------------------------------------------------
# ``sqlalchemy.orm.mapper()`` was removed in SA 2.0.  The replacement is
# ``registry().map_imperatively(Class, table)`` which already exists in 1.4.
# It returns the very same Mapper object the old ``mapper()`` used to return,
# so behaviour (and the returned type) is preserved.


def map_imperatively(class_, local_table, **kw):
    """Map ``class_`` to ``local_table`` and return the resulting Mapper.

    Drop-in replacement for the removed ``sqlalchemy.orm.mapper()``.

    The callers in sqlkit always create a brand new throw-away class for
    reflected tables, so a fresh registry per call is safe (a class is never
    mapped twice).
    """
    from sqlalchemy.orm import registry
    reg = registry()
    return reg.map_imperatively(class_, local_table, **kw)


# ---------------------------------------------------------------------------
# expression.Label
# ---------------------------------------------------------------------------
# ``expression._Label`` (private) was renamed to the public ``expression.Label``.
# The public name already exists in 1.4, so use it directly and fall back to
# the private one only if some very old SA is around.
try:
    Label = expression.Label
except AttributeError:                                  # pragma: no cover
    Label = expression._Label


# ---------------------------------------------------------------------------
# Session autocommit mode
# ---------------------------------------------------------------------------
# The legacy ``Session.autocommit`` attribute (and the whole autocommit mode)
# was removed in SA 2.0.  On 2.x a session is always in the "begin on demand"
# mode that corresponds to the old ``autocommit=False``.


def session_autocommit(session):
    """Return whether ``session`` is in the legacy autocommit mode.

    Always ``False`` on SA 2.x (the mode no longer exists)."""
    return bool(getattr(session, 'autocommit', False))
