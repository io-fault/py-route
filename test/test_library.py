import os
import sys
from .. import library as lib

def test_equality(test):
	# routes are rather abstract, but we dont want Routes for a given
	# domain to match Routes with equal routing that exist in a distinct domain
	ir = lib.Import(None, ('foo',))
	fr = lib.File(None, ('foo',))
	test/ir.points == fr.points
	test/ir.context == fr.context

	# points and context are identical, but the type needs to be the same as well.
	test/ir != fr

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

	# bottom
	r = lib.Import.from_fullname(__package__)
	test/r.bottom() == lib.Import.from_fullname(local)
	test/r.bottom() == r.bottom().bottom()

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

def test_File_void(test):
	with lib.File.temporary() as t:
		f = t/'doesnotexist'
		test/f.is_container() == False
		test/f.real() != f

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

def test_File_last_modified(test):
	"""
	System check.
	"""
	import time

	with lib.File.temporary() as d:
		r = d / 'last_modified_testfile'
		with r.open('w') as f:
			f.write('data\n')

		test/r.exists() == True

		mtime1 = r.last_modified()
		time.sleep(1.1)
		# sleep one whole second in case the filesystem's
		# precision is at the one second mark.

		with r.open('a') as f:
			f.write('appended\n')

		mtime2 = r.last_modified()

	test/mtime2 > mtime1
	test/mtime1.measure(mtime2) >= lib.libtime.Measure.of(second=1)

def test_File_set_last_modified(test):
	"""
	System check.
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
	&lib.File.since
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
	Test the various classmethods that construct file instances.
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

def test_Import_anchor(test):
	i = lib.Import.from_fullname(__package__)
	i = i.anchor()
	test/i.context == i.bottom()

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
