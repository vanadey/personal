#!/usr/bin/python
# vim: set ts=3 sw=3 tw=0 et :
#
# Script developed for synchronising data on backup pendrive (that was later edited in place 
# and de-synchronised with the data on disk) with the original directory tree
#

  # for exception-proofing file operations

import argparse
import hashlib
import os, os.path, sys
import pickle   # for saving intermediate results file as dictionary object
import enum


BUF_SIZE = 65536  # let's read stuff in 64kb chunks!


def parse_args() :
   # parse arguments
   usage_text = (
      "Compares a candidate dir tree against a storage dir tree, identifying files that are already present\n"
      "(and therefore need not be copied).")
   epilog_text= (
      "Typical usage cases:\n"
      "  %(prog)s --identify-duplicates --dir DIRECTORY\n"
      "                        : Identify duplicates within DIRECTORY\n"
      "  %(prog)s --identify-duplicates --dir DIRECTORY --repository REPOSITORY\n"
      "                        : Identify files that are present in directory, but not in repository\n"
      "                          (i.e. that should be added to repository)\n"
      "  %(prog)s --suggest --dir DIRECTORY --repository REPOSITORY\n"
      "                        : Suggest which copy in repository to keep if several are present\n"
      "  %(prog)s --store-hashes HASHFILE --dir DIRECTORY\n"
      "                        : Compute file hashes and just store them for future analysis\n"
      "  %(prog)s --dir-hashes HASHFILE --identify-duplicates\n"
      "                        : Load file hashes for a single directory and identify duplicates among them\n"
      "  %(prog)s --dir-hashes HASHFILE0 --repo-hashes HASHFILE1 --all\n"
      "                        : Load file hashes and do full analysis")
   parser = argparse.ArgumentParser(description=usage_text,epilog=epilog_text,formatter_class=argparse.RawDescriptionHelpFormatter)
   parser.add_argument("-d","--dir", action="store", dest="dir", help="directory tree potentially with duplicates;\nif repository is also specified: with duplicates w.r.t. storage repository; it will also provide hints which copy in the storage repository to keep")
   parser.add_argument("-r","--repository", action="store", dest="repository", help="permanent storage repository")
   parser.add_argument("--sha1", action="store_const", const=hashlib.sha1, dest="hasher", default=hashlib.md5)
   parser.add_argument("--store-hashes", action="store", dest="hash_store", help="File to store computed file hashes in; precludes further actions")
   parser.add_argument("--dir-hashes", action="store", dest="dir_hashes", help="File with computed file hashes for directory")
   parser.add_argument("--repo-hashes", action="store", dest="repo_hashes", help="File with computed file hashes for repository")
   parser.add_argument("--delete", action="store_true", dest="delete", help="Really delete files identified as reduntant (default: report only)")
   parser.add_argument("-c","--csv", action="store_const", const="csv", dest="format_dup", default="human", help="Report duplicates in CSV format (default: human-readable)")
   parser.add_argument("--debug", action="store_true", dest="debug", help="Print lots of debugging information")
   actions = parser.add_argument_group("actions")
   actions.add_argument("--identify-duplicates", action="store_true", dest="identify", help="Identify duplicates within directory tree(s)")
   actions.add_argument("--suggest", action="store_true", dest="suggest", help="Suggest which copy in repository to keep if several are present")
   actions.add_argument("--all", action="store_true", dest="all_steps", help="Combine --identify-duplicates and --suggest")
   _result = parser.parse_args()

   _result.dirtree_count = 1 if (_result.dir or _result.dir_hashes) and not (_result.repository or _result.repo_hashes) else 2

   # argument logic check
   if _result.all_steps :
      _result.identify = _result.suggest = True
   if not (_result.dir or _result.dir_hashes) :
      error("One must specify either directory or directory hashfile", True)
   if _result.dir and _result.dir_hashes :
      error("Specifying directory and directory hashfile makes no sense", True)
   if _result.repository and _result.repo_hashes :
      error("Specifying repository and repository hashfile makes no sense", True)
   if (_result.repository or _result.repo_hashes) and not (_result.dir or _result.dir_hashes) :
      error("Specifying repository (or hashfile) without directory (or hashfile) makes no sense",True)
   if _result.hash_store and (_result.dir_hashes or _result.repo_hashes or _result.identify or _result.suggest) :
      error("Storing hashes precludes any other actions",True)
   if _result.hash_store and not _result.dir :
      error("If one wants to compute hashes, one has to specify a directory...",True)
   if _result.hash_store and _result.repository :
      error("Computng hashes works on single directories only; run twice, specifying both dirs in turn",True)
   if _result.suggest and _result.dirtree_count != 2 :
      error("--suggest requires specifying both directory (or hashfile) and repository (or hashfile)",True)

   return _result


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

def read_hashes(hashfile) :
   with open(hashfile,'rb') as input_file:
      try:
         options.dir = pickle.load(input_file)
         return pickle.load(input_file)
      except:
         error("Wrong format of hashfile {0}!".format(hashfile), True)


