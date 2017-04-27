import os
import sys
from .. import library as lib

def test_inconsistent_type_equality(test):
	# routes are rather abstract, but we dont want Routes for a given
	# domain to match Routes with equal routing that exist in a distinct domain
	ir = lib.Import(None, ('point',))
	fr = lib.File(None, ('point',))

	# Show that points and context are identical.
	test/ir.points == fr.points
	test/ir.context == fr.context

	# Type needs to be identical for comparison.
	test/ir != fr

def test_Route(test):
	"""
	# Test all of the Route base class methods and properties manipulating the context and points.
	"""
	Type = lib.Route
	root = Type(None, ())
	sub = Type(root, ('first',))
	subsub = Type(sub, ('second',))

	test/subsub.absolute == ('first', 'second')
	test/subsub.identifier == 'second'
	test/subsub.root == subsub.root.root

	test/subsub.container == sub
	test/id(subsub.context) == id(sub)

	# "invert" routes
	test/(~subsub) == subsub
	test/(~subsub).points == ('first', 'second')
	test/(~subsub).context == root
	x = ~subsub
	y = ~x
	test/id(~y) == id(y)

	# Navigation
	x = root / 'd1' / 'd2' / 'f1'
	test/(x * 'null').absolute == (x.container.absolute + ('null',))
	test/(x ** 0) == x
	test/(x ** 1) == x.container
	test/(x ** 2) == x.container.container
	test/(x ** 3) == x.container.container.container

	s3 = subsub / 'third'
	test/s3.absolute == ('first', 'second', 'third')
	s5 = s3.extend(['fourth', 'fifth'])
	test/s5.absolute == ('first', 'second', 'third', 'fourth', 'fifth')
	test/s5.extend([]) == s5

	test/(-s3) == Type(None, ('third', 'second', 'first'))

	# empty points
	empty = Type(s3, ())
	test/empty.container == s3.container
	test/empty.identifier == s3.identifier
	test/root.identifier == None

	# subroute checks
	test/(s5 in s3) == True
	test/(s3 in s5) == False
	test/(s5.container in s3) == True
	test/(s5.container.container in s3) == True
	test/(s3.container in s3) == False
	test/(s3 in s3.container) == True

	# getitem check
	test/s3[0] == 'second'
	test/IndexError ^ (lambda: s3[2])
	test/s5[-1] == 'fifth'
	test/s5[-2] == 'fourth'
	test/s5[:] == ('second', 'third', 'fourth', 'fifth')

	test/(+s5).context.points == (s5.absolute)
	test/(+s5).context.context == None

def test_Route_relative_resolution(test):
	"""
	# Check relative path resolution.
	"""
	Function = lib.Route._relative_resolution
	test/Function(('first', '.', 'second')) == ['first', 'second']
	test/Function(('first', 'second', '..')) == ['first']
	test/Function(('first', 'second', '..', '..')) == []
	test/Function(('first', 'second', '..', '..', '..')) == []

def test_Route_path(test):
	"""
	# Test &lib.Route.path.
	"""
	Type = lib.Route
	common = Type(None, ('prefix', 'common'))
	target = common / 'dir' / 'subdir' / 'target'
	origin = common / 'distinct' / 'path' / 'to' / 'file'

	test/origin >> target == (3, ('dir', 'subdir', 'target'))
	test/target >> origin == (2, ('distinct', 'path', 'to', 'file'))

	local1 = common / 'file-1'
	local2 = common / 'file-2'
	test/local1 >> local2 == (0, ('file-2',))
	test/local2 >> local1 == (0, ('file-1',))

	# now, nothing in common
	outofscope = Type(None, ('file',))
	test/outofscope >> local1 == (0, local1.absolute)

	test/(local1 >> local2) == (local2 << local1)
	test/(origin >> target) == (target << origin)

