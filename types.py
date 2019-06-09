"""
# Implementation classes for Routes.

# Provides a common base class for selectors and a segment class for out-of-context route management.
"""
from . import core

class Selector(core.PartitionedSequence):
	"""
	# Route domain base class.

	# Subclasses provide access methods to a resource identified
	# by the sequence of identifiers contained within the selector instance.
	"""

class Segment(core.PartitionedSequence):
	"""
	# Sequence of identifiers that may be incorporated into a selector subclass.
	"""

	__slots__ = ('context', 'points',)

	def __str__(self):
		return "(" + (" >> ".join(self.absolute)) + ")"

	def __repr__(self):
		return "%s.%s.from_sequence(%r)" %(__name__, self.__class__.__name__, list(self.absolute))

	@classmethod
	def from_sequence(Class, points):
		return Class(None, tuple(points))

	def __sub__(self, removed:"Segment") -> "Segment":
		n = len(removed)
		if n and self.points[-n:] == removed:
			return self.__class__(self.context, self.points[:-n])
		return self
