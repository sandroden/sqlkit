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
CSS helpers to replace the Gtk2 ``modify_base``/``modify_text``/``modify_fg``
APIs that are silently ignored by modern Gtk3 themes.

The functions here generate a tiny per-widget :class:`Gtk.CssProvider`,
attach it to the widget's style context with
``Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION`` (so it wins over the theme), and
keep a reference on the widget (``_sk_css_provider_<role>``) so that a later
call can *remove* the previous provider before installing a new one (or simply
clear it when the colour is reset).

Important Gtk3 gotchas handled here:

* themes paint ``Gtk.Entry`` backgrounds with a ``background-image`` gradient,
  so a plain ``background-color`` is invisible unless we also set
  ``background-image: none``;
* a :class:`Gtk.TextView` paints its text area through the ``text`` subnode,
  hence the ``textview text { ... }`` selector.
"""

from gi.repository import Gtk
from gi.repository import Gdk


def color_to_css(color):
    """Return a CSS colour string for *color*.

    *color* may be:

    * a ``str`` (passed through verbatim: any valid CSS/X11 colour name or
      ``#rrggbb`` works, e.g. ``'green'``, ``'#f6ebba'``);
    * a :class:`Gdk.Color` (16-bit components, the old ``Gdk.color_parse``
      result);
    * a :class:`Gdk.RGBA` (e.g. from ``style_context.get_background_color``).
    """
    if isinstance(color, str):
        return color
    if isinstance(color, Gdk.RGBA):
        return color.to_string()
    if isinstance(color, Gdk.Color):
        # Gdk.Color uses 16-bit channels; to_string() yields #rrrrggggbbbb
        # which CSS accepts, but normalise to #rrggbb to be safe/portable.
        r = color.red >> 8
        g = color.green >> 8
        b = color.blue >> 8
        return '#%02x%02x%02x' % (r, g, b)
    # last resort: let Gtk try to stringify it
    return str(color)


def apply_css(widget, role, css):
    """Install *css* on *widget* under the given *role*.

    Removes any previously-installed provider for the same *role* first.  If
    *css* is falsy the role is simply cleared (colour reset).  *role* is an
    arbitrary short label that namespaces the stored provider reference, so a
    widget can carry several independent CSS overrides (e.g. ``'bg'`` and
    ``'text'``).
    """
    attr = '_sk_css_provider_%s' % role
    context = widget.get_style_context()

    old = getattr(widget, attr, None)
    if old is not None:
        context.remove_provider(old)
        setattr(widget, attr, None)

    if not css:
        return

    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode('utf-8'))
    context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    setattr(widget, attr, provider)


def _selector_for(widget, kind):
    """Return the CSS selector fragment appropriate for *widget*.

    *kind* is ``'bg'`` or ``'text'``.  Entries need ``background-image: none``
    to override theme gradients; TextViews paint through a ``text`` subnode.
    """
    if isinstance(widget, Gtk.TextView):
        node = 'textview text'
    elif isinstance(widget, Gtk.Entry):
        node = 'entry'
    else:
        node = '*'
    return node


def set_background(widget, color):
    """Set the *background* of *widget* (entry/textview/...) to *color*.

    Pass ``color=None`` to clear a previously-set background.
    """
    if color is None:
        apply_css(widget, 'bg', None)
        return
    node = _selector_for(widget, 'bg')
    css = '%s { background-image: none; background-color: %s; }' % (
        node, color_to_css(color))
    apply_css(widget, 'bg', css)


def set_text_color(widget, color, disabled_only=False):
    """Set the *foreground/text* colour of *widget* to *color*.

    Pass ``color=None`` to clear.  When *disabled_only* is True the colour only
    applies to the ``:disabled`` (insensitive) state, reproducing the old
    ``modify_text(INSENSITIVE, ...)`` behaviour that greyed out non-editable
    widgets.
    """
    if color is None:
        apply_css(widget, 'text', None)
        return
    node = _selector_for(widget, 'text')
    pseudo = ':disabled' if disabled_only else ''
    if isinstance(widget, Gtk.TextView):
        # textview text -> the :disabled goes on the textview node
        node = 'textview%s text' % pseudo
        css = '%s { color: %s; }' % (node, color_to_css(color))
    else:
        css = '%s%s { color: %s; }' % (node, pseudo, color_to_css(color))
    apply_css(widget, 'text', css)


def set_label_color(label, color):
    """Set the foreground colour of a :class:`Gtk.Label` to *color*.

    Pass ``color=None`` to clear.  Used for the blue foreign-key labels.
    """
    if color is None:
        apply_css(label, 'fg', None)
        return
    css = 'label { color: %s; }' % color_to_css(color)
    apply_css(label, 'fg', css)
