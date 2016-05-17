#!/usr/bin/python
# vim: set ts=3 sw=3 tw=0 et :
#
# Script developed for synchronising data on backup pendrive (that was later edited in place 
# and de-synchrnised with the data on disk) with the original directory tree
#

from __future__ import with_statement  # for exception-proofing file operations

import argparse
#import md5, sha
import hashlib
import os, os.path, sys
import time
import cPickle   # for saving intermediate results file as dictionary object


BUF_SIZE = 65536  # lets read stuff in 64kb chunks!


def parse_args() :
   # parse arguments
   usage_text = """Compares two dir trees, looking for files that are present in one of them only."""
   epilog_text="""Typical usage:
  %(prog)s <just do it!>"""
   parser = argparse.ArgumentParser(description=usage_text,epilog=epilog_text,formatter_class=argparse.RawDescriptionHelpFormatter)
   parser.add_argument('refdir', metavar="REFERENCE_DIRECTORY", help="directory tree that will provide hints concerning which copy in the other dir tree to keep")
   parser.add_argument('backupdir', metavar="BACKUP_DIRECTORY", help="the other dir tree...")
   parser.add_argument("--sha1", action="store_const", const=hashlib.sha1, dest="hasher", default=hashlib.md5)
   parser.add_argument("--store-hashes", action="store", dest="hash_store", help="File to store computed file hashes in (for future duplicate identification without needing to re-analyse dir tree).")
   parser.add_argument("--load-hashes", action="store", dest="hash_load", help="File to load computed file hashes from (for duplicate identification without needing to re-analyse dir tree. Overrides REFERENCE_DIRECTORY and BACKUP_DOCUMENT with stored values.")
   parser.add_argument("--delete", action="store_true", dest="delete", help="Really delete files identified as reduntant (default: report only)")
   parser.add_argument("-c","--csv", action="store_const", const="csv", dest="format_dup", default="human", help="Report duplicates in CSV format (default: human-readable)")
   parser.add_argument("--debug", action="store_true", dest="debug", help="Print lots of debugging information")
   parser.add_argument("-1", action="store_true", dest="step1", help="Identify duplicates in refdir")
   parser.add_argument("-2", action="store_true", dest="step2", help="Identify duplicates in backupdir")
   parser.add_argument("-3", action="store_true", dest="step3", help="Suggest which copy in backupdir to keep if several are present")
   parser.add_argument("-4", action="store_true", dest="step4", help="Identify files that are only present in backupdir and not in refdir")
   options = parser.parse_args()
   # argument logic check
   if options.hash_store and options.hash_load :
      error("Both --store-hashes and --load-hashes specified, make up your mind...",True)
   options.all_steps = False if (options.step1 or options.step2 or options.step3 or options.step4) else True
   return options


def error(msg,is_fatal = False) :
   sys.stderr.write("{0:s} error: {1:s}\n".format("Fatal" if is_fatal else "Non-fatal",msg))
   if is_fatal : exit (1)

def append_or_insert(dict_of_lists,key,elem) :
   if key in dict_of_lists :
      dict_of_lists[key].append(elem)
   else :
      dict_of_lists[key] = [elem]

def debug_msg(msg) :
   if options.debug :
      sys.stdout.write("[debug] {0:s}\n".format(msg))

def get_hashes(dirtree, hash_engine) :
   _hashes = {}
   if os.path.isdir(dirtree) : debug_msg("get_hashes: valid directory \'{0:s}\' passed as argument".format(dirtree))
   for dirpath, dirs, files in os.walk(dirtree) :
      debug_msg("get_hashes: descending into directory \'{0:s}\'\n".format(dirpath))
      for _file in files :
         _file_fullpath = os.path.join(dirpath,_file)
         debug_msg("get_hashes: processing file name \'{0:s}\'\n".format(_file_fullpath))
         if os.path.isfile(_file_fullpath) :
            if os.access(_file_fullpath,os.R_OK) :
               with open(_file_fullpath,'rb') as _input_file :
                  _hasher = hash_engine()
                  while True :
                     data = _input_file.read(BUF_SIZE)
                     if not data : break
                     _hasher.update(data)
                  _hash = _hasher.hexdigest()
                  debug_msg("get_hashes: file \'{0:s}\' : hash = {1:s}\n".format(_file_fullpath,_hash))
                  #print "File: {0}, hash: {1}".format(_file_fullpath,_hash)
                  append_or_insert(_hashes,_hash,_file_fullpath)
            else : error("Cannot read file {0}, skipping".format(_file_fullpath),False)

#      for _dir in dirs :
#         debug_msg("get_hashes: os.walk generated: {0:s} {1:s}\n".format(dirpath,_dir))
#         _dir_fullpath = os.path.join(dirpath,_dir)
#         debug_msg("get_hashes: descending into directory {0:s}\n".format(_dir_fullpath))
#         for _file in os.listdir(_dir_fullpath) :
   return _hashes


