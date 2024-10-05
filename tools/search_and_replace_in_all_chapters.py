import os
from os.path import dirname, join
import shutil

#--------------------------------------------------------------------

def process_line(line):
	return line

#--------------------------------------------------------------------

def process_file(filename):
	with open(filename, encoding="utf-8") as fin:
		with open(filename + ".new", encoding="utf-8") as fout:
			for line in fin:
				fout.write(process_line(line))
	shutil.move(filename + ".new", filename)

#--------------------------------------------------------------------

def collect_chapter_filenames(index_filename):
	all_subfiles = []
	with open(index_filename, encoding="utf-8") as f:
		state = "INIT"
		for line in f:
			if state == "INIT":
				if "```{toctree}" in line:
					state = "IN_TOCTREE"
			elif state == "IN_TOCTREE":
				if "```" in line:
					state = "DONE"
				else:
					subfile = line.strip()
					if not subfile.startswith(":") and subfile != "":
						all_subfiles.append(subfile + ".md")
		assert(state == "DONE")

	all_filenames = []
	for subfile in all_subfiles:
		filename = join(dirname(index_filename), subfile)
		all_filenames.append(filename)
		if subfile.endswith("index.md"):
			all_filenames.extend(collect_chapter_filenames(filename))
	return all_filenames

#--------------------------------------------------------------------

def main():
	index_filename = join(dirname(dirname(__file__)), "index.md")
	for filename in collect_chapter_filenames(index_filename):
		print(filename)

#--------------------------------------------------------------------

main()
