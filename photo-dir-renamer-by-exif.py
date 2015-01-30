#!/usr/bin/python

import argparse, sys

def parse_args() :
	# parse arguments
	usage_text = """..."""

	parser = argparse.ArgumentParser(description=usage_text,formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	parser.add_argument('dirs', metavar="DIR", nargs="+", help="directories to rename")
	parser.add_argument("--no-kidding", action="store_false", dest="dry_run", default=True)
	parser.add_argument("--remove-leading-numbers", action="store_true", dest="remove_lead_numbers", default=False,
								help="if old dir name starts with a number, omit the number together with hyphen or space that follows it")
	parser.add_argument("--dash-to-space", action="store_true", dest="dash_to_space", default=False,
								help="in new dir name replace dashes with spaces")
	parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False)
	parser.add_argument("-l", "--loglevel", action="store", type=int, dest="DEBUG", metavar="LOGLEVEL",
								help="loglevel [0-9]; 0 = normal operation; 9 = log every little detail", default=0)
	options = parser.parse_args()

	return options

def debug_print(debug_lvl,lvl,msg) :
	if lvl <= debug_lvl :
		sys.stderr.write("[DL{0:d}] {1:s}\n".format(lvl,msg))


def error(msg,is_fatal = False) :
	sys.stderr.write("{0:s} error: {1:s}\n".format("Fatal" if is_fatal else "Non-fatal",msg))
	if is_fatal : exit (1)


try:
	import pyexiv2
except:
	error("This script requires module \"pyexiv2\".",True)

import os, os.path

################################################################################
#
# main program starts here
#
################################################################################
IMAGETYPES = [".jpg",".jpeg",".png",".tiff"]

if __name__ == "__main__" :
	options = parse_args()
	for _dir in options.dirs:
		_dir = _dir.rstrip(os.sep)
		debug_print(options.DEBUG,1,"processing directory {0:s}".format(_dir))
		_startdate = _enddate = None
		for root, dirs, files in os.walk(_dir):
			for _filename in files:
				debug_print(options.DEBUG,2,"processing file {0:s}".format(os.path.join(root,_filename)))
				for _imagetype in IMAGETYPES:
					if _filename.lower().endswith(_imagetype):
						_filepath = os.path.join(root,_filename)
						_metadata = pyexiv2.ImageMetadata(_filepath)
						try:
							_metadata.read()
						except:
							if options.verbose:
								error("Cannot read EXIF metadata from file {0:s}, skipping...".format(_filepath))
							break

						try:
							_datedata = _metadata['Exif.Image.DateTime']
						except:
							if options.verbose or options.DEBUG > 1:
								error("EXIF metadata in file {0:s} does not seem to contain a date field, skipping...".format(_filepath))
							debug_print(options.DEBUG,3,"actual EXIF fields: {0:s}".format(_metadata.exif_keys))
							break

						try:
							_date = _datedata.value.date()  # _date will be a datetime.date object
						except:
							if options.verbose:
								error("EXIF metadata in file {0:s} does not seem to contain a valid date ({1:s}), skipping...".format(_filepath,_datedata.raw_value))
							break

						if _startdate == None or _startdate > _date :
							_startdate = _date
						if _enddate == None or _enddate < _date :
							_enddate = _date
						break

		if not (_startdate and _enddate):
			print "No photos with EXIF timestamps in directory: {0:s}".format(_dir)
		else:
			_path,_lastdir = os.path.split(_dir)
			if _startdate != _enddate :
				_timestamp = "[{0:s} - {1:s}]".format(_startdate.isoformat(),_enddate.isoformat())
			else:
				_timestamp = "[{0:s}]".format(_startdate.isoformat())

			if options.remove_lead_numbers:
				_lastdir = _lastdir.lstrip('0123456789')
				_lastdir = _lastdir.lstrip('- ')

			if options.dash_to_space:
				_lastdir = _lastdir.replace('-',' ')

			_newdir = os.path.join(_path,"{0:s} {1:s}".format(_timestamp,_lastdir))

			if os.access(_newdir,os.F_OK):
				error("Directory already exists: '{0:s}'".format(_newdir))
			else:
				if options.dry_run :
					print "Would rename: '{0:s}'  ->  '{1:s}'".format(_dir,_newdir)
				else:
					try:
						os.rename(_dir,_newdir)
					except:
						error("Cannot rename directories: '{0:s}'  ->  '{1:s}'".format(_dir,_newdir))