def test_File(test):
	dir = os.path.dirname(os.path.realpath(__file__))
	r = lib.File.from_absolute(os.path.realpath(__file__))
	test/r.fullpath == os.path.realpath(__file__)
	# context reduction
	test/(~r is r) == True

	rd = r.container
	test/rd.fullpath == dir

	# tail
	end = lib.File.from_absolute('foo')
	test/(rd + end).fullpath == os.path.join(dir, 'foo')

	test/lib.File.from_absolute('/foo/bar.tar.gz').extension == 'gz'

def test_File_repr(test):
	end = lib.File.from_absolute('/test')
	test/repr(end).__contains__('/test') == True

def test_File_bytespath(test):
	p = lib.File.from_absolute('/test/path')
	test/p.bytespath == b'/test/path'

def test_File_which(test):
	test/lib.File.which('cat') / lib.File
	test/lib.File.which('nosuchbin__x__') == None

def test_File_temporary(test):
	path = None
	with lib.File.temporary() as t:
		path = t.fullpath
		test/os.path.exists(path) == True
		test/t.is_container() == True
		test/t.last_modified() != None

	# temporary context over, should not exist.
	test/os.path.exists(path) == False
	test/OSError ^ t.last_modified

def test_File_tree(test):
	"""
	# Test &lib.File.tree and &lib.File.subnodes
	"""

	with lib.File.temporary() as t:
		f = t / 'file'
		f.init('file')
		test/f.subnodes() == ([],[]) # OSError
		test/f.tree() == ([], []) # OSError

		d = t / 'dir'
		s = d / 'subdir'
		l = s / 'file-in-subdir'
		l.init('file')

		expect = ([d, s], [f, l])
		queried = t.tree()
		for x in (expect, queried):
			x[0].sort()
			x[1].sort()

		test/queried == expect

def test_File_real(test):
	"""
	# Test &lib.File.real
	"""
	with lib.File.temporary() as t:
		f = t/'doesnotexist'
		test/f.is_container() == False
		test/f.real() != f

def test_File_replace(test):
	# Regular file replacement.
	with lib.File.temporary() as t:
		src = t / 'srcfile'
		with src.open('wb') as f:
			f.write(b'sources')

		dst = t / 'dstfile'
		with dst.open('wb') as f:
			f.write(b'dest')

		dst.replace(src)
		with dst.open('rb') as f:
			test/f.read() == b'sources'

		src = t / 'srcdir'
		srcfile = src / 's' / 's'
		srcfile.init('file')
		with srcfile.open('wb') as f:
			f.write(b'subdir_sources')

		dst.replace(src)
		test/(dst / 's').exists() == True
		test/(dst / 's' / 's').exists() == True
		dir = dst / 's'
		test/dir.type() == 'directory'
		file = dir / 's'
		with file.open('rb') as f:
			test/f.read() == b'subdir_sources'

def test_File_cwd(test):
	with lib.File.temporary() as t:
		test/os.getcwd() != str(os.path.realpath(str(t)))
		with t.cwd():
			test/os.getcwd() == str(os.path.realpath(str(t)))
			test/str(lib.File.from_cwd()) == os.path.realpath(str(t))

def test_File_init(test):
	"""
	# Test &lib.File.init checking that the parent directories are
	# properly created regardless of the selected type.
	"""

	with lib.File.temporary() as t:
		d = t / 'parent' / 'subdir'
		f = t / 'parent2' / 'subfile'
		p = t / 'parent2' / 'subpipe'

		f.init('file')
		test/f.exists() == True
		test/f.type() == 'file'

		d.init('directory')
		test/d.exists() == True
		test/d.type() == 'directory'

		p.init('pipe')
		test/p.type() == 'pipe'

def test_File_extension(test):
	f = lib.File.from_path('test')
	test/f.extension == None

def test_File_from_home(test):
	hd = lib.File.home()
	test/str(hd) == os.environ['HOME']

def test_File_size(test):
	r = lib.File.from_path(__file__)

	d = r.container / 'test-size-info'

	f1 = d / 'one'
	f2 = d / 'two'
	f3 = d / 'three'
	f4 = d / 'four'
	test/f1.size() == 1
	test/f2.size() == 2
	test/f3.size() == 3
	test/f4.size() == 4

