"""
# Implementation of the route base class and route tools.

# The primary class, &PartitionedSequence, is essentially a unrolled linked list
# leveraging Python's reference counting to allow sharing of routes and segments
# across instances.
"""
import functools
import typing

from ..context.tools import cachedcalls, consistency

# Type signature for identifiers used by &Selector and &Segment instances.
Identifier = typing.Hashable

# Reduction for often re-used PartitionedSequence.points
def vcombine(*args):
	return args
partition_cache = cachedcalls(32)(vcombine)

def join(head, tail):
	return partition_cache(*head, *tail)
absolute_cache = cachedcalls(64)(join)

@cachedcalls(32)
def construct_cache(Class, context, points):
	return Class(context, points)

def map_partitions(parts):
	# Utility for mapping absolute indexes to partitioned indexes
	i = 0
	for p in parts:
		yield from ((i, x) for x in range(len(p)))
		i += 1

def relative_path(target, source) -> (int, int, typing.Sequence[Identifier]):
	# Produce information for forming a relative path.
	# PartitionedSequence specific details; used by correlate and segment.
	if source.context is target.context:
		from_path = source.points
		target_path = target.points
	else:
		from_path = source.absolute
		target_path = target.absolute

	cl = consistency(from_path, target_path)

	return cl, len(from_path), target_path

