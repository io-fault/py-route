import os
import sys
from .. import library as lib

def test_equality(test):
	# routes are rather abstract, but we dont want Routes for a given
	# domain to match Routes with equal routing that exist in a distinct domain
	ir = lib.Import(None, ('foo',))
	fr = lib.File(None, ('foo',))
	test/ir.points == fr.points
	test/ir.datum == fr.datum

	# points and datum are identical, but the type needs to be the same as well.
	test/ir != fr

def test_Import(test):
	# ..bit strange when dealing with nested project packages
	fullpath = __package__.split('.')
	localpath = fullpath[fullpath.index('routes'):]
	local = '.'.join(fullpath[:fullpath.index('routes')+1])

	# package.test
	r = lib.Import.from_fullname(__package__)
	# datum reduction
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
	# datum reduction
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

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
