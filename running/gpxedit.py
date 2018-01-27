#!/usr/bin/python3
import sys
import gpxpy
import datetime
#from datetime import datetime
import argparse


TIMEFORMAT = "%Y-%m-%dT%H:%M:%S"  # acc. to datetime.strptime requirements
DURATIONFORMAT = "%H:%M:%S"  # acc. to datetime.strptime requirements

def parse_args() :
   # parse arguments
   usage_text = (
      "Modifies a GPX file (GPS track data).")
   epilog_text= (
      "Typical usage cases:\n"
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
   parser = argparse.ArgumentParser(description=usage_text,epilog=epilog_text,\
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
   parser.add_argument("-i","--input", required=True, metavar="INFILE", action="store", dest="infile", help="input GPX file to read")
   parser.add_argument("-o","--output", required=True, metavar="OUTFILE", action="store", dest="outfile", help="output GPX file to write")
   time = parser.add_argument_group("time")
   time.add_argument("--start", metavar="STARTTIME", action="store", dest="starttime", help="desired track start time")
   time.add_argument("--finish", metavar="ENDTIME", action="store", dest="endtime", help="desired track end time")
   time.add_argument("--duration", metavar="DURATION", action="store", dest="duration", help="desired track duration")
   parser.add_argument("--debug", action="store_true", dest="debug", help="Print lots of debugging information")
   _result = parser.parse_args()

   # argument logic check
   if _result.starttime and _result.endtime and _result.duration :
      error("Specifying start time, end time and duration together makes no sense", True)

   return _result


def error(msg,is_fatal = False) :
   sys.stderr.write("{0:s} error: {1:s}\n".format("Fatal" if is_fatal else "Non-fatal",msg))
   if is_fatal : exit (1)


def debug_msg(msg) :
   if options.debug :
      sys.stdout.write("[debug] {0:s}\n".format(msg))


def get_time_bounds(gpx) :
   start_time = datetime.datetime(year=2099, month=1, day=1, hour=0, minute=0, second=0)
   finish_time = datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0, second=0)
   
   for track in gpx.tracks:
      for segment in track.segments:
         for point in segment.points:
            if point.time < start_time:
               start_time = point.time
            elif point.time > finish_time:
               finish_time = point.time
   return start_time,finish_time


###############################################
#
# the program starts here
#
###############################################

options = parse_args()

gpx_file = open(options.infile,"r")
gpx = gpxpy.parse(gpx_file)

lat = []
lon = []
timestamps = []

# not really needed for time-shift only, but who cares...
start_time_original, finish_time_original = get_time_bounds(gpx)
debug_msg("Original start/end: " + str(start_time_original) + " - " + str(finish_time_original))
duration_original = finish_time_original - start_time_original
debug_msg("Original duration = " + str(duration_original))

if options.starttime and not options.duration and not options.endtime :
   # time-shift only
   start_time = datetime.strptime(options.starttime,TIMEFORMAT)
   debug_msg("Computed finish time = " + str(start_time + duration_original))
   time_scaling_factor = 1
elif not options.starttime and not options.duration and options.endtime :
   # time-shift only by finish time
   finish_time = datetime.strptime(options.endtime,TIMEFORMAT)
   start_time = finish_time - duration_original
   debug_msg("Computed start time = " + str(start_time))
   time_scaling_factor = 1
elif options.starttime and options.duration and not options.endtime :
   # time-shift by start time & time scaling
   start_time = datetime.strptime(options.starttime,TIMEFORMAT)
   duration = datetime.strptime(options.duration,"%H:%M:%S") - datetime.strptime("00:00:00","%H:%M:%S")
   debug_msg("Desired duration = " + str(duration))
   time_scaling_factor = duration / duration_original
   debug_msg("Computed finish time = " + str(start_time + duration_original * time_scaling_factor))
elif options.starttime and not options.duration and options.endtime :
   # time-shift by start time & time scaling to fit into explicit period
   start_time = datetime.strptime(options.starttime,TIMEFORMAT)
   finish_time = datetime.strptime(options.endtime,TIMEFORMAT)
   duration = finish_time - start_time
   debug_msg("Desired duration = " + str(duration))
   time_scaling_factor = duration / duration_original
else :
   error("Unrecognized time argument combination",True)

debug_msg("Time scaling factor = " + str(time_scaling_factor))




for track in gpx.tracks:
   for segment in track.segments:
      for point in segment.points:
         offset = point.time - start_time_original
         point.time = start_time + offset*time_scaling_factor

with open(options.outfile, 'w') as outfile :
   outfile.write(gpx.to_xml())
