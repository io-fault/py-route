"""
# Analyze implementation specific features of &.core.PartitionedSequence and other &.core functions.
"""
from .. import core as module

def test_Route_iterpoints(test):
	root = module.PartitionedSequence(None, ())
	test/list(root.iterpoints()) == []

	x = root / 'first'
	test/list(x.iterpoints()) == ['first']

	x /= 'second'
	test/list(x.iterpoints()) == ['first', 'second']

	# Need at least one check to validate functionality
	# across partitions.
	x = module.PartitionedSequence(x, ('third',))
	test/list(x.iterpoints()) == ['first', 'second', 'third']

def test_Route_iterinverse(test):
	root = module.PartitionedSequence(None, ())
	test/list(root.iterinverse()) == []

	x = root / 'first'
	test/list(x.iterinverse()) == ['first']

	x /= 'second'
	test/list(x.iterinverse()) == list(reversed(['first', 'second']))

	# Need at least one check to validate functionality
	# across partitions.
	x = module.PartitionedSequence(x, ('third',))
	test/list(x.iterinverse()) == list(reversed(['first', 'second', 'third']))

def test_Route_sorting(test):
	root = module.PartitionedSequence(None, ('prefix',))
	mid = module.PartitionedSequence(root, ('path',))
	suffix = module.PartitionedSequence(mid, ('suffix',))
	seq = [
		(suffix/'c'),
		(suffix/'b'),
		(suffix/'a'),
		(suffix/'z'),
	]
	test/seq[0].points[-1] == 'c' # Sanity.

	seq.sort()
	test/seq[0].points[-1] == 'a'
	test/seq[1].points[-1] == 'b'
	test/seq[2].points[-1] == 'c'
	test/seq[3].points[-1] == 'z'

	for x in seq:
		test.isinstance(x, module.PartitionedSequence)

def test_Route_delimit(test):
	Type = module.PartitionedSequence
	prefix = Type(None, ('prefix',)).delimit()
	test/prefix.context.points == ('prefix',)

	r = prefix/'suffix'
	test/r.points == ('suffix',)
	r = r.delimit()
	test/r.points == ()
	test/r.context.points == ('suffix',)

def test_Route_iterpartitions(test):
	Type = module.PartitionedSequence

	prefix = Type(None, ('prefix',))
	test/list(prefix.iterpartitions()) == [('prefix',)]

	prefix = prefix.delimit()
	test/list(prefix.iterpartitions()) == [(), ('prefix',)]

def test_Route_from_partitions(test):
	Type = module.PartitionedSequence

	r1 = Type.from_partitions([
		(),
		('path',)
	])
	test/r1.points == ('path',)
	test/r1.context.points == ()

	r2 = Type.from_partitions([
		(x for x in ()),
		('path' for x in range(1))
	])
	test/r2.points == ('path',)
	test/r2.context.points == ()

	test/r1 == r2

def test_Router_container_skip(test):
	"""
	# Make sure empty contexts are skipped when accessing a route's container.
	"""
	Type = module.PartitionedSequence

	r1 = Type.from_partitions([
		('root',),
		(),
		('path',)
	])
	test/r1.absolute == ('root', 'path',)

	p1 = r1.container
	test/p1.partitions() == [('root',), (), ()] # Only trim when there's a step to take.

	# fully trimmed
	p2 = p1.container
	test/p2.partitions() == [()]

	# root ascent
	p3 = p2.container
	test/p3.partitions() == [()]

def test_Route_pickling(test):
	"""
	# Check python.org/.../pickle support.
	"""
	import pickle
	Type = module.PartitionedSequence

	samples = [
		(),
		('path',),
		('to', 'file'),
	]

	state = []
	for x in samples:
		state.append(x)
		r1 = Type.from_partitions(state)
		r2 = pickle.loads(pickle.dumps(r1))
		test/r1 == r2
		test/r1.partitions() == r2.partitions()

def test_Route_switch(test):
	"""
	# - &module.PartitionedSequence.__mul__
	"""
	Type = module.PartitionedSequence
	root = Type(None, ())

	test/(root*'file') == root/'file'

	path = root / 'directory'
	test/(path*'file') == root/'file'

	path = path.delimit()
	test/(path*'file') == root/'file'

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
