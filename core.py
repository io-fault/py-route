"""
# Implementation of the concrete base classes for working with Routes.

# The primary class, &PartitionedSequence, is essentially a unrolled linked list
# leveraging Python's reference counting to allow sharing of routes and segments
# across instances.
"""
import functools
import operator
import itertools

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

	def __init__(self, context:"PartitionedSequence", points:tuple):
		self.context = context
		self.points = points

	def __pos__(self):
		"""
		# Return a new equivalent instance with a context depth of 1 so
		# that the new Route's context contains all the points of the
		# original Route.
		"""

		context = self.__class__(None, self.absolute)
		return self.__class__(context, ())

	def __rshift__(self, target, predicate=operator.eq,
			takewhile=itertools.takewhile,
			zip=zip,
			sum=sum,
			len=len,
		) -> (int, tuple):
		"""
		# Construct a sequence of points identifying the &target relative to &self.

		# Essentially, find the common prefix and note the number of containers between
		# it and &self. Subsequently, get the points necessary to select the target from
		# that common prefix.
		"""

		target_path = target.absolute
		from_path = self.absolute

		i = takewhile(True.__eq__, itertools.starmap(predicate, zip(target_path, from_path)))
		top = sum(1 for x in i)
		containers = len(from_path) - top - 1

		return containers, tuple(target_path[top:])

	def __lshift__(self, target):
		"""
		# Parameter inversion of &__rshift__.
		"""
		return target >> self

	def __hash__(self):
		"""
		# Hash on the &absolute of the Route allowing consistency regardless of context.
		"""
		return hash(self.absolute)

	def __eq__(self, ob, isinstance=isinstance):
		"""
		# Whether the absolute points of the two Routes are consistent.
		"""

		if isinstance(ob, self.__class__):
			return self.absolute == ob.absolute

	def __lt__(self, ob, isinstance=isinstance):
		if isinstance(ob, self.__class__):
			return self.absolute < ob.absolute

	def __contains__(self, subject):
		if subject.context is self:
			# Context based fast path.
			return True

		# Resolve absolute and check common prefix.
		sab = self.absolute
		sub = subject.absolute
		return sub[:len(sab)] == sab

	def __getitem__(self, req):
		"""
		# Select slices and items from the *relative* &points.
		# Points inside the &context will not be accessible.
		"""

		return self.points[req]

	def __add__(self, tail):
		"""
		# Add the two Routes together maintaining the context of the first.

		# Maintains the invariant: `x+y == x.extend(y.absolute)`.
		"""
		return tail.__class__(self.context, self.points + tail.absolute)

	def __truediv__(self, next_point):
		"""
		# Extend the Route by one point.
		"""
		return self.__class__(self.context, self.points + (next_point,))

	def __mul__(self, replacement):
		"""
		# Select a node adjacent to the current selection.

		# Returns a new &Route.
		"""
		return self.container / replacement

	def __pow__(self, ancestor:int, range=range):
		"""
		# Select the n-th ancestor of the route.

		# Returns a new &Route.
		"""

		y = self
		# This is not efficient, but it allows the preservation
		# of the context.
		for x in range(ancestor):
			y = y.container
		return y

	def extend(self, extension):
		"""
		# Extend the Route using the given sequence of points.
		"""

		return self.__class__(self.context, self.points + tuple(extension))

	def __neg__(self):
		"""
		# Return a new &Route with &self's absolute points reversed.
		# The &context is not maintained in the returned instance.

		# ! WARNING:
			# Tentative interface.
		"""

		return self.__class__(None, tuple(reversed(self.absolute)))

	def __invert__(self):
		"""
		# Consume one context level into a new Route. The invariant, `self == ~self`, holds;
		# If the &context is &None, &self will be returned.
		"""

		if self.context is None:
			return self

		return self.__class__(self.context.context, self.context.points + self.points)

	@property
	def absolute(self):
		"""
		# The absolute sequence of points.
		"""

		r = self.points
		x = self
		while x.context is not None:
			r = x.context.points + r
			x = x.context
		return r

	@property
	def relative(self):
		"""
		# The sequence of points relative to the context.
		# Synonym for the &points property.
		"""
		return self.points

	@property
	def identifier(self):
		"""
		# The identifier of the node relative to its container. (Head)
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
		# The root &Route with respect to the Route's context.
		"""

		return self.__class__(self.context, self.points[0:1])

	@property
	def container(self):
		"""
		# Return a Route to the outer (parent) Route; this merely removes the last point in the
		# sequence trimming the &context when necessary.
		"""

		if self.points:
			return self.__class__(self.context, self.points[:-1])
		else:
			return self.__class__(None, self.absolute[:-1])

	@staticmethod
	def _relative_resolution(points, len=len):
		"""
		# Resolve points identified as self points, `.`, and container points, `..`.

		# Used by &Route subclasses to support relative paths; this method should not be used
		# directly.
		"""
		rob = []
		add = rob.append
		parent_count = 0

		for x in points:
			if not x or x == '.':
				continue
			elif x == '..':
				parent_count += 1
			else:
				if parent_count:
					del rob[-parent_count:]
					parent_count = 0
				add(x)
		else:
			if parent_count:
				del rob[-parent_count:]

		return rob

class Route(PartitionedSequence):
	"""
	# Route domain base class.
	"""

class Segment(PartitionedSequence):
	"""
	# A path segment used to refer to a series of points in a &Route out-of-context.
	"""

	__slots__ = ('context', 'points',)

	def __str__(self):
		return (">>".join(self.absolute))

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