def get_hashes(dirtree) :
   _hash_engine = options.hasher

   # validate options
   if not os.access(dirtree, os.R_OK):
      error("Cannot read directory {0}".format(dirtree), True)

   # start_time = time.time()
   # _hashes = get_hashes(options.dir,md5)
   # print "MD5: elapsed time = {0:f}, dict size = {1:d}".format(time.time() - start_time,len(_hashes))
   debug_msg("processing directory tree \"{0:s}\"".format(dirtree))

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
                  _hasher = _hash_engine()
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
      debug_msg("detect_duplicates: hash {0:s} associated with files {1:s}\n".format(_hash,str(_files)))
      if len(_files) > 1 :
         _sizes = {}  # 2nd identity criterion - file size
         for _file in _files :
            append_or_insert(_sizes,os.path.getsize(_file),_file)
         debug_msg("detect_duplicates: hash {0:s} - files sizes {1:s}\n".format(_hash,str(_sizes)))
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

def report_duplicates(candidate_dir_dups,hash_collisions) :
   print(("\n*** directory tree: {0:d} hash collisions ***".format(hash_collisions)))
   if candidate_dir_dups :
      if options.format_dup == "csv" :
         for _dup in candidate_dir_dups :
            _msg = "\"DIR DUPLICATE\""
            _,_,_filenames = _dup
            for _dupname in _filenames :
               _msg += ",\"{0:s}\"".format(_dupname)
            print(_msg)
      else :
         for _dup in candidate_dir_dups :
            _msg = "DIR DUPLICATE: "
            _,_,_filenames = _dup
            for _dupname in _filenames :
               _msg += " \'{0:s}\'".format(_dupname)
            print(_msg)
   print(("\n*** directory tree: {0:d} duplicate sets detectes ***".format(len(candidate_dir_dups))))

class Mode(enum.Enum) :
   """Modes of operation"""
   unknown = False
   compute_hashes = "compute hashes"
   find_duplicates = "identify duplicates in dir"
   find_new_files = "find files in candidate dir absent in repository"
   deduplicate = "suggest which files in repository to keep (de-duplicate)"

###############################################
#
# the program starts here
#
###############################################
options = parse_args()

mode = Mode.unknown
#options = _result
if options.hash_store:
   mode = Mode.compute_hashes
if options.identify:
   if options.dirtree_count == 1:
      mode = Mode.find_duplicates
   elif options.dirtree_count == 2:
      mode = Mode.find_new_files
   else:
      error("Internal argument parsing error", True)
if options.suggest and options.dirtree_count == 2:
   mode = Mode.deduplicate
if not mode:
   error("Incorrect syntax!", True)
print("[AWSdebug] mode : '{}'".format(mode.value))

# get hashes for candidate directory
if options.dir_hashes:
   _hashes_candidate_dir = read_hashes(options.dir_hashes)
else:
   _hashes_candidate_dir = get_hashes(options.dir)
   if mode == Mode.compute_hashes:
      with open(options.hash_store, 'wb') as output_file:
         pickle.dump(options.dir, output_file)
         pickle.dump(_hashes_candidate_dir, output_file)
      exit(0)  # computing hashes precludes any other actions

# get hashes for repository, if applicable
if options.dirtree_count == 2 :
   if options.repo_hashes:
      _hashes_repository = read_hashes(options.repo_hashes)
   else:
      _hashes_repository = get_hashes(options.repository)

##################################
#  main program decision ladder
if mode == Mode.find_duplicates :
   # detect duplicates within dirtree
   _candidate_dir_dups,_hash_collisions = detect_duplicates(_hashes_candidate_dir)
   report_duplicates(_candidate_dir_dups,_hash_collisions)

elif mode == Mode.find_new_files :
   # identify files occurring only in candidate dir and absent from repository
   # (thus candidates for adding to repository)
   _uniq = []
   for _hash in sorted(_hashes_candidate_dir.keys()):
      # noinspection PyUnboundLocalVariable
      if _hash not in _hashes_repository:
         _uniq.extend(_hashes_candidate_dir[_hash])
   print("\n***** Files existing only in candidate directory: *****")
   for _f in sorted(_uniq): print(_f)

elif mode == Mode.deduplicate :
   # suggest which copy in repository to keep
   _cnt_decided = _cnt_undecided = 0
   _repository_dups,_hash_collisions = detect_duplicates(_hashes_candidate_dir)
   #report_duplicates(_repository_dups,_hash_collisions)
   for _hash,_size,_dups in _repository_dups :
      # first look up the file in reference dir
      if _hash in _hashes_candidate_dir :
         _decided = False
         _chosen = []
         _candidate_dir_locations = []
         for _candidate_dir_file in _hashes_candidate_dir[_hash] :
            _candidate_dir_locations.append(os.path.relpath(_candidate_dir_file,options.dir))
         for _dup in _dups :
            if os.path.relpath(_dup,options.repository) in _candidate_dir_locations :
               _decided = True
               _cnt_decided += 1
               _chosen.append(_dup)
         print("--- Duplicates : ---")
         print("REF: {0}".format(_hashes_candidate_dir[_hash][0]))
         for _dup in _dups :
            print("{0} : {1}".format(_dup,"hgw" if not _decided else "keep" if _dup in _chosen else "delete"))
            if options.delete :
               if _decided and _dup not in _chosen :
                  os.remove(_dup)
                  #print "os.remove({0})".format(_dup)
         if not _decided :
            _cnt_undecided += 1

print("\ncandidate dir : {0}\nrepository    : {1}".format(options.dir,options.repository))
#print "duplicates decided: {0:d}  undecided: {1:d}".format(_cnt_decided,_cnt_undecided)
