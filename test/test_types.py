"""
# Check the sequence manipulations provided by the base classes.
"""
from .. import types as module

def test_inconsistent_type_equality(test):
	# routes are rather abstract, but we dont want Routes for a given
	# domain to match Routes with equal routing that exist in a distinct domain
	class KRoute(module.Selector):
		pass
	class JRoute(module.Selector):
		pass

	kr = KRoute(None, ('point',))
	jr = JRoute(None, ('point',))

	# Show that points and context are identical.
	test/jr.points == kr.points
	test/jr.context == kr.context

	# Type needs to be identical for comparison.
	test/jr != kr

def test_Route(test):
	"""
	# Test all of the Route base class methods and properties manipulating the context and points.
	"""
	Type = module.Selector
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

def test_Route_path(test):
	"""
	# - &module.Selector.path
	"""
	Type = module.Selector
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

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
