from .venue_request import *

# Without this, `from .venue_request import *` in openreview/__init__.py also copies the
# submodule of the same name, which then replaces the `openreview.venue_request` package.
__all__ = [name for name in dir() if not name.startswith('_') and name != 'venue_request']
