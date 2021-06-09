"""
# Route Protocols
"""
import abc
import typing
import collections.abc

@collections.abc.Hashable.register
class Route(metaclass=abc.ABCMeta):
	"""
	# A series of identifiers used to form an absolute or relative path.
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
	def identifier(self):
		"""
		# The identity of the node relative to its immediate container. The last point in the route.
		"""

	@abc.abstractmethod
	def truncate(self, point):
		"""
		# Construct a new &Route consisting of the existing sequence of points up to the *last*
		# point specified by the &point argument. Similar to slicing a sequence from a
		# reverse index search. Truncate does *not* cross &context boundaries.
		"""

	@abc.abstractmethod
	def __pow__(self, route):
		"""
		# Numeric ascend operation.
		"""

	@abc.abstractmethod
	def __invert__(self):
		"""
		# Stepwise root ascension.
		"""

	@abc.abstractmethod
	def __lshift__(self, route):
		"""
		# Stepwise ascension path.
		"""

	@abc.abstractmethod
	def __rshift__(self, route):
		"""
		# Stepwise descension path.
		"""

	@abc.abstractmethod
	def __xor__(self, route):
		"""
		# Stepwise traverse path.
		"""

	@abc.abstractmethod
	def __add__(self, route):
		"""
		# Sequence-type extension.
		"""

	@abc.abstractmethod
	def __matmul__(self, route):
		"""
		# Composite extension.
		"""

	@abc.abstractmethod
	def __floordiv__(self, route):
		"""
		# Segment extension.
		"""

	@abc.abstractmethod
	def __truediv__(self, route):
		"""
		# Single point extension.
		"""

class FileSystemPath(metaclass=abc.ABCMeta):
	"""
	# File system APIs for supporting common access functions.
	"""

	@abc.abstractmethod
	def fs_alloc(self):
		"""
		# Allocate the necessary resources to create the target path as a file or directory.

		# Normally, this means creating the leading path to the identified resource.
		"""

	@abc.abstractmethod
	def fs_load(self) -> bytes:
		"""
		# Retrieve the binary data from the file referenced by the &Route.

		# If the storage system being referenced by the Route is not storing binary data,
		# then the object stored should be transformed into binary data. For instance,
		# if the Route was bound to a virtual filesystem that was storing &str instances,
		# then the returned object should be encoded using a context configured encoding.
		"""

	@abc.abstractmethod
	def fs_store(self, data:bytes) -> None:
		"""
		# Store the given &data at the &Route.
		"""

	@abc.abstractmethod
	def fs_get_text_content(self) -> str:
		"""
		# Retrieve the contents of the file reference by the &Route as a &str.
		"""

	@abc.abstractmethod
	def fs_set_text_content(self, text:str) -> None:
		"""
		# Set the contents of the file to the given &text.
		"""

	@abc.abstractmethod
	def fs_get_last_modified(self) -> "timestamp":
		"""
		# Retrieve the timestamp that the file at the &Route was last modified at.
		"""

	@abc.abstractmethod
	def fs_set_last_modified(self, timestamp):
		"""
		# Update the modification time of the file identified by the &Route.
		"""

	@abc.abstractmethod
	def fs_type(self) -> str:
		"""
		# A string identifying the type of file selected by the &Route.
		"""

	@abc.abstractmethod
	def fs_executable(self) -> bool:
		"""
		# Whether or not the regular file is executable.

		# Directories marked as executable are not considered executables.
		"""

	@abc.abstractmethod
	def fs_searchable(self) -> bool:
		"""
		# Whether or not the directory's listing can be retrieved.

		# Regular files marked as executable are not considered searchable.
		"""

	@abc.abstractmethod
	def fs_test(self) -> bool:
		"""
		# Whether the file exists.
		"""

	@abc.abstractmethod
	def fs_select(self:Route, pattern:object, area:str='directory') -> typing.Collection[Route]:
		"""
		# Select the set of files relative to the &Route that match the given &pattern
		# within the designated &area.
		"""
