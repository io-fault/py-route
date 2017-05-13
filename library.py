"""
# File system and Python Module routes. Manipulate paths and query the file system.

# &.library provides the only functionality of the project. The &File and &Import classes
# allow the management of filesystem and import routes with query methods that can
# interrogate their respective systems. The &Route base class is designed for subclassing;
# the point-sequence manipulation functions and context management allows Routes of different
# types to be defined that share similar semantics with respect to finite identifier selection.

# [ File System ]

# File systems paths are managed using &File routes. The primary constructor is the
# &File.from_path class method that resolves relative paths based on the current
# working directory of the process:

#!/pl/python
	route = libroutes.File.from_path('file-in-current-directory')

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
	route = libroute.Import.from_fullname('fault.routes.library')

# Imports have fewer constructors:

	# - &Import.from_fullname
	# - &Import.from_attributes
	# - &Import.from_context

# [ Abstract Routes ]

# &Route provides a base class for managing an arbitrary route. The primary requirement
# being that the points along the route should be hashable.
"""
import os
import os.path
import sys
import pkgutil
import importlib
import shutil
import tempfile
import contextlib
import collections
import stat
import typing
import itertools
import functools
import operator

from ..chronometry import library as libtime # Import needs to be delayed somehow.

@functools.total_ordering
class Route(object):
	"""
	# Route base class.

	# Provides generic manipulation methods.
	"""

	def __init__(self, context:object, points:tuple):
		self.context = context
		self.points = points

	def __pos__(self):
		"""
		# Return a new equivalent instance with a context depth of 1 so
		# that the new Route's context contains all the points of the
		# original Route.
		"""

		context = self.__class__(None, self.absolute)
		return self.__class__(context, ())

	def __rshift__(self, target, predicate=operator.eq,
			takewhile=itertools.takewhile,
			zip=zip,
			sum=sum,
			len=len,
		) -> (int, tuple):
		"""
		# Construct a sequence of points identifying the &target relative to &self.

		# Essentially, find the common prefix and note the number of containers between
		# it and &self. Subsequently, get the points necessary to select the target from
		# that common prefix.
		"""

		target_path = target.absolute
		from_path = self.absolute

		i = takewhile(True.__eq__, itertools.starmap(predicate, zip(target_path, from_path)))
		top = sum(1 for x in i)
		containers = len(from_path) - top - 1

		return containers, tuple(target_path[top:])

	def __lshift__(self, target):
		"""
		# Parameter inversion of &__rshift__.
		"""
		return target >> self

	def __hash__(self):
		"""
		# Hash on the &absolute of the Route allowing consistency regardless of context.
		"""
		return hash(self.absolute)

	def __eq__(self, ob, isinstance=isinstance):
		"""
		# Whether the absolute points of the two Routes are consistent.
		"""

		if isinstance(ob, self.__class__):
			return self.absolute == ob.absolute

	def __lt__(self, ob, isinstance=isinstance):
		if isinstance(ob, self.__class__):
			return self.absolute < ob.absolute

	def __contains__(self, absolute):
		return absolute.points[:len(self.points)] == self.points

	def __getitem__(self, req):
		"""
		# Select slices and items from the *relative* &points.
		# Points inside the &context will not be accessible.
		"""

		return self.points[req]

	def __add__(self, tail):
		"""
		# Add the two Routes together maintaining the context of the first.

		# Maintains the invariant: `x+y == x.extend(y.absolute)`.
		"""
		return tail.__class__(self.context, self.points + tail.absolute)

	def __truediv__(self, next_point):
		"""
		# Extend the Route by one point.
		"""
		return self.__class__(self.context, self.points + (next_point,))

	def __mul__(self, replacement):
		"""
		# Select a node adjacent to the current selection.

		# Returns a new &Route.
		"""
		return self.container / replacement

	def __pow__(self, ancestor:int):
		"""
		# Select the n-th ancestor of the route.

		# Returns a new &Route.
		"""

		y = self
		# This is not efficient, but it allows the preservation
		# of the context.
		for x in range(ancestor):
			y = y.container
		return y

	def extend(self, extension):
		"""
		# Extend the Route using the given sequence of points.
		"""

		return self.__class__(self.context, self.points + tuple(extension))

	def __neg__(self):
		"""
		# Return a new &Route with &self's absolute points reversed.
		# The &context is not maintained in the returned instance.

		# ! WARNING:
			# Tentative interface.
		"""

		return self.__class__(None, tuple(reversed(self.absolute)))

	def __invert__(self):
		"""
		# Consume one context level into a new Route. The invariant, `self == ~self`, holds;
		# If the &context is &None, &self will be returned.
		"""

		if self.context is None:
			return self

		return self.__class__(self.context.context, self.context.points + self.points)

	@property
	def absolute(self):
		"""
		# The absolute sequence of points.
		"""

		r = self.points
		x = self
		while x.context is not None:
			r = x.context.points + r
			x = x.context
		return r

	@property
	def relative(self):
		"""
		# The sequence of points relative to the context.
		# Synonym for the &points property.
		"""
		return self.points

	@property
	def identifier(self):
		"""
		# The identifier of the node relative to its container. (Head)
		"""

		if self.points:
			return self.points[-1]
		else:
			if self.context is not None:
				return self.context.identifier
			return None

	@property
	def root(self):
		"""
		# The root &Route with respect to the Route's context.
		"""

		return self.__class__(self.context, self.points[0:1])

	@property
	def container(self):
		"""
		# Return a Route to the outer (parent) Route; this merely removes the last point in the
		# sequence trimming the &context when necessary.
		"""

		if self.points:
			return self.__class__(self.context, self.points[:-1])
		else:
			return self.__class__(None, self.absolute[:-1])

	@staticmethod
	def _relative_resolution(points, len=len):
		"""
		# Resolve points identified as self points, `.`, and container points, `..`.

		# Used by &Route subclasses to support relative paths; this method should not be used
		# directly.
		"""
		rob = []
		add = rob.append
		parent_count = 0

		for x in points:
			if not x or x == '.':
				continue
			elif x == '..':
				parent_count += 1
			else:
				if parent_count:
					del rob[-parent_count:]
					parent_count = 0
				add(x)
		else:
			if parent_count:
				del rob[-parent_count:]

		return rob