def test_File_get_last_modified(test):
	"""
	# System check.
	"""
	import time

	with lib.File.temporary() as d:
		r = d / 'last_modified_testfile'
		with r.open('w') as f:
			f.write('data\n')

		test/r.exists() == True

		mtime1 = r.get_last_modified()
		time.sleep(1.1)
		# sleep one whole second in case the filesystem's
		# precision is at the one second mark.

		with r.open('a') as f:
			f.write('appended\n')

		mtime2 = r.get_last_modified()

	test/mtime2 > mtime1
	test/mtime1.measure(mtime2) >= lib.libtime.Measure.of(second=1)

def test_File_set_last_modified(test):
	"""
	# System check.
	"""

	with lib.File.temporary() as d:
		r = d / 'last_modified_testfile'
		with r.open('w') as f:
			f.write('data\n')

		test/r.exists() == True
		original_time = r.last_modified()

		ttime = lib.libtime.now().update('minute', -10, 'hour')

		r.set_last_modified(ttime)
		new_time = r.last_modified()

		test/new_time != original_time
		test/new_time.truncate('second') == ttime.truncate('second')

def test_File_since(test):
	"""
	# &lib.File.since
	"""

	with lib.File.temporary() as root:
		f1 = root / 'file1'
		f2 = root / 'file2'
		f3 = root / 'file3'

		files = [f1, f2, f3]
		for x in files:
			x.init('file')

		times = [x.last_modified() for x in files]
		times.sort(reverse=True)
		y = times[0]

		test/list(root.since(lib.libtime.now())) == []

		m = root.since(lib.libtime.now().rollback(minute=1))
		test/set(x[1] for x in m) == set(files)

def test_File_construct(test):
	"""
	# Test the various classmethods that construct file instances.
	"""

	test/str(lib.File.from_absolute('/')) == '/'

	context = lib.File.from_absolute('/no/such/directory')

	test/str(lib.File.from_relative(context, 'file')) == '/no/such/directory/file'
	test/str(lib.File.from_relative(context, './file')) == '/no/such/directory/file'

	test/str(lib.File.from_relative(context, '../file')) == '/no/such/file'
	test/str(lib.File.from_relative(context, '../../file')) == '/no/file'

	# Same directory
	test/str(lib.File.from_relative(context, '../.././././file')) == '/no/file'

	# parent references that find the limit.
	test/str(lib.File.from_relative(context, '../../..')) == '/'
	test/str(lib.File.from_relative(context, '../../../..')) == '/'

	# Smoke test .from_path; two branches that use prior tested methods.
	test/str(lib.File.from_path('./file')) == os.getcwd() + '/file'
	test/str(lib.File.from_path('file')) == os.getcwd() + '/file'
	test/str(lib.File.from_path('/file')) == '/file'

def test_File_basename_manipulations(test):
	with lib.File.temporary() as t:
		f = t/'doesnotexist'
		f_archive = f.suffix('.tar.gz')
		test/f_archive.fullpath.endswith('.tar.gz') == True
		f_test_archive = f.prefix('test_')
		test/f_test_archive.identifier.startswith('test_') == True

def test_File_properties(test):
	# executable
	sysexe = lib.File.from_absolute(sys.executable)
	test/sysexe.executable() == True
	test/sysexe.type() == "file"

	module = lib.File.from_absolute(__file__)
	test/module.executable() == False
	test/module.type() == "file"

	moddir = module.container
	test/moddir.type() == "directory"

def test_File_void(test):
	"""
	# File.void operation.
	"""

	with lib.File.temporary() as d:
		sd = d / 'subdir'
		sf = sd / 'subfile'
		sf.init('file')

		with sf.open('wb') as x:
			x.write(b'data')

		test/sd.exists() == True
		test/sf.exists() == True
		sf.void()
		test/sf.exists() == False
		sf.init('file')
		test/sf.exists() == True

		sd.void()
		test/sd.exists() == False
		test/sf.exists() == False

