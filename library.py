"""
Routes is a library for manipulating paths to arbitrary "things".
The paths are normally routes to a File or Import, Python module.

Routes have a dual purpose: point to a "thing", and interact with the "thing".
The conflation is strictly for convenience.
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

from . import abstract

from ..chronometry import library as time

class File(abstract.Route):
	"""
	Route subclass for file system objects.
	"""
	__slots__ = ('datum', 'points',)

	@classmethod
	def from_absolute(typ, s, sep = os.path.sep):
		return typ(None, tuple([x for x in s.split(sep) if x]))

	@classmethod
	def home(typ):
		"""
		Return a new Route to the "HOME" directory defined by the environment.

		The returned Route's `datum` is the HOME path.
		"""
		return typ(typ.from_absolute(os.environ['HOME']), ())

	@classmethod
	def cwd(typ, getcwd = os.getcwd):
		"""
		Return a new Route to the current working directory.

		The returned Route's `datum` is the current working directory path.
		"""
		return typ(typ.from_absolute(getcwd()), ())

	@classmethod
	def from_path(typ, s, realpath = os.path.realpath, dirname = os.path.dirname):
		"""
		Return a new Route to the current working directory.

		The returned Route's `datum` is the current working directory path.
		"""
		rp = realpath(s)
		dn = dirname(rp)
		return typ(typ.from_absolute(dn), (rp[len(dn):],))

	@classmethod
	@contextlib.contextmanager
	def temporary(typ):
		with tempfile.TemporaryDirectory() as d:
			yield typ(typ.from_absolute(d), ())

	@classmethod
	def which(typ, exe, dirname = os.path.dirname):
		"""
		Return a new Route the executable found by which.
		"""
		rp = shutil.which(exe)
		dn = dirname(rp)
		return typ(typ.from_absolute(dn), (rp[len(dn)+1:],))

	def __repr__(self):
		return '{0}.{1}.from_absolute({2!r})'.format(__name__, self.__class__.__name__, self.fullpath)

	def __str__(self):
		return self.fullpath

	@property
	def fullpath(self, sep = os.path.sep):
		if self.datum is not None:
			# let the outermost datum handle the root /, if any
			prefix = self.datum.fullpath
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
	def bytespath(self, encoding = sys.getfilesystemencoding()):
		return self.fullpath.encode(encoding, "surrogateescape")

	def suffix(self, s):
		"""
		Modify the name of the file adding the given suffix.

		Returns a new Route.
		"""
		*prefix, basename = self.points
		prefix.append(basename + s)
		return self.__class__(self.datum, tuple(prefix))

	def prefix(self, s):
		"""
		Modify the name of the file adding the given prefix.

		Returns a new Route.
		"""
		*prefix, basename = self.points
		prefix.append(s + basename)
		return self.__class__(self.datum, tuple(prefix))

	_type_map = {
			stat.S_IFIFO: 'pipe',
			stat.S_IFSOCK: 'socket',
			stat.S_IFLNK: 'link',
			stat.S_IFDIR: 'directory',
			stat.S_IFREG: 'file',
			stat.S_IFBLK: 'device',
			stat.S_IFCHR: 'device',
	}
	def type(self, ifmt = stat.S_IFMT, stat = os.stat, type_map = _type_map):
		s = stat(self.fullpath)
		return type_map[ifmt(s.st_mode)]

	def is_container(self, isdir = os.path.isdir):
		return isdir(self.fullpath)

	def subnodes(self, listdir = os.listdir, isdir = os.path.isdir, join = os.path.join):
		"""
		Return a pair of lists, the first being a list of Routes to
		directories in this Route and the second being a list of Routes to non-directories
		in this Route.

		If the Route does not point to a directory, a pair of empty lists will be returned.
		"""
		path = self.fullpath

		try:
			l = listdir(self.fullpath)
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

	def real(self, exists = os.path.exists):
		"""
		Return the part of the File route that actually exists on the File system.
		"""
		x = self.__class__.from_absolute(self.fullpath)
		while x.points:
			if exists(x.fullpath):
				return x
			x = x.container

	def exists(self, exists = os.path.exists):
		"""
		Return the part of the File route that actually exists on the File system.
		"""
		return exists(self.fullpath)

	def size(self, listdir = os.listdir):
		"""
		Return whether or not the file or directory has contents.
		"""
		if not self.exists():
			return None

		if self.is_container():
			return len(listdir(self.fullpath))
		else:
			with self.open(mode='rb') as f:
				f.seek(0, 2)
				return f.tell()

	def void(self, rmtree = shutil.rmtree, remove = os.remove):
		"""
		Remove the entire tree that this Route points to.
		No file will survive. Unless it's not owned by the user.
		"""
		if self.is_container():
			rmtree(self.fullpath)
		elif self.exists():
			remove(self.fullpath)

	def replace(self, route):
		"""
		Drop the existing node and replace it with the file or directory at the
		given route
		"""
		if self.void():
			try:
				shutil.copytree(route.fullpath, self.fullpath)
				return True
			except OSError:
				pass
		return False

	def last_modified(self, stat = os.stat, unix = time.unix):
		return unix(stat(self.fullpath).st_mtime)

	def init(self, type, mkdir = os.mkdir, exists = os.path.exists):
		"""
		init(type)

		Create the filesystem node described by the type parameter at this route.
		Any directories leading up to the node will be automatically created if
		they do not exist.

		If a node of any type already exists at this route, nothing happens.

		`type` is one of: :py:obj:`'file'`, :py:obj:`'container'`, :py:obj:`'pipe'`.
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
		Open the file pointed to by the route.

		If the file doesn't exist, create it; if the directories
		leading up to the file don't exist, create the directories too.
		"""
		f = None
		try:
			self.init('file')
			f = open(self.fullpath, *args, **kw)
			with f:
				yield f
		finally:
			pass

class Import(abstract.Route):
	"""
	Route for Python packages and modules.
	"""
	__slots__ = ('datum', 'points',)

	@classmethod
	def from_context(typ):
		"""
		Return a new Route to the package containing the module that is executing
		:py:meth:`from_context`. If the module is a package, a Route to that package is
		returned.
		"""
		f = sys._getframe()
		while f is not None and f.f_globals['__name__'] == __name__:
			f = f.f_back
		if f is not None:
			return typ.from_fullname(f.f_globals['__package__'])
		return None

	@classmethod
	def from_fullname(typ, s):
		"""
		Given an absolute module path, return a Pointer instance to that path.
		"""
		return typ.from_points(None, *s.split('.'))

	@classmethod
	def from_points(typ, datum, *points):
		rob = object.__new__(typ)
		rob.__init__(datum, points)
		return rob

	def __str__(self):
		return self.fullname

	def __repr__(self):
		return '{0}.{1}.from_fullname({2!r})'.format(__name__, self.__class__.__name__, self.fullname)

	def __contains__(self, abs):
		"""
		Whether or not the Path contains the given Pointer.
		"""
		return abs.points[:len(self.points)] == self.points

	def __getitem__(self, req):
		return self.__class__(self.datum, self.points[req])

	@property
	def fullname(self):
		"""
		Return the absolute path of the Pointer.
		"""
		# accommodate for Nones
		return '.'.join(self.points)

	@property
	def basename(self):
		"""
		The module's name relative to its package.
		"""
		return self.points[-1]

	@property
	def package(self):
		"""
		Return a Pointer to the module's package.
		If the Pointer is referencing a package, return the object.
		"""
		if self.is_container():
			return self
		return self.__class__(self.datum, self.points[:-1])

	@property
	def root(self):
		return self.__class__(self.datum, self.points[0:1])

	@property
	def container(self):
		"""
		Return a Pointer to the containing package. (parent package module)
		"""
		return self.__class__(self.datum, self.points[:-1])

	@property
	def loader(self, find_loader = pkgutil.find_loader):
		return find_loader(self.fullname)

	def is_container(self, find_loader = pkgutil.find_loader):
		"""
		Interrogate the module's loader as to whether or not it's a "package module".
		"""
		fn = self.fullname
		return find_loader(fn).is_package(fn)
	is_package = is_container

	def real(self, find_loader = pkgutil.find_loader):
		"""
		The "real" portion of the Route.
		Greatest Absolute Route that actually exists.

		None if no parts are real.
		"""
		x = self
		while x.points:
			if find_loader(x.fullname):
				return x
			x = x.container

	def last_modified(self, stat = os.stat, unix = time.unix):
		"""
		Return the modification time of the module in a rhythm Timestamp.
		"""
		return unix(stat(self.module().__file__).st_mtime)

	def scan(self, attr):
		"""
		Scan the :py:meth:`stack` of modules for the given attribute returning a pair
		containing the module the object at that attribute.
		"""
		modules = self.stack()
		for x in modules:
			if attr in x.__dict__:
				yield (x, x.__dict__[attr])

	def bottom(self, valids = (True, False), name = '__pkg_bottom__'):
		"""
		Return a Route to the package module containing an attribute named
		'__pkg_bottom__' whose value is :py:obj:`True` or :py:obj:`False`.
		"""
		for (mod, value) in self.scan(name):
			if value in valids:
				return self.__class__.from_fullname(mod.__name__)
		return None # no bottom

	def project(self):
		"""
		Return the "project" module of the :py:meth:`bottom` package.
		"""
		bottom = self.bottom()
		if bottom is not None:
			return (bottom/'project').module()

	def module(self, import_module = importlib.import_module):
		"""
		Return the module that is being referred to by the path.
		"""
		fn = self.fullname
		ld = self.loader
		if ld is None:
			# module does not exist
			return None
		return ld.load_module(fn)

	def stack(self):
		"""
		Return a list of module objects. The first being the outermost package module, the
		last being the module being pointed to, subject module, and the between being the
		packages leading to the subject.
		"""
		x = self
		r = []
		while x.points:
			mod = x.module()
			if mod is None:
				return None
			r.append(mod)
			x = x.container
		return r

	def subnodes(self, iter_modules = pkgutil.iter_modules):
		"""
		subnodes()

		Return two pairs of sequences containing pointers to the subnodes of the Pointer.
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
					if ispkg:
						packages.append(ir)
					else:
						modules.append(ir)

		return packages, modules

	def tree(self, deque = collections.deque):
		"""
		tree()

		Return a package full tree.
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

	def file(self, from_path = File.from_path):
		"""
		Get the :py:class:`File` instance pointing to the module.
		"""
		path = getattr(self.loader, 'path', None)
		if path is None:
			# NamespaceLoader seems inconsistent here.
			path = self.loader._path._path
		return from_path(path)
