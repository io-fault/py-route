import importlib

# Import fault.routes package module.
from .. import __name__ as pkgname
module = importlib.import_module(pkgname)
