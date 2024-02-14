#!/usr/bin/python3
import sys
import re
import datetime
import argparse

sys.path.append("..")  # valid within full repo only, otherwise just copy the awsutils.py file to the same directory
import awsutils as aws_utils

TIMEFORMAT = "%Y-%m-%dT%H:%M:%SZ"  # acc. to datetime.strptime requirements
DURATIONFORMAT = "%H:%M:%S"  # acc. to datetime.strptime requirements


def parse_args():
   # parse arguments
   usage_text = (
      "Modifies a GPX file (GPS track data) using another (Viking-generated) GPX file as reference.\n"
      "Does not parse the files as GPX or even XML, simply treats them as text files.")
   epilog_text = (
      "Typical usage cases:\n"
      "  %(prog)s --input INFILE --reference REFERENCE_FILE --output OUTFILE\n"
      "                        : Filter INFILE, deleting track points not in REFERENCE_FILE\n"
      "*** not yet implemented beyond this point ***\n"
      "  %(prog)s --input INFILE --start STARTTIME --output OUTFILE\n"
      "                        : Time-shift GPX file so that the track starts at STARTTIME\n"
      "  %(prog)s --input INFILE --finish ENDTIME --output OUTFILE\n"
      "                        : Time-shift GPX file so that the track ends at ENDTIME\n"
      "  %(prog)s --input INFILE --start STARTTIME  --finish ENDTIME --output OUTFILE\n"
      "                        : Scale GPX file so that the track starts at STARTTIME and ends at ENDTIME.\n"
      "  %(prog)s --input INFILE --duration TOTALTIME --output OUTFILE\n"
      "                        : Scale GPX file so that the track starts at original time and lasts TOTALTIME.\n"
      "Expected date/time format: YYYY-mm-ddTHH:MM:SS, e.g. 2018-01-12T21:23:12\n"
      "Expected duration format: HH:MM:SS, e.g. 01:15:46\n"
   )
   parser = argparse.ArgumentParser(description=usage_text, epilog=epilog_text, \
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
   parser.add_argument("-i", "--input", required=True, metavar="INFILE", action="store", dest="infile",
                       help="input GPX file to read")
   parser.add_argument("-o", "--output", required=True, metavar="OUTFILE", action="store", dest="outfile",
                       help="output GPX file to write")
   parser.add_argument("-r", "--reference", required=False, metavar="REFERENCE_FILE", action="store", dest="reffile",
                       help="reference GPX file, specifies points to filter")
   time = parser.add_argument_group("time")
   time.add_argument("--start", metavar="STARTTIME", action="store", dest="starttime", help="desired track start time")
   time.add_argument("--finish", metavar="ENDTIME", action="store", dest="endtime", help="desired track end time")
   time.add_argument("--duration", metavar="DURATION", action="store", dest="duration", help="desired track duration")
   parser.add_argument("--debug", action="store_true", dest="debug", help="Print lots of debugging information")
   _result = parser.parse_args()
   
   # argument logic check
   if _result.starttime and _result.endtime and _result.duration:
      aws_utils.error("Specifying start time, end time and duration together makes no sense", True)
   
   return _result


def get_time_bounds(gpx):
   start_time = datetime.datetime(year=2099, month=1, day=1, hour=0, minute=0, second=0)
   finish_time = datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0, second=0)
   
   for track in gpx.tracks:
      for segment in track.segments:
         for point in segment.points:
            if point.time < start_time:
               start_time = point.time
            elif point.time > finish_time:
               finish_time = point.time
   return start_time, finish_time


###############################################
#
# the program starts here
#
###############################################

options = parse_args()

if options.reference :
   # FILTERING MODE; reference file is used as list of track points to be left in the input file

   refpoints = []
   
   with open(options.reffile) as reffile :
      is_in_trkpt = False
      for line in reffile:
         _line = line.strip()
         if _line.startswith("<trkpt ") :
            is_in_trkpt = True
         elif _line.endswith("</trkpt>") :
            is_in_trkpt = False
         elif is_in_trkpt and _line.startswith("<time>") and _line.endswith("</time>"):
            refpoints.append(_line)
   
   if not refpoints :
      aws_utils.error("Reference GPX file contains no track points",True)
      
   print(str(refpoints))
   refpoints.reverse()
   
   # Ye Olde State Machine
   is_in_trkpt = False
   trkpt_body = ""
   next_refpoint = refpoints.pop()
   is_valid_refpoint = False
   
   with open(options.outfile,"w") as outfile :
      with open(options.infile) as infile :
         for in_line in infile :
            _in_line = in_line.strip()
            if is_in_trkpt :
               if _in_line.startswith("<time>") and _in_line.endswith("</time>") :
                  if _in_line == next_refpoint :
                     is_valid_refpoint = True
            elif _in_line.startswith("<trkpt ") :
               is_in_trkpt = True
               
            if is_in_trkpt :
               trkpt_body += in_line
   
               if _in_line.startswith("</trkpt>") :
                  if is_valid_refpoint :
                     outfile.write(trkpt_body)
                     is_valid_refpoint = False
                     next_refpoint = refpoints.pop() if refpoints else "INVALID_TIMESTAMP"
                  is_in_trkpt = False
                  trkpt_body = ""
   
            else :
               outfile.write(in_line)

# FOR FUTURE REFERENCE
#
# rgx_time = re.compile(r"\s*<time>([^<]+)</time>\s*")
# with open(options.reffile) as reffile :
#    for line in reffile :
#       _time_str = rgx_time.match(line)
#       if _time_str :
#          debug_msg(_time_str.group(1))
#          _time = datetime.datetime.strptime(_time_str.group(1),TIMEFORMAT)
#          refpoints.append(_time)
