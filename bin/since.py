import sys

from ...system import files
from ...time import types as timetypes
from ...time import sysclock

def main(timestamp:str, *paths, file=None):
	"""
	# [ Parameters ]

	# /timestamp/
		# /`'now'`/
			# Print the list of files in the directory
			# that are said to have been modified in the future.
		# /`'recently'`/
			# Print the list of files that have been modified
			# within the last 16 minutes.
		# /`timestamp.isdigit()`/
			# Print the list of files that have been modified
			# within the last `int(timestamp)` seconds.
		# /`<iso formatted timestamp>`/
			# Print the list of files that have been modified
			# since the ISO-9660 formmated timestamp.

	# /paths/
		# A set of relative paths to search for modifications within.
	"""

	if timestamp == 'now':
		timestamp = sysclock.now()
	elif timestamp == 'recently':
		timestamp = sysclock.now().rollback(minute=16)
	elif timestamp.isdigit():
		timestamp = sysclock.now().rollback(second=int(timestamp))
	else:
		timestamp = timetypes.Timestamp.of(iso=timestamp)

	for x in paths:
		r = files.Path.from_path(x)
		for mt, mr in r.since(timestamp):
			print(str(mr).replace('\n', '\\n'), file=file)

if __name__ == '__main__':
	main(*sys.argv[1:])