def test_File_link(test):
	"""
	# Test &lib.File.symbolic_link.
	"""
	with lib.File.temporary() as t:
		target = t / 'file'
		with target.open('wb') as f:
			f.write(b'test file')

		# Relative Mode
		sym = t / 'symbolic'
		test/sym.exists() == False
		sym.link(target)
		test/sym.exists() == True
		with sym.open('rb') as f:
			test/f.read() == b'test file'

		common = t / 'dir' / 'subdir'
		common.init('directory')
		dst = common / 'from-1' / 'from-2' / 'file'
		src = common / 'to-1' / 'to-2' / 'to-3' / 'file'
		src.init('file')

		with src.open('wb') as f:
			f.write(b'source data')

		dst.init('file')
		dst.void()
		dst.link(src)
		with dst.open('rb') as f:
			test/f.read() == b'source data'

def test_File_recursive_since(test):
	"""
	# &lib.File.since with recursive directories.
	"""
	import itertools
	ago10mins = lib.libtime.now().rollback(minute=10)
	thirty = lib.libtime.now().rollback(minute=30)

	with lib.File.temporary() as t:
		d = t / 'dir' / 'subdir'
		f = d / 'file'
		f.init('file')
		for r in itertools.chain(*t.tree()):
			r.set_last_modified(thirty)

		f.set_last_modified(ago10mins)

		# create recursion
		l = d / 'link'
		l.link(t / 'dir')
		test/list(t.since(ago10mins.rollback(minute=10)))[0][1] == f

def test_Import(test):
	# ..bit strange when dealing with nested project packages
	fullpath = __package__.split('.')
	localpath = fullpath[fullpath.index('routes'):]
	local = '.'.join(fullpath[:fullpath.index('routes')+1])

	# package.test
	r = lib.Import.from_fullname(__package__)
	# context reduction
	test/(~r is r) == True

	# crawl stack; closest package module is chosen
	test/lib.Import.from_context() == r

	test/r.fullname == '.'.join((__package__, ))
	test/r.module() == sys.modules[__package__]
	test/r.container.module() == sys.modules['.'.join(__package__.split('.')[:-1])]

	# stack
	r = lib.Import.from_fullname(__package__)
	modules = r.stack()
	test/len(modules) >= len(fullpath)

	test/modules[0] == r.module() # most "significant" module first
	for x in modules:
		test/x == r.module()
		r = r.container

	# floor
	r = lib.Import.from_fullname(__package__)
	test/r.floor() == lib.Import.from_fullname(local)
	test/r.floor() == r.floor().floor()

	# project
	from .. import project
	r = lib.Import.from_fullname(__package__)
	test/r.project() == project
	test/r.last_modified() != None

	# module that does not exist
	r = lib.Import.from_fullname('+++++nosuch_module')
	test/r.module() == None
	test/r.root == r

	# real resolution
	r = lib.Import.from_fullname(__package__ + '.' + '+++++nosuch_module')
	test/r.module() == None
	test/r.real() == lib.Import.from_fullname(__package__)

def test_Import_anchor(test):
	i = lib.Import.from_fullname(__package__)
	i = i.anchor()
	test/i.context == i.floor()

def test_Import_from_attributes(test):
	mod, attr = lib.Import.from_attributes(__package__)
	test/mod == lib.Import.from_fullname(__package__)
	test/attr == ()

def test_Import_tree(test):
	pkg = lib.Import.from_fullname(__package__)
	project = pkg.floor()
	pkgs, mods = map(set, project.tree())

	test/((project/'test') in pkgs) == True
	test/((project/'documentation') in pkgs) == True
	test/((project/'library') in mods) == True

def test_Import_get_last_modified(test):
	# This is essentally the implementation; the method is mere convenience.
	pkg = lib.Import.from_fullname(__package__)
	test/pkg.file().get_last_modified() == pkg.get_last_modified()

def test_Import_subnodes(test):
	"""
	# Test the filtering and functionality of &library.Import.subnodes.
	"""
	test.skip("not implemented")

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
