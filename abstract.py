"""
"""
import abc

class Route(metaclass = abc.ABCMeta):
	"""
	An abstract path to a resource.
	"""
	@abc.abstractproperty
	def datum(self):
		"""
		The :term:`route` that this Route is relative to. The :py:attr:`datum` attribute of
		Routes is :py:obj:`None` if the Route is absolute.
		"""

	@abc.abstractproperty
	def points(self):
		"""
		Tuple of *relative* nodes in the Route. Points are hashable identifiers used to
		access the :term:`selection`.
		"""

	def __init__(self, datum, points):
		self.datum = datum
		self.points = points

	@abc.abstractproperty
	def __str__(self):
		"""
		The string representation of the :py:attr:`absolute` appropriate for the context of
		the runtime.
		"""

	def __hash__(self):
		return hash((self.datum, self.points))

	def __repr__(self):
		return "{0}({1}, {2})".format(self.__qualname__, repr(self.datum), repr(self.points))

	def __str__(self):
		return '/'.join(self.points)

	def __eq__(self, ob, isinstance = isinstance):
		# Datums can be None, so that's where the recursion stops.
		return (self.absolute == ob.absolute and isinstance(ob, self.__class__))

	def __contains__(self, abs):
		return abs.points[:len(self.points)] == self.points

	def __getitem__(self, req):
		# for select slices of routes
		return self.__class__(self.datum, self.points[req])

	def __add__(self, tail):
		if tail.datum is None:
			return tail.__class__(self, tail.points)
		else:
			# replace the datum
			return tail.__class__(self, tail.absolute.points)

	def __truediv__(self, next_point):
		return self.__class__(self.datum, self.points + (next_point,))

	def __invert__(self):
		"""
		Consume one datum level into a new Route.
		"""
		if self.datum is None:
			return self
		return self.__class__(self.datum.datum, self.datum.points + self.points)

	@property
	def absolute(self):
		"""
		The absolute sequence of points.
		"""
		r = self.points
		x = self
		while x.datum is not None:
			r = x.datum.points + r
			x = x.datum
		return r

	@property
	def identity(self):
		"""
		The identity of the node relative to its container. (Head)
		"""
		return self.points[-1]

	@property
	def local(self):
		"""
		Return a Pointer to the module's package.
		If the Pointer is referencing a package, return the object.
		"""
		if self.is_container():
			return self
		return self.__class__(self.points[:-1])

	@property
	def root(self):
		"""
		The root Route with respect to the Route's datum.
		"""
		return self.__class__(self.datum, self.points[0:1])

	@property
	def container(self):
		"""
		Return a Route to the outer Route; this merely removes the last crumb in the
		sequence.
		"""
		return self.__class__(self.datum, self.points[:-1])

	@abc.abstractmethod
	def is_container(self):
		"""
		Interrogate the graph determining whether the Route points to a leaf node.
		"""

	@abc.abstractmethod
	def real(self):
		"""
		Interrogate the graph in order to determine the valid portion of the route.

		This method returns an absolute Route.
		"""

	@abc.abstractmethod
	def subnodes(self):
		"""
		subnodes()

		:returns: ([], ...)
		:rtype: A tuple of sequences containing subnodes of a type consistent with the Route.

		Interrogate the graph returning a sequence of sequences containing the sub-nodes of
		the subject.
		"""
