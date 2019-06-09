"""
# Check the sequence manipulations provided by the base classes.
"""
from .. import core as module

def test_Route_relative_resolution(test):
	"""
	# Check relative path resolution.
	"""
	Function = module.PartitionedSequence._relative_resolution
	test/Function(('first', '.', 'second')) == ['first', 'second']
	test/Function(('first', 'second', '..')) == ['first']
	test/Function(('first', 'second', '..', '..')) == []
	test/Function(('first', 'second', '..', '..', '..')) == []

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