class File(Route):
	"""
	# &Route subclass for file system paths.
	"""
	_path_separator = os.path.sep

	__slots__ = ('context', 'points',)

	@classmethod
	def from_path(Class, path:str, getcwd=os.getcwd) -> "File":
		"""
		# Construct a &File instance from the given absolute or relative path
		# provided for &string; if a relative path is specified, it will
		# be relative to the current working directory as identified by
		# &os.getcwd.

		# This is usually the most appropriate way to instantiate a &File route
		# from user input. The exception being cases where the current working
		# directory is *not* the relevant context.
		"""

		if path and path[0] == '/':
			return Class.from_absolute(path)
		else:
			return Class.from_relative(Class.from_absolute(getcwd()), path)

	@classmethod
	def from_relative(Class, context:"File", path:str, chain=itertools.chain) -> "File":
		"""
		# Return a new Route pointing to the file referenced by &path;
		# where path is a path relative to the &context &File instance.

		# This function does *not* refer to the current working directory
		# returned by &os.getcwd; if this is desired, &from_path is the
		# appropriate constructor to use.
		"""
		s = Class._path_separator

		points = Class._relative_resolution(chain(
			context.absolute,
			path.strip(s).split(s)
		))
		return Class(None, tuple(points))

	@classmethod
	def from_absolute(Class, path:str, tuple=tuple) -> "File":
		return Class(None, tuple(x for x in path.split(Class._path_separator) if x))

	@classmethod
	def from_cwd(Class, *points:str, getcwd=os.getcwd) -> "File":
		"""
		# Return a new Route to the current working directory.

		# The returned Route's `context` is the current working directory path,
		# and the &points as the sequence of following identifiers.
		"""

		return Class(Class.from_absolute(getcwd()), points)

	@classmethod
	def home(Class) -> "File":
		"""
		# Return a new Route to the home directory defined by the environment.

		# The returned Route's &context is the HOME path.
		"""

		return Class(Class.from_absolute(os.environ['HOME']), ())

	@classmethod
	@contextlib.contextmanager
	def temporary(Class, TemporaryDirectory=tempfile.TemporaryDirectory) -> Route:
		"""
		# Create a temporary directory at the route using a context manager.
		# This is a wrapper around &tempfile.TemporaryDirectory that returns a &Route.

		# The use of specific temporary files is avoided as they have inconsistent
		# behavior on certain platforms.

		# A &File route to the temporary directory is returned on entrance,
		# so the (keyword)`as` target *must* be specified in order to refer
		# files inside the directory.
		"""

		with TemporaryDirectory() as d:
			yield Class(Class.from_absolute(d), ())

	@classmethod
	def which(Class, exe, dirname=os.path.dirname) -> "File":
		"""
		# Return a new Route to the executable found by which.
		"""

		rp = shutil.which(exe)
		if rp is None:
			return None

		dn = dirname(rp)

		return Class(Class.from_absolute(dn), (rp[len(dn)+1:],))

	def __repr__(self):
		return '{0}.{1}.from_absolute({2!r})'.format(__name__, self.__class__.__name__, self.fullpath)

	def __str__(self):
		return self.fullpath

	@property
	def fullpath(self, sep=os.path.sep) -> str:
		"""
		# Returns the full filesystem path designated by the route.
		"""

		if self.context is not None:
			# let the outermost context handle the root /, if any
			prefix = self.context.fullpath
			if not self.points:
				return prefix
		else:
			if not self.points:
				return sep
			# Covers the case for a leading '/'
			prefix = ''

		rpath = sep.join(self.points)

		return sep.join((prefix, rpath))

	@property
	def bytespath(self, encoding=sys.getfilesystemencoding()) -> bytes:
		"""
		# Returns the full filesystem path designated by the route as a &bytes object
		# returned by encoding the &fullpath in &sys.getfilesystemencoding with
		# `'surrogateescape'` as the error mode.
		"""

		return self.fullpath.encode(encoding, "surrogateescape")

	def suffix(self, appended_suffix) -> "File":
		"""
		# Modify the name of the file adding the given suffix.

		# Returns a new &File Route.
		"""

		*prefix, basename = self.points
		prefix.append(basename + appended_suffix)

		return self.__class__(self.context, tuple(prefix))

	def prefix(self, s) -> "File":
		"""
		# Modify the name of the file adding the given prefix.

		# Returns a new &File Route.
		"""

		*prefix, basename = self.points
		prefix.append(s + basename)

		return self.__class__(self.context, tuple(prefix))

	@property
	def extension(self):
		"""
		# Return the dot-extension of the file path.

		# Given a route to a file with a '.' in the final point, return the remainder of
		# the string after the '.'. Dot-extensions are often a useful indicator for the
		# consistency of the file's content.
		"""

		i = self.identifier
		p = i.rfind('.')
		if p == -1:
			return None

		return i[p+1:]

	_type_map = {
		stat.S_IFIFO: 'pipe',
		stat.S_IFLNK: 'link',
		stat.S_IFREG: 'file',
		stat.S_IFDIR: 'directory',
		stat.S_IFSOCK: 'socket',
		stat.S_IFBLK: 'device',
		stat.S_IFCHR: 'device',
	}

	def type(self, ifmt=stat.S_IFMT, stat=os.stat, type_map=_type_map) -> str:
		"""
		# The kind of node the route points to. Transforms the result of an &os.stat
		# call into a string describing the (python:attribute)`st_mode` field.

		# [Effects]
		# /Product
			# - `'pipe'`
			# - `'link'`
			# - `'file'`
			# - `'directory'`
			# - `'socket'`
			# - `'device'`
		"""

		try:
			s = stat(self.fullpath)
		except FileNotFoundError:
			return None

		return type_map[ifmt(s.st_mode)]

	def executable(self, get_stat=os.stat, mask=stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH) -> bool:
		"""
		# Whether the file at the route is considered to be an executable.
		"""

		mode = get_stat(self.fullpath).st_mode
		return (mode & mask) != 0

	def is_container(self, isdir=os.path.isdir) -> bool:
		"""
		# Whether or not the &Selection is a directory.
		"""

		return isdir(self.fullpath)
	is_directory = is_container

	def is_regular_file(self):
		"""
		# Whether or not the &Selection is a regular file.

		# Uses &os.stat to query the local file system to discover the type.
		"""

		return self.type() == 'file'

	def subnodes(self, listdir=os.listdir, isdir=os.path.isdir, join=os.path.join):
		"""
		# Return a pair of lists, the first being a list of Routes to
		# directories in this Route and the second being a list of Routes to non-directories
		# in this Route.

		# If the Route does not point to a directory, a pair of empty lists will be returned.
		"""

		path = self.fullpath

		try:
			l = listdir(path)
		except OSError:
			# Error indifferent.
			# User must make explicit checks to interrogate permission/existence.
			return ([], [])

		directories = []
		files = []
		for x in l:
			sub = self.__class__(self, (x,))
			if isdir(join(path, x)):
				directories.append(sub)
			else:
				files.append(sub)

		return directories, files

	def tree(self, Queue=collections.deque):
		"""
		# Return a directory's full tree as a pair of lists of &File
		# instances referring to the contained directories and files.
		"""
		dirs, files = self.subnodes()
		cseq = Queue(dirs)

		while cseq:
			dir = cseq.popleft()
			sd, sf = dir.subnodes()

			# extend output
			dirs.extend(sd)
			files.extend(sf)

			# process subdirectories
			cseq.extend(sd)

		return dirs, files

	def since(self, since:libtime.Timestamp,
			traversed=None,
		) -> typing.Iterable[typing.Tuple[libtime.Timestamp, Route]]:
		"""
		# Identify the set of files that have been modified
		# since the given point in time.

		# The resulting &typing.Iterable does not include directories.

		# [ Parameters ]

		# /since
			# The point in time after which files and directories will be identified
			# as being modified and returned inside the result set.
		"""

		# Traversed holds real absolute paths.
		if not traversed:
			traversed = set()
			traversed.add(os.path.realpath(str(self)))
		else:
			rpath = os.path.realpath(str(self))
			if rpath in traversed:
				return
			else:
				traversed.add(rpath)

		dirs, files = self.subnodes()

		for x in files:
			mt = x.last_modified()
			if mt.follows(since):
				yield (mt, x)

		for x in dirs:
			yield from x.since(since, traversed=traversed)

	def real(self, exists=os.path.exists) -> "File":
		"""
		# Return the part of the File route that actually exists on the File system.
		"""

		x = self.__class__.from_absolute(self.fullpath)
		while x.points:
			if exists(x.fullpath):
				return x
			x = x.container

	def exists(self, exists=os.path.lexists) -> bool:
		"""
		# Return the part of the File route that actually exists on the File system.
		"""

		return exists(self.fullpath)

	def size(self, stat=os.stat) -> int:
		"""
		# Return the size of the file as depicted by &os.stat.

		# The &os.stat function is used to get the information.
		# &None is returned if an &OSError is raised by the call.
		"""

		return stat(self.fullpath, follow_symlinks=True).st_size

	def get_last_modified(self, stat=os.stat, unix=libtime.unix) -> libtime.Timestamp:
		"""
		# Return the modification time of the file.
		"""

		return unix(stat(self.fullpath).st_mtime)
	last_modified = get_last_modified

	def set_last_modified(self, time:libtime.Timestamp, utime=os.utime):
		"""
		# Set the modification time of the file identified by the &Route.
		"""

		return utime(self.__str__(), (-1, time.select('unix')/1000))

	def meta(self, stat=os.stat, unix=libtime.unix):
		"""
		# Return file specific meta data.

		# ! WARNING:
			# Preliminary API.
		"""

		st = stat(self.fullpath)

		return (unix(st.st_ctime), unix(st.st_mtime), st.st_size)

	def void(self, rmtree = shutil.rmtree, remove=os.remove):
		"""
		# Remove the entire tree that this Route points to.
		# No file will survive. Unless it's not owned by the user.
		"""

		if self.exists():
			if self.is_container():
				rmtree(self.fullpath)
			else:
				remove(self.fullpath)

	def replace(self, replacement:"File", copytree=shutil.copytree, copyfile=shutil.copy):
		"""
		# Drop the existing file or directory, &self, and replace it with the
		# file or directory at the given route, &replacement.

		# [ Parameters ]

		# /replacement
			# The route to the file or directory that will be used to replace
			# the one at &self.
		"""

		self.void()
		src = replacement.fullpath
		dst = self.fullpath

		if replacement.is_container():
			copytree(src, dst, symlinks=True, copy_function=copyfile)
		else:
			copyfile(src, dst)

	def link(self, to:"File", relative=True, link=os.symlink, exists=os.path.lexists):
		"""
		# Create a *symbolic* link at &self pointing to &to, the target file.

		# [ Parameters ]
		# /to
			# The target of the symbolic link.
		# /relative
			# Whether or not to resolve the link as a relative path.
		"""

		if relative:
			parents, points = self >> to
			target = '../' * parents
			target += '/'.join(points)
		else:
			target = str(to)

		dst = str(self)
		if exists(dst):
			os.remove(dst)

		link(target, dst)

	def init(self, type, mkdir=os.mkdir, exists=os.path.lexists):
		"""
		# Create the filesystem node described by the type parameter at this route.
		# Any directories leading up to the node will be automatically created if
		# they do not exist.

		# If a node of any type already exists at this route, nothing happens.

		# &type is one of: `'file'`, `'directory'`, `'pipe'`.
		"""

		fp = self.fullpath
		if exists(fp):
			return

		routes = []
		x = self.container
		while not exists(x.fullpath):
			routes.append(x)
			x = x.container

		# create directories
		routes.reverse()
		for x in routes:
			mkdir(x.fullpath)

		if type == "file":
			# touch the file.
			with open(fp, 'x'): # Save ACL errors, concurrent op created file
				pass
		elif type == "directory":
			mkdir(fp)
		elif type == "pipe":
			os.mkfifo(fp)

	@contextlib.contextmanager
	def open(self, *args, **kw):
		"""
		# Open the file pointed to by the route.

		# If the file doesn't exist, create it; if the directories
		# leading up to the file don't exist, create the directories too.
		"""

		f = None

		try:
			self.init('file')
			f = open(self.fullpath, *args, **kw)
			with f:
				yield f
		finally:
			pass

	def load(self, mode='rb') -> bytes:
		"""
		# Open the file, and return the entire contents as a &bytes instance.
		# If the file does not exist, an *empty bytes instance* is returned.

		# Unlike &store, this will not initialize the file.
		"""
		if not self.exists():
			return b''

		with self.open(mode) as f:
			return f.read()

	def store(self, data:bytes, mode='wb'):
		"""
		# Given a &bytes instance, &data, store the contents at the location referenced
		# by the &Route. If the file does not exist, *it will be created* along with
		# the leading directories.
		"""
		with self.open(mode) as f:
			return f.write(data)

	@contextlib.contextmanager
	def cwd(self, chdir=os.chdir, getcwd=os.getcwd) -> 'File':
		"""
		# Context manager using the &File route as the current working directory within the
		# context. On exit, restore the current working directory to that the operating system
		# reported:

			#!/pl/python
				root = libroutes.File.from_absolute('/')
				with root.cwd() as oldcwd:
					...

		# The old current working directory is yielded as a &File instance.
		"""

		cwd = getcwd()

		try:
			chdir(self.fullpath)
			yield self.from_absolute(cwd)
		finally:
			chdir(cwd)

