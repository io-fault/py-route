"""
# Route Protocols
"""
import abc
import typing
import collections.abc

@collections.abc.Hashable.register
class Selectors(metaclass=abc.ABCMeta):
	"""
	# An abstract series of identifiers. The common protocol between &Route and &Segment
	"""

	@property
	@abc.abstractmethod
	def context(self):
		"""
		# The &Route that this Route is relative to; &None if the route isn't anchored
		# to a particular Context.
		"""

	@property
	@abc.abstractmethod
	def points(self):
		"""
		# Tuple of *relative* nodes in the Route. Points are hashable identifiers used to
		# access the Selected Resource. This does not include the points in the &context.
		"""

	@property
	@abc.abstractmethod
	def container(self):
		"""
		# Return a Route to the outer Route. This will cross &context boundaries.
		"""

	@property
	@abc.abstractmethod
	def absolute(self):
		"""
		# The absolute sequence of points relative to the hierarchy's true root.
		"""

	@property
	@abc.abstractmethod
	def root(self):
		"""
		# The root of the Route with respect to the Route's context. The property's &Route
		# will have the &context as a prefix and the initial point as its only point.
		"""

	@property
	@abc.abstractmethod
	def identifier(self):
		"""
		# The identity of the node relative to its immediate container. The last point in the route.
		"""

	@abc.abstractmethod
	def discard(self, points = 1):
		"""
		# Construct a new &Route consisting of path of the instance up until the specified number
		# of points. Discard does *not* cross context boundaries.
		"""

	@abc.abstractmethod
	def truncate(self, point):
		"""
		# Construct a new &Route consisting of the existing sequence of points up to the *last*
		# point specified by the &point argument. Similar to slicing a sequence from a
		# reverse index search. Truncate does *not* cross &context boundaries.
		"""

	@abc.abstractmethod
	def lateral(self, point, ascent = 1):
		"""
		# Construct a new &Route that refers to a point that exists alongside the &context of
		# the &Route. For filesystems, this would be the parent directory of the &context with
		# the specified &point argument as its trailing point.

		# Used to escape &context boundaries while still referring to it; &ascent defaults to
		# one, but can be used to adjust the distance from the &context.
		"""

	@abc.abstractmethod
	def ascend(self, ascent = 1):
		"""
		# Construct a new &Route where the last &ascent number of points are discarded from
		# the route. However, if the level ascends beyond the &context, cross the boundary and
		# define the route as being the root of a new &context.
		"""

	@abc.abstractmethod
	def descend(self, *points):
		"""
		# Construct a new &Route with the given &points appended.
		"""

class Route(Selectors):
	# System Queries; methods that actually interacts with the represented object
	# Potentially, this should be a distinct metaclass.

	@abc.abstractmethod
	def is_container(self):
		"""
		# Interrogate the graph determining whether the Route points to a node that can
		# refer to other points. For some fields, this may always be &True.
		"""

	@abc.abstractmethod
	def real(self):
		"""
		# Interrogate the points in the graph in order to determine the valid portion of the route.
		# Returns a new Route to the portion of the route that actually exists or the same
		# instance if it is real. If no real portion exists, &None must be returned.
		"""

	@abc.abstractmethod
	def subnodes(self):
		"""
		# Interrogate the graph returning a sequence of sequences containing the sub-nodes of
		# the subject.
		"""

class FileInterface(metaclass=abc.ABCMeta):
	"""
	# File system APIs for supporting common access functions.
	"""

	@abc.abstractmethod
	def load(self) -> bytes:
		"""
		# Retrieve the binary data from the file referenced by the &Route.

		# If the storage system being referenced by the Route is not storing binary data,
		# then the object stored should be transformed into binary data. For instance,
		# if the Route was bound to a virtual filesystem that was storing &str instances,
		# then the returned object should be encoded using a context configured encoding.
		"""

	@abc.abstractmethod
	def store(self, data:bytes) -> None:
		"""
		# Store the given &data at the &Route.
		"""

	@abc.abstractmethod
	def get_text_content(self) -> str:
		"""
		# Retrieve the contents of the file reference by the &Route as a &str.
		"""

	@abc.abstractmethod
	def set_text_content(self, text:str) -> None:
		"""
		# Set the contents of the file to the given &text.
		"""

	@abc.abstractmethod
	def get_last_modified(self) -> "timestamp":
		"""
		# Retrieve the timestamp that the file at the &Route was last modified at.
		"""

	@abc.abstractmethod
	def set_last_modified(self, timestamp):
		"""
		# Update the modification time of the file identified by the &Route.
		"""

	@abc.abstractmethod
	def type(self) -> str:
		"""
		# A string identifying the type of file selected by the &Route.
		"""

	@abc.abstractmethod
	def is_disconnected_link(self) -> bool:
		"""
		# Whether the &Route selects a symbolic link whose target does not exist.
		"""

	@abc.abstractmethod
	def is_regular_file(self) -> bool:
		"""
		# Whether the &Route selects a regular file.
		"""

	@abc.abstractmethod
	def is_directory(self) -> bool:
		"""
		# Whether the &Route selects a directory.
		"""

	@abc.abstractmethod
	def executable(self) -> bool:
		"""
		# Whether or not the regular file is executable.

		# Directories marked as executable are not considered executables.
		"""

	@abc.abstractmethod
	def searchable(self) -> bool:
		"""
		# Whether or not the directory's listing can be retrieved.

		# Regular files marked as executable are not considered searchable.
		"""

	@abc.abstractmethod
	def exists(self) -> bool:
		"""
		# Whether the file exists.
		"""

	@abc.abstractmethod
	def files(self) -> typing.Collection["File"]:
		"""
		# Return a sequence of &Route instances that are normal files contained
		# within the &Route.
		"""

	@abc.abstractmethod
	def subdirectories(self) -> typing.Collection["File"]:
		"""
		# Return a sequence of &Route instances that are directories contained
		# within the &Route.
		"""

	@abc.abstractmethod
	def select(self:Route, pattern:object, area:str='directory') -> typing.Collection[Route]:
		"""
		# Select the set of files relative to the &Route that match the given &pattern
		# within the designated &area.
		"""
