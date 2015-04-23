"""
Route interface specifiation.
"""
import abc
import collections.abc

class Resource(metaclass = abc.ABCMeta):
	"""
	An arbitrary object or representation that a Route points to.
	"""

@collections.abc.Hashable.register
class Route(metaclass = abc.ABCMeta):
	"""
	An abstract path to a &Resource.
	"""
	@property
	@abc.abstractmethod
	def datum(self):
		"""
		The &:route that this Route is relative to; &None if the route isn't anchored
		to a particular datum.
		"""

	@property
	@abc.abstractmethod
	def points(self):
		"""
		Tuple of *relative* nodes in the Route. Points are hashable identifiers used to
		access the &:selection. This does not include the points in the &datum.
		"""

	@property
	@abc.abstractmethod
	def absolute(self):
		"""
		The absolute sequence of points relative to the hierarchy true root.
		Conceptually, tuple(&datum) + tuple(&points).

		When use of the &datum as an axis is no longer desired, this property should be accessed.
		"""

	@property
	@abc.abstractmethod
	def root(self):
		"""
		The root of the Route with respect to the Route's datum. The property's &Route
		will have the &datum as a prefix and the initial point as its only point.
		"""

	@property
	@abc.abstractmethod
	def identity(self):
		"""
		The identity of the node relative to its immediate container. The last point in the route.
		"""

	@abc.abstractmethod
	def discard(self, points = 1):
		"""
		Construct a new &Route consisting of path of the instance up until the specified number
		of points. Discard does *not* cross datum boundaries.
		"""

	@abc.abstractmethod
	def truncate(self, point):
		"""
		Construct a new &Route consisting of the existing sequence of points up to the *last*
		point specified by the &point argument. Similar to slicing a sequence from a
		reverse index search. Truncate does *not* cross &datum boundaries.
		"""

	@abc.abstractmethod
	def lateral(self, point, ascent = 1):
		"""
		Construct a new &Route that refers to a point that exists alongside the &datum of
		the &Route. For filesystems, this would be the parent directory of the &datum with
		the specified &point argument as its trailing point.

		Used to escape &datum boundaries while still referring to it; &ascent defaults to
		one, but can be used to adjust the distance from the &datum.
		"""

	@abc.abstractmethod
	def ascend(self, ascent = 1):
		"""
		Construct a new &Route where the last &ascent number of points are discarded from
		the route. However, if the level ascends beyond the &datum, cross the boundary and
		define the route as being the root of a new &datum.
		"""

	@abc.abstractmethod
	def descend(self, *points):
		"""
		Construct a new &Route with the given &points appended.
		"""

	@property
	@abc.abstractmethod
	def container(self):
		"""
		Return a Route to the outer Route. This will *not* cross datum boundaries.
		"""

	# System Queries; methods that actually interacts with the represented object
	# Potentially, this should be a distinct metaclass.

	@abc.abstractmethod
	def is_container(self):
		"""
		Interrogate the graph determining whether the Route points to a node that can
		refer to other points. For some fields, this may always be &True.
		"""

	@abc.abstractmethod
	def real(self):
		"""
		Interrogate the points in the graph in order to determine the valid portion of the route.
		Returns a new Route to the portion of the route that actually exists or the same
		instance if it is real. If no real portion exists, &None must be returned.
		"""

	@abc.abstractmethod
	def subnodes(self):
		"""
		Interrogate the graph returning a sequence of sequences containing the sub-nodes of
		the subject.
		"""

@collections.abc.Hashable.register
class Perspective(metaclass=abc.ABCMeta):
	"""
	An object of near arbitrary consistency dictating the consistency of a particular
	&Point.
	"""

@collections.abc.Hashable.register
class Point(metaclass=abc.ABCMeta):
	"""
	A point in an arbitrary hierarchy with respect to a configured perspective.
	"""
	@abc.abstractmethod
	def rotate(self, perspective) -> Point:
		"""
		Construct a new Point at the same location using a different perspective.
		Normally used to access a different set of properties, but directories and lineals
		may be different as well.
		"""

	@property
	@abc.abstractmethod
	def perspective(self):
		"""
		The relevant perspective used to refer to the selection.
		Primarily used as a parameter to identify the visibility of relationships.

		&None if not applicable.
		"""

	@property
	@abc.abstractmethod
	def root(self):
		"""
		An object representing the root of a hierarchy; the last lineal.

		Unlike &Route instances, &Point's are not constrained to a datum, so the boundaries
		are defined by the graph that is being interrogated.
		"""

	@property
	@abc.abstractmethod
	def route(self):
		"""
		Reference to the object being interfaced relative to &root.
		The &route with respect to the &root procures this &Point.

		The datum of the &Route will be initialized to the absolute path to the &Point.
		"""

	@property
	@abc.abstractmethod
	def lineals(self):
		"""
		An ordered mapping of objects that lead to the subject.
		The index is an offset of the distance from the &route; index zero is the immediate parent.
		"""

	@property
	@abc.abstractmethod
	def directory(self):
		"""
		An ordered mapping of objects that are directly related to the subject;
		normally, objects contained by the subject itself.

		Large or infinite associations will often use custom types.
		"""

	@property
	@abc.abstractmethod
	def contexts(self):
		"""
		An ordered mapping of objects that are contextually relavant to the subject.

		The meaning and consistency of &contexts is wholly dependant on the underlying
		representation of the concept.
		"""

	@property
	@abc.abstractmethod
	def properties(self):
		"""
		Mapping providing information about the subject relevant to the perspective.
		"""