class Import(Route):
	"""
	# Route for Python packages and modules.
	"""

	__slots__ = ('context', 'points',)

	@classmethod
	def from_context(Class):
		"""
		# Return a new Route to the package containing the module that is executing
		# &from_context. If the module is a package, a Route to that package is
		# returned.
		"""
		f = sys._getframe()
		while f is not None and f.f_globals['__name__'] == __name__:
			f = f.f_back
		if f is not None:
			return Class.from_fullname(f.f_globals['__package__'])
		return None

	@classmethod
	def from_fullname(Class, s):
		"""
		# Given a valid `__name__`, return an &Import instance to that path.
		"""
		return Class.from_points(None, *s.split('.'))

	@classmethod
	def from_module(Class, module):
		"""
		# Given module containing a valid `__name__`, return an &Import
		# instance to that path.
		"""
		return Class(None, tuple(module.__name__.split('.')))

	@classmethod
	def from_points(Class, context, *points):
		rob = object.__new__(Class)
		rob.__init__(context, points)
		return rob

	@classmethod
	def from_attributes(Class, path, tuple=tuple):
		"""
		# Create a &Route and an attributes sequence based on the given &path such that
		# the &Route is the &real portion of the &path and text following real module
		# path is the sequence of attributes.
		"""
		R = Class.from_fullname(path)
		module = R.real()
		attributes = path[len(str(module))+1:]
		return module, tuple(attributes.split('.') if attributes else ())

	def __bool__(self):
		return any((self.context, self.points))

	def __str__(self):
		return self.fullname

	def __repr__(self):
		return '{0}.{1}.from_fullname({2!r})'.format(__name__, self.__class__.__name__, self.fullname)

	def __contains__(self, abs):
		"""
		# Whether or not the Path contains the given Pointer.
		"""
		return abs.points[:len(self.points)] == self.points

	def __getitem__(self, req):
		return self.__class__(self.context, self.points[req])

	@property
	def fullname(self):
		"""
		# Return the absolute path of the module Route; dot separated module names.
		"""
		# accommodate for Nones
		return '.'.join(self.absolute)

	@property
	def basename(self):
		"""
		# The module's name relative to its package; node identifier used to refer to the module.
		# Alias to &identifier.
		"""

		return self.identifier

	@property
	def package(self):
		"""
		# Return a &Route to the module's package.
		# If the &Route is referencing a package, return &self.

		# ! WARNING:
			# This will be a method.
		"""

		if self.is_container():
			return self

		return self.__class__(self.context, self.points[:-1])

	@property
	def root(self):
		return self.__class__(self.context, self.points[0:1])

	@property
	def loader(self):
		"""
		# The loader of the module.
		"""

		return self.spec().loader

	def spec(self, find_spec=importlib.util.find_spec):
		"""
		# The spec for loading the module.
		"""

		try:
			return find_spec(self.fullname)
		except Exception:
			return None

	def exists(self):
		"""
		# Whether or not the module exists inside the Python paths.
		# However, the module may not be importable.
		"""

		return (self.spec() is not None)

	def is_container(self, find_loader=pkgutil.find_loader):
		"""
		# Interrogate the module's loader as to whether or not it's a "package module".
		"""

		if self.spec() is None:
			return False

		fn = self.fullname
		return find_loader(fn).is_package(fn)
	is_package = is_container

	def real(self):
		"""
		# The "real" portion of the Route.
		# Greatest Absolute Route that *actually exists* on the file system.

		# &None if no parts are real, and &self if the entire route exists.
		"""

		x = self
		while x.points:
			try:
				if x.spec() is not None:
					return x
			except (ImportError, AttributeError):
				pass
			x = x.container

	def get_last_modified(self, stat=os.stat, unix=libtime.unix) -> libtime.Timestamp:
		"""
		# Return the modification time of the module's file as a chronometry Timestamp.
		"""
		return self.file().get_last_modified()
	last_modified = get_last_modified

	def stack(self):
		"""
		# Return a list of module objects. The first being the outermost package module, the
		# last being the module being pointed to, subject module, and the between being the
		# packages leading to the &self.
		"""

		x = self
		r = []

		while (x.context, x.points) != (None, ()):
			mod = x.module()
			if mod is not None:
				r.append(mod)
			x = x.container

		return r

	def scan(self, attribute):
		"""
		# Scan the &stack of modules for the given attribute returning a pair
		# containing the module and the object accessed with the &attribute.
		"""

		modules = self.stack()
		for x in modules:
			if attribute in x.__dict__:
				yield (x, x.__dict__[attribute])

	def floor(self, valids={'project', 'context'}, name='__factor_type__'):
		"""
		# Find the context or project factor for the given module &self.
		"""

		for (mod, value) in self.scan(name):
			if value in valids:
				return self.__class__.from_fullname(mod.__name__)

		return None # No outer modules with __factor_type__.

	def project(self):
		"""
		# Return the 'project' module of the &floor package.
		"""

		f = self.floor()
		if f is not None:
			if f.module().__factor_type__ == 'context':
				return (f/'context'/'project').module()
			else:
				return (f/'project').module()

	def anchor(self):
		"""
		# Anchor the &Import route according to the project's context.
		# This returns a new &Import instance whose &context is the &floor of the module.
		"""
		points = self.absolute
		project = self.floor()
		rel = points[len(project.points):]
		return self.__class__(project, tuple(rel))

	def module(self, trap=True, import_module=importlib.import_module):
		"""
		# Return the module that is being referred to by the path.
		"""

		try:
			return import_module(self.fullname)
		except Exception:
			if trap is True:
				return None
			else:
				raise

	def subnodes(self, iter_modules=pkgutil.iter_modules):
		"""
		# Return a pairs of sequences containing routes to the subnodes of the route.
		"""

		packages = []
		modules = []

		if self.is_package:
			prefix = self.fullname

			# only packages have subnodes
			module = self.module()
			if module is not None:
				path = getattr(module, '__path__', None)
				for (importer, name, ispkg) in iter_modules(path) if path is not None else ():
					path = '.'.join((prefix, name))
					ir = self.__class__.from_fullname(path)

					# Filter entries identified as being a Python module,
					# but are not regular files or do not exist.
					if ir.spec() is None or ir.file().type() != 'file':
						# This applies to package modules as well as
						# the __init__.py file should be available saving
						# a namespace loader.
						continue

					if ispkg:
						packages.append(ir)
					else:
						modules.append(ir)

		return packages, modules

	def tree(self, deque = collections.deque):
		"""
		# Return a package's full tree as a pair of lists.
		"""

		pkgs, mods = self.subnodes()
		tree = {}
		pkgsq = deque(pkgs)

		while pkgsq:
			pkg = pkgsq.popleft()
			sp, pm = pkg.subnodes()

			# extend output
			pkgs.extend(sp)
			mods.extend(pm)

			# process subpackages
			pkgsq.extend(sp)
		return pkgs, mods

	def file(self, from_path=File.from_path, getattr=getattr):
		"""
		# Get the &File instance pointing to the module's file.
		"""

		path = getattr(self.loader, 'path', None)
		if path is None:
			# NamespaceLoader seems inconsistent here.
			return None

		return from_path(path)

	def directory(self):
		"""
		# The package directory of the module.
		"""

		pkg = self.package
		return pkg.file().container

	def cache(self):
		"""
		# The (filesystem:identifier)`__pycache__` directory associated with the module's file.
		"""

		return self.directory() / '__pycache__'
