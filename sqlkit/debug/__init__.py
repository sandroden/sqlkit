from . import debug as _debug_module
__doc__ = _debug_module.__doc__
from .debug import *
# `from .debug import *` exports a function called debug() that shadows
# the submodule of the same name. Restore submodule access so that
# `from sqlkit.debug import debug` (or relative `from . import debug`)
# yields the module, while the function is still available as
# `sqlkit.debug.<all-other-symbols>`.
debug = _debug_module
del _debug_module
