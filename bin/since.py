import sys

from .. import library as libroutes
from ...chronometry import library as libtime

def main(timestamp:str, *paths, file=None):
	"""
	[ Parameters ]
	/timestamp
		/`'now'`
			Print the list of files in the directory
			that are said to have been modified in the future.
		/`'recently'`
			Print the list of files that have been modified
			within the last 16 minutes.
		/`timestamp.isdigit()`
			Print the list of files that have been modified
			within the last `int(timestamp)` seconds.
		/`<iso formatted timestamp>`
			Print the list of files that have been modified
			since the ISO-9660 formmated timestamp.
	/paths
		A set of relative paths to search for modifications within.
	"""

	if timestamp == 'now':
		timestamp = libtime.now()
	elif timestamp == 'recently':
		timestamp = libtime.now().rollback(minute=16)
	elif timestamp.isdigit():
		timestamp = libtime.now().rollback(second=int(timestamp))
	else:
		timestamp = libtime.Timestamp.of(iso=timestamp)

	for x in paths:
		r = libroutes.File.from_path(x)
		for mt, mr in r.modifications(timestamp):
			print(str(mr).replace('\n', '\\n'), file=file)

if __name__ == '__main__':
	main(*sys.argv[1:])