@functools.total_ordering
class PartitionedSequence(object):
	"""
	# Route implementation class managing the path as a partitioned sequence.

	# The stored sequences are usually tuples that are connected to a Context
	# instance defining the preceeding points in the path. The intent of the
	# structure is to allow path sharing for reducing memory use when working
	# with long paths. However, this is not done automatically and the exact
	# usage must be aware of how &context can eliminate redundant leading segments.
	"""

	def correlate(self, target) -> typing.Tuple[int, typing.Sequence[Identifier]]:
		"""
		# The relative positioning of &self with respect to &target.
		# Provides the necessary information to form a relative path to &target from &self.

		# Returns the number of steps to ascend and the sequence of identifiers to apply in
		# order to arrive at &target.
		"""
		cl, l, path = relative_path(target, self)
		asecent = l - cl
		segment = path[cl:]

		return (asecent, segment)

	@classmethod
	def from_sequence(Class, points, context=None, chunksize=4):
		r = None

		for i in range(0, len(points), chunksize):
			r = Class(context, partition_cache(*points[i:i+chunksize]))
			context = r

		return r if r is not None else Class(None, ())

	# Partition Interfaces

	@classmethod
	def from_partitions(Class, parts:typing.Iterable[typing.Tuple[Identifier]], context=None):
		"""
		# Construct a new instance from an iterable of partitions in root order.
		"""
		for points in parts:
			context = construct_cache(Class, context, partition_cache(*points))

		return context if context is not None else construct_cache(Class, None, ())

	def from_context(self, *paths:Identifier):
		"""
		# Construct a new route relative to &self.context.
		"""
		return self.__class__(self.context, paths)

	def delimit(self):
		"""
		# Create a new partitioned sequence designating &self as the context.

		# If the context-relative path of &self is an empty sequence, &self is returned exactly.
		"""
		if self.points:
			return self.__class__(self, ())
		else:
			return self

	def iterpartitions(self):
		"""
		# Produce the *partitions* of the sequence in inverse order.

		# The identifiers *inside* the partitions will be in root order.
		"""
		x = self
		while x.context is not None:
			yield x.points
			x = x.context
		yield x.points

	def partitions(self, list=list):
		"""
		# Construct a sequence of partitions in root order.
		# Result is a suitable parameter for &from_partitions.
		"""
		l = list(self.iterpartitions())
		l.reverse()
		return l

	def __init__(self, context, points:typing.Tuple[Identifier]):
		self.context = context
		self.points = points

	def __repr__(self):
		return "%s.from_partitions(%r)" %(self.__class__.__name__, self.partitions())

	def __reduce__(self):
		return (self.from_partitions, (self.partitions(),))

	def __hash__(self):
		"""
		# Hash on the &absolute of the Route allowing consistency regardless of context.
		"""
		return hash(self.absolute)

	def __eq__(self, operand, isinstance=isinstance):
		"""
		# Whether the absolute points of the two Routes are consistent.
		"""

		if isinstance(operand, self.__class__):
			if self.context is operand.context:
				return self.points == operand.points

			# Compare absolute
			return self.absolute == operand.absolute

	def __lt__(self, operand, isinstance=isinstance):
		if isinstance(operand, self.__class__):
			if self.context is operand.context:
				return self.points < operand.points

			return self.absolute < operand.absolute

	# Sequence Interfaces

	def __len__(self):
		return sum(map(len, self.iterpartitions()))

	def __iter__(self) -> typing.Iterator[Identifier]:
		for p in self.partitions():
			yield from p

	def __contains__(self, operand):
		for p in self.iterpartitions():
			if operand in p:
				return True

		return False

	def __getitem__(self, req):
		return self.absolute[req]

	def __add__(self, tail:typing.Iterable[Identifier], list=list):
		"""
		# Add the two Routes together maintaining the context of the first.
		"""
		t = list(tail)
		if t:
			return self.__class__(self.context, partition_cache(*self.points, *t))
		else:
			return self

	def extend(self, extension):
		# Deprecating.
		return self + extension

	# Route Interfaces

	def __xor__(self, operand):
		ascent, segment = self.correlate(operand)

		x = self
		for i in range(ascent):
			yield x
			x = x.container

		yield x

		path = []
		for y in segment:
			path.append(y)
			yield x + path

	def __truediv__(self, identifier:Identifier):
		"""
		# Append the operand, &identifier, to the route.
		"""
		return self.__class__(self.context, self.points + (identifier,))

	def __floordiv__(self, route):
		"""
		# Extend the route using a route operand.
		# Maintains partitioning of &route.
		"""
		if isinstance(route, PartitionedSequence):
			return self.from_partitions(route.partitions(), context=self)

		return NotImplemented

	def __matmul__(self, segment):
		"""
		# Iterate over segment and return the combined path at those points added on &self.
		"""
		path = []
		for x in segment.iterpoints():
			path.append(x)
			yield self + path

	def __mul__(self, replacement:Identifier):
		"""
		# Route (final) suffix substitution.
		"""
		return self.__class__(self.context, partition_cache(*self.points[:-1], replacement))

	def __pow__(self, strip:int, range=range):
		"""
		# Select the n-th ancestor of the route preserving context.
		# Returns a new route.
		"""
		if strip < 0:
			strip = len(self) + strip

		y = self
		# This is not efficient, but it preserves the partitions.
		for x in range(strip):
			y = y.container
		return y

	def iterpoints(self):
		"""
		# Iterate the identifiers that make up the route in root order.
		"""

		x = self
		seq = []
		add = seq.append
		while x.context is not None:
			add(x.points)
			x = x.context
		add(x.points)

		for i in reversed(seq):
			yield from i
	__route__ = iterpoints

	def iterinverse(self):
		"""
		# Iterate the identifiers that make up the route in inverse order.
		"""

		x = self
		while x.context is not None:
			yield from reversed(x.points)
			x = x.context

		yield from reversed(x.points)

	@property
	def absolute(self):
		"""
		# The absolute sequence of points.
		"""

		r = self.points
		x = self
		while x.context is not None:
			r = absolute_cache(x.context.points, r)
			x = x.context
		return r

	@property
	def identifier(self):
		"""
		# The final identifier in the sequence.
		"""

		if self.points:
			return self.points[-1]
		else:
			if self.context is not None:
				return self.context.identifier
			return None

	@property
	def root(self):
		"""
		# The root &PartitionedSequence with respect to the Route's context.
		"""

		return self.__class__(self.context, partition_cache(*self.points[0:1]))

	@property
	def container(self):
		"""
		# Return a Route to the outer (parent) Route; this merely removes the last point in the
		# sequence trimming the &context when necessary.
		"""
		ctx = self.context
		p = self.points

		while not p and ctx is not None:
			p = ctx.points
			ctx = ctx.context

		return self.__class__(ctx, partition_cache(*p[:-1]))