def detect_duplicates(dir_hashes) :
   _hash_collisions = 0
   _duplicates = []
   for _hash in sorted(dir_hashes.keys()) :
      _files = dir_hashes[_hash]
      debug_msg("detect_duplicates: hash {0:s} associated with files {1:s}\n".format(_hash,_files))
      if len(_files) > 1 :
         _sizes = {}  # 2nd identity criterion - file size
         for _file in _files :
            append_or_insert(_sizes,os.path.getsize(_file),_file)
         debug_msg("detect_duplicates: hash {0:s} - files sizes {1:s}\n".format(_hash,_sizes))
         for _size in _sizes :
            if len(_sizes[_size]) > 1 :
               #print "--- Duplicates: ---------"
               #for _file in _sizes[_size] :
               #   print _file
               _duplicates.append((_hash,_size,_sizes[_size]))  # store tuple
               debug_msg("detect_duplicates: hash {0:s} - DUPLICATE DETECTED\n".format(_hash))
         if len(_sizes) > 1 :
            _hash_collisions += 1
   return _duplicates,_hash_collisions

def report_duplicates(refdir_dups,hash_collisions,dir_type) :
   print "\n*** {0:s} directory: {1:d} hash collisions ***".format(dir_type.capitalize(),hash_collisions)
   if refdir_dups :
      if options.format_dup == "csv" :
         for _dup in refdir_dups :
            _msg = "\"{0:s} DIR DUPLICATE\"".format(dir_type.upper())
            _,_,_filenames = _dup
            for _dupname in _filenames :
               _msg += ",\"{0:s}\"".format(_dupname)
            print _msg
      else :
         for _dup in refdir_dups :
            _msg = dir_type.upper() + " DIR DUPLICATE: "
            _,_,_filenames = _dup
            for _dupname in _filenames :
               _msg += " \'{0:s}\'".format(_dupname)
            print _msg
   print "\n*** {0:s} directory: {1:d} duplicate sets detectes ***".format(dir_type.capitalize(),len(refdir_dups))


###############################################
#
# the program starts here
#
###############################################
options = parse_args()

if options.hash_load :
   with open(options.hash_load) as input_file :
      try :
         options.refdir = cPickle.load(input_file)
         _hashes_refdir = cPickle.load(input_file)
         options.backupdir = cPickle.load(input_file)
         _hashes_backupdir = cPickle.load(input_file)
      except :
         error("Wrong format of hashes file {0}!".format(options.hash_load),True)
else :
   #if options.hasher == "sha1" : HASHER = sha
   #elif options.hasher == "md5" : HASHER = md5
   #else : HASHER = md5
   HASHER=options.hasher

   # validate options
   if not os.access(options.refdir,os.R_OK) :
      error("Cannot read directory {0}".format(options.refdir),True)
   if not os.access(options.backupdir,os.R_OK) :
      error("Cannot read directory {0}".format(options.backupdir),True)

   #start_time = time.time()
   #_hashes = get_hashes(options.refdir,md5)
   #print "MD5: elapsed time = {0:f}, dict size = {1:d}".format(time.time() - start_time,len(_hashes))
   debug_msg("processing reference image directory \"{0:s}\"".format(options.refdir))
   _hashes_refdir = get_hashes(options.refdir,HASHER)
   debug_msg("processing backup image directory \"{0:s}\"".format(options.backupdir))
   _hashes_backupdir = get_hashes(options.backupdir,HASHER)

   if options.hash_store :
      with open(options.hash_store,'w') as output_file :
         cPickle.dump(options.refdir,output_file)
         cPickle.dump(_hashes_refdir,output_file)
         cPickle.dump(options.backupdir,output_file)
         cPickle.dump(_hashes_backupdir,output_file)

# run 1 : detect duplicates in refdir
if options.all_steps or options.step1 :
   _refdir_dups,_hash_collisions = detect_duplicates(_hashes_refdir)
   report_duplicates(_refdir_dups,_hash_collisions,"reference")

# run 2 : detect duplicates in backupdir
if options.all_steps or options.step2 :
   _backupdir_dups,_hash_collisions = detect_duplicates(_hashes_backupdir)
   print "\n*** Backup directory: {0:d} hash collisions ***".format(_hash_collisions)

# run 3 : suggest which copy in backupdir to keep
if options.all_steps or options.step3 :
   _cnt_decided = _cnt_undecided = 0
   for _hash,_size,_dups in _backupdir_dups :
      # first look up the file in reference dir
      if _hash in _hashes_refdir :
         _decided = False
         _chosen = []
         _refdir_locations = []
         for _refdir_file in _hashes_refdir[_hash] :
            _refdir_locations.append(os.path.relpath(_refdir_file,options.refdir))
         for _dup in _dups :
            if os.path.relpath(_dup,options.backupdir) in _refdir_locations :
               _decided = True
               _cnt_decided += 1
               _chosen.append(_dup)
         print "--- Duplicates : ---"
         print "REF: {0}".format(_hashes_refdir[_hash][0])
         for _dup in _dups :
            print "{0} : {1}".format(_dup,"hgw" if not _decided else "keep" if _dup in _chosen else "delete")
            if options.delete :
               if _decided and _dup not in _chosen :
                  os.remove(_dup)
                  #print "os.remove({0})".format(_dup)
         if not _decided :
            _cnt_undecided += 1

# run 4 : count files occurring only in backupdir (and absent from refdir)
if options.all_steps or options.step4 :
   _uniq = []
   for _hash in sorted(_hashes_backupdir.keys()) :
      if _hash not in _hashes_refdir :
         _uniq.extend(_hashes_backupdir[_hash])
   print "\n***** Files existing only in backup directory: *****"
   for _f in sorted(_uniq) : print _f

print "\nreference dir : {0}".format(options.refdir)
print "backup dir : {0}".format(options.backupdir)
#print "duplicates decided: {0:d}  undecided: {1:d}".format(_cnt_decided,_cnt_undecided)
