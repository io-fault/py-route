"""
# Route and Segment implementation used by &..system.files and &..system.python.

# [ File System ]

# File systems paths are managed using &File routes. The primary constructor is the
# &File.from_path class method that resolves relative paths based on the current
# working directory of the process:

#!/pl/python
	route = fault.system.files.Path.from_path('file-in-current-directory')

# Normally, Routes are created from class methods, not from type instantiation.
# File systems routes have a number of constructors:

	# - &File.from_path
	# - &File.from_absolute
	# - &File.from_relative
	# - &File.from_cwd
	# - &File.temporary

# [ Python Module Hierarchy ]

# Python modules have their own hierarchy and a special Route class is used in order
# to provide a query set useful for Python modules.

# The primary constructor is the &Import.from_fullname class method that builds
# the Route from the module's full path.

#!/pl/python
	route = fault.system.python.Import.from_fullname('fault.routes.library')

# Imports have fewer constructors:

	# - &Import.from_fullname
	# - &Import.from_attributes
	# - &Import.from_context
"""
# Implementation Base Classes.
from .core import *

# XXX: Temporary names until references are updated.
from ..system.python import Import
from ..system.files import Path as File
