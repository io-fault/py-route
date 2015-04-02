"""
Route interface specifiation.
"""
import abc
import collections.abc

@collections.abc.Hashable.register
class Route(metaclass = abc.ABCMeta):
	"""
	An abstract path to a resource.
	"""
	@property
	@abc.abstractmethod
	def datum(self):
		"""
		The :term:`route` that this Route is relative to; @None if the route isn't anchored
		to a particular datum.
		"""

	@property
	@abc.abstractmethod
	def points(self):
		"""
		Tuple of *relative* nodes in the Route. Points are hashable identifiers used to
		access the :term:`selection`.
		"""

	@property
	@abc.abstractmethod
	def absolute(self):
		"""
		The absolute sequence of points. Conceptually, tuple(@datum) + tuple(@points).
		"""

	@property
	@abc.abstractmethod
	def identity(self):
		"""
		The identity of the node relative to its immediate container.
		The last point in the route.
		"""

	@property
	@abc.abstractmethod
	def root(self):
		"""
		The root Route with respect to the Route's datum.
		"""

	@property
	@abc.abstractmethod
	def container(self):
		"""
		Return a Route to the outer Route; this merely removes the last crumb in the
		sequence.
		"""

	# System Queries; methods that actually interacts with the represented object
	# Potentially, this should be a distinct metaclass.

	@abc.abstractmethod
	def is_container(self):
		"""
		Interrogate the graph determining whether the Route points to a node that can
		refer to other points.
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
		Interrogate the graph returning a sequence of sequences containing the sub-nodes of
		the subject.
		"""
