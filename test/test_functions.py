"""
# Check utility functions present in &.__init__.
"""
from .. import rewrite as module

def test_rewrite_relative(test):
	"""
	# Check relative path resolution.
	"""
	Function = module.relative
	test/Function(('first', '.', 'second')) == ['first', 'second']
	test/Function(('first', 'second', '..')) == ['first']
	test/Function(('first', 'second', '..', '..')) == []
	test/Function(('first', 'second', '..', '..', '..')) == []

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
