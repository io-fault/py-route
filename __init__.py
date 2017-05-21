"""
# Routes provides a set of classes for managing arbitrary paths. The specializations
# provide convenient access to information about the path's selection making things such as
# fetching modification times convenient and obvious.

# A route, &.library.Route, is merely a sequence of identifiers used to select an object or
# concept. However, it is structured so that the path is relative to a context in
# order to make certain manipulations relative to a particular node.
# Importantly, nodes may not actually exist; the path of the route is entirely independent
# of connected system managing the Real Nodes.

#!/pl/python
	from fault.chronometry import library as libtime
	from fault.routes import library as libroutes

	cat_exe = libroutes.File.from_absolute('/bin/cat')
	etc_dir = libroutes.File.from_absolute('/etc')
	root_dir = libroutes.File.from_absolute('/')

	# # Queries.
	mod_time = cat_exe.get_last_modified()
	binary_size = cat_exe.size()
	assert cat_exe.type() == 'executable'
	assert root_dir.type() == 'directory'

	# # Get changes since:
	modified_files = etc_dir.since(libtime.now().rollback(hour=1))
"""
__factor_type__ = 'project'
