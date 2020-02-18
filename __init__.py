"""
# Route data structures and protocols.
"""
import typing
import itertools
from . import core

Identifier = core.Identifier
consistency = core.consistency

def relative_resolution(
		points:typing.Tuple[Identifier],
		delta=({'':0, '.':0, '..':1}).get
	):
	"""
	# Resolve relative accessors within the confines of &points.
	"""
	r = []
	add = r.append
	change = 0

	for x in points:
		a = delta(x)
		if a is not None:
			change += a
		else:
			if change:
				# Apply ascent.
				del r[-change:]
				change = 0
			add(x)
	else:
		if change:
			del r[-change:]

	return r

class Segment(core.PartitionedSequence):
	"""
	# Sequence of identifiers that may be incorporated into a selector subclass.
	"""

	__slots__ = ('context', 'points',)

	def __str__(self):
		parts = ["->".join(x) for x in self.iterpartitions()]
		return ''.join("(" + x + ")" for x in parts)

	def __bool__(self):
		"""
		# True is the segment has any points; False if zero.
		"""
		for x in self.iterpartitions():
			if x:
				return True

		return False

	def segment(self, from_stem=None,
			Cache=core.construct_cache,
			RPath=core.relative_path,
		):
		if self.context is from_stem:
			return Cache(self.__class__, None, self.points)
		elif from_stem is None:
			return self

		cl, l, seg = RPath(self, from_stem)
		if cl < l:
			# Outside of stem.
			return Cache(self.__class__, None, ())

		return self.__class__(None, seg[cl:])

class Selector(core.PartitionedSequence):
	"""
	# Route domain base class.

	# Subclasses provide access methods to a resource identified
	# by the sequence of identifiers contained within the selector instance.
	"""

	def segment(self, from_stem=None,
			Segment=Segment,
			Cache=core.construct_cache,
			RPath=core.relative_path,
		) -> Segment:
		"""
		# Construct a &Segment from &self starting at the position designated by &from_stem.
		# If stem is not given, the entire selector will be converted.
		"""
		if self.context is from_stem:
			return Cache(Segment, None, self.points)
		elif from_stem is None:
			return Segment.from_partitions(self.partitions())

		cl, l, seg = RPath(self, from_stem)
		if cl < l:
			# Outside of stem.
			return Cache(Segment, None, ())

		return Segment(None, seg[cl:])

	def __str__(self):
		parts = ["/".join(x) for x in self.iterpartitions()]
		return ''.join("[" + x + "]" for x in parts)

	def __bool__(self):
		# Subclasses with another opinion on selector truth should override.
		return True

	_relative_resolution = staticmethod(relative_resolution)
