"""Finding #13: unregister_hook / unregister_layout ignored `nick` and deleted
every registration for the table.  They must only remove the requested nick,
leaving the others in place; when the last nick is removed the table entry is
dropped entirely.
"""
from sqlkit.db import defaults


class HookA:
    pass


class HookB:
    pass


def test_unregister_hook_only_removes_given_nick():
    defaults.hooks.clear()
    defaults.register_hook('t1', HookA, nick='default')
    defaults.register_hook('t1', HookB, nick='alt')

    defaults.unregister_hook('t1', nick='alt')

    assert defaults.get_hook('t1', nick='default') is HookA
    assert defaults.get_hook('t1', nick='alt') is None


def test_unregister_hook_last_nick_drops_table():
    defaults.hooks.clear()
    defaults.register_hook('t2', HookA, nick='default')
    defaults.unregister_hook('t2', nick='default')
    assert 't2' not in defaults.hooks


def test_unregister_layout_only_removes_given_nick():
    defaults.layout_dict.clear()
    defaults.register_layout('t1', 'LAYOUT_A', nick='default')
    defaults.register_layout('t1', 'LAYOUT_B', nick='alt')

    defaults.unregister_layout('t1', nick='alt')

    assert defaults.get_layout('t1', nick='default') == 'LAYOUT_A'
    assert defaults.get_layout('t1', nick='alt') is None


def test_unregister_layout_last_nick_drops_table():
    defaults.layout_dict.clear()
    defaults.register_layout('t2', 'LAYOUT_A', nick='default')
    defaults.unregister_layout('t2', nick='default')
    assert 't2' not in defaults.layout_dict
