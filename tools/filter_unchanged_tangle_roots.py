"""
Only keep the ones that changed
filter_unchanged_tangle_roots.py <roots_json> <current> <previous>
"""

import json
import argparse
import sys
import os
from os.path import join
import hashlib

parser = argparse.ArgumentParser(
	prog="filter_unchanged_tangle_roots",
	description="""
	Only keep directories whose content changed between current and previous
	tangled trees.
	""",
)

parser.add_argument(
	"roots_json",
	help="""
	List of directories to filter, as a json array
	""",
)

parser.add_argument(
	"current",
	help="""
	Root directory of the current state of tangled code, relative to which the
	list of directories is given
	""",
)

parser.add_argument(
	"previous",
	help="""
	Root directory of the previous state, to compare with current
	""",
)


def hash_dir(dirname):
	h = hashlib.sha256()
	for root, dirs, files in os.walk(dirname):
		for filename in files:
			h.update(b'$')
			h.update(filename.encode())
			with open(join(root, filename), "rb") as f:
				#hh = hashlib.file_digest(f, "sha256")
				#h.update(hh.digest())
				h.update(f.read())
		for dirname in dirs:
			h.update(b'@')
			h.update(dirname.encode())
	return h.digest()

def main(args):
	sys.stderr.write(f"input: {args.roots_json}\n")
	# Dirty fix to transform ["foo", "bar",] into ["foo", "bar"]
	clean_roots_json = '[' + args.roots_json.strip('[]').strip().strip(',') + ']'

	roots = json.loads(clean_roots_json, strict=False)

	def did_change(root):
		current_hash = hash_dir(join(args.current, root))
		previous_hash = hash_dir(join(args.previous, root))
		return current_hash != previous_hash
	changed_roots = list(filter(did_change, roots))

	sys.stderr.write(f"output: {changed_roots}\n")
	print(json.dumps(changed_roots))

if __name__ == "__main__":
	main(parser.parse_args())
