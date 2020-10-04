"""
# Relative path resolution.
"""
import typing

def relative(points:typing.Sequence[str], delta=({'':0, '.':0, '..':1}).get):
	"""
	# Resolve relative accessors within &points.
	"""
	r = []
	add = r.append
	change = 0

	for x in points:
		a = delta(x)
		if a is not None:
			change += a
		else:
			if change:
				# Apply ascent.
				del r[-change:]
				change = 0
			add(x)
	else:
		if change:
			del r[-change:]

	return r
