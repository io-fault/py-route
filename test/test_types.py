"""
# Check the sequence manipulations provided by the base classes.
"""
from . import module

def test_inconsistent_type_equality(test):
	# routes are rather abstract, but we dont want Routes for a given
	# domain to match Routes with equal routing that exist in a distinct domain
	class KRoute(module.Selector):
		pass
	class JRoute(module.Selector):
		pass

	kr = KRoute(None, ('point',))
	jr = JRoute(None, ('point',))

	# Show that points are identical.
	test/jr.context == None
	test/kr.context == None
	test/jr.points == kr.points

	# Type needs to be identical for comparison.
	test/jr != kr

def test_Route_operations(test):
	"""
	# Check route specific operators
	"""
	Type = module.Selector
	Delta = module.Segment

	root = Type(None, ())
	sub = Type(root, ('first',))
	test/len(sub) == 1

	subsub = Type(sub, ('second',))
	test/len(subsub) == 2

	test/subsub.absolute == ('first', 'second')
	test/subsub.identifier == 'second'
	test/subsub.root == subsub.root.root

	test/subsub.container == sub
	test/id(subsub.context) == id(sub)

	# Navigation
	x = root / 'd1' / 'd2' / 'f1'
	test/len(x) == 3
	test/(x * 'null').absolute == (x.container.absolute + ('null',))
	test/(x ** 0) == x
	test/(x ** 1) == x.container
	test/(x ** 2) == x.container.container
	test/(x ** 3) == x.container.container.container

	s3 = subsub / 'third'
	test/s3.absolute == ('first', 'second', 'third')
	s5 = s3 + ['fourth', 'fifth']
	test/s5.absolute == ('first', 'second', 'third', 'fourth', 'fifth')
	test/(s5 + []) == s5

	# empty points
	empty = Type(s3, ())
	test/empty.container == s3.container
	test/empty.identifier == s3.identifier
	test/root.identifier == None

def test_Route_sequence(test):
	Type = module.Selector

	# subroute checks
	parts = [
		('root',),
		('path', 'to', 'context'),
		('target',),
	]
	s = [
		Type.from_partitions(parts[0:i])
		for i in range(1, len(parts)+1)
	]
	for x in s:
		test/('root' in x) == True
		test/('no-such-identifier' in x) == False
		test/x[0] == 'root'

	for x in s[1:]:
		test/('to' in x) == True
		test/x[1] == 'path'
		test/x[2] == 'to'
		test/x[3] == 'context'

	test/IndexError ^ (lambda: s[0][1])
	test/s[2][:] == ('root', 'path', 'to', 'context', 'target')

def test_Route_addition(test):
	"""
	# - &module.Selector
	"""
	Type = module.Selector
	Con = Type.from_sequence

	root = Con(())
	test/(root + ['first']) == Con(['first'])
	test/(root + []) == Con([])

	for i in range(16):
		fullpath = list(range(i))
		cat = root + fullpath
		test/list(cat.absolute) == fullpath

def test_Route_plural_division(test):
	"""
	# Validate `r//segment` operations.
	"""
	Selector = module.Selector
	Segment = module.Segment
	Con = Selector.from_sequence

	sel = Selector(None, ('prefix', 'common'))
	seg = Segment(None, ('suffix',))

	extended = sel // seg
	test/extended == Con(['prefix', 'common', 'suffix'])
	test.isinstance(extended, type(sel))

	seg /= 'terminal'
	extended = sel // seg
	test/extended == Con(['prefix', 'common', 'suffix', 'terminal'])
	test.isinstance(extended, type(sel))

	seg = Segment.from_sequence([])
	extended = sel // seg
	test/extended == sel
	test.isinstance(extended, type(sel))

def test_Route_index_keys(test):
	Selector = module.Selector
	v1 = Selector(None, ('root', 'path', 'target'))
	v2 = Selector(Selector(None, ('root',)), ('path', 'target'))

	test/(v1 in {v2:1}) == True
	test/(v2 in {v1:1}) == True
	test/({v2:1})[v1] == 1
	test/({v1:2})[v2] == 2

def test_Route_segment(test):
	p = module.Selector(None, ('prefix',))

	s = p / 'suffix'
	test/list(s.segment(p)) == ['suffix']

	# p is not in s
	test/list(p.segment(s)) == []

	s = p / 'segment-1' / 'segment-2'
	s.delimit()
	s /= 'segment-3'
	s /= 'target'
	test/list(s.segment(p)) == ['segment-1', 'segment-2', 'segment-3', 'target']

def test_Route_stepwise_shift(test):
	root = module.Selector.from_partitions([
		('root',),
	])
	s1 = module.Segment.from_partitions([
		('prefix', 'stem-1'),
		('path', 'to', 'target'),
	])
	p1 = module.Selector.from_partitions([
		('root',),
		('prefix', 'stem-1'),
		('path', 'to', 'target'),
	])

	test/(root // s1) == p1

	steps = list(root >> s1)
	x = p1
	y = list(steps) # copy
	while y:
		test/list(x) == list(y[-1])
		x = x.container
		del y[-1:]

	steps.reverse()
	test/list(root << s1) == steps

def test_Route_stepwise_ascent(test):
	root = module.Selector.from_partitions([])
	p1 = module.Selector.from_partitions([
		('root',),
		('prefix', 'stem-1'),
		('path', 'to', 'target'),
	])
	s1 = p1.segment()

	steps = list(root << s1)
	test/steps == list(~p1)

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
