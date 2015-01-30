#!/usr/bin/python
from __future__ import with_statement  # for exception-proofing file operations

import zipfile
import argparse
import sys  # for stdout
import os.path
import os  # for file access checks

def parse_args() :
   # parse arguments
   usage_text = """Typical invocation: %(prog)s archive.zip
   
Unpacks ZIP archive, repairing faulty Windows path separators (\\)"""
   
   parser = argparse.ArgumentParser(description=usage_text,formatter_class=argparse.RawDescriptionHelpFormatter)
   parser.add_argument("-o", "--outdir", metavar="DIR", action="store", dest="outdir", help="where to unpack archive")
   parser.add_argument('archives', metavar="FILE", nargs="+", help="archives to unpack")
   parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False)
   parser.add_argument("-t", "--test", action="store_true", dest="test", default=False, help="do not extract, just pretend")
   parser.add_argument('--version', action='version', version='%(prog)s 1.0')

   options = parser.parse_args()

   return options

################################################################################
#
# main program starts here
#
################################################################################

if __name__ == "__main__" :
   options = parse_args()

   for archive in options.archives :
      try :
         zf_ = zipfile.ZipFile(archive)
      except :
         sys.stderr.write("Cannot open archive {0:s}\n".format(archive))
         continue

      for entry_ in zf_.infolist() :
        filepath_ = entry_.filename
        if "\\" in filepath_ :
           filepath_ = entry_.filename.replace('\\',os.sep)
        #if file_ :  # directories will have this empty
        if not filepath_.endswith(os.sep) :
           if options.verbose :
              sys.stdout.write("Extracting {0:s}\n".format(filepath_))
           if not options.test :
              dir_,file_ = os.path.split(filepath_)
              if options.outdir and len(options.outdir) > 0 :
                 dir_ = os.path.join(options.outdir,dir_)
              if not os.access(dir_,os.F_OK) :
                 os.makedirs(dir_)
              with open(filepath_,'w') as of_ :
                 of_.write(zf_.read(entry_))
