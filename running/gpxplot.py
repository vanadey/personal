#!/usr/bin/python3

from os import listdir
from os.path import isfile, join
import sys
import matplotlib.pyplot as plt
import gpxpy
import argparse


def parse_args() :
   # parse arguments
   usage_text = (
      "Plots all GPX tracks from a specified directory.")
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
   parser.add_argument("dirs", metavar="DIR", nargs="+", help="directories containing GPX files to plot")
   parser.add_argument("-o","--output", required=True, metavar="OUTFILE", action="store", dest="outfile", help="output image file")
   parser.add_argument("-f","--format", required=False, metavar="FORMAT", action="store", dest="outformat", \
                       choices=["png","svg","pdf","ps","eps"], default="png", help="output image file format")
   parser.add_argument("--debug", action="store_true", dest="debug", help="Print lots of debugging information")
   _result = parser.parse_args()

   # argument logic check

   return _result


def error(msg,is_fatal = False) :
   sys.stderr.write("{0:s} error: {1:s}\n".format("Fatal" if is_fatal else "Non-fatal",msg))
   if is_fatal : exit (1)


def debug_msg(msg) :
   if options.debug :
      sys.stdout.write("[debug] {0:s}\n".format(msg))


###############################################
#
# the program starts here
#
###############################################

options = parse_args()

data = []
for data_dir in options.dirs :
   for data_file in listdir(data_dir) :
      full_data_path = join(data_dir,data_file)
      if isfile(full_data_path) :
         data.append(full_data_path)

lat = []
lon = []

fig = plt.figure(facecolor = '0.05')
ax = plt.Axes(fig, [0., 0., 1., 1.], )
#ax.autoscale(enable=True,tight=True)
ax.set_aspect('equal')
ax.set_axis_off()
fig.add_axes(ax)

for gpx_filename in data:
    gpx_file = open(gpx_filename, 'r')
    gpx = gpxpy.parse(gpx_file)

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                lat.append(point.latitude)
                lon.append(point.longitude)
    plt.plot(lon, lat, color = 'deepskyblue', lw = 0.2, alpha = 0.8)
    lat = []
    lon = []

if not options.outfile.endswith(options.outformat) :
   options.outfile += "." + options.outformat
plt.savefig(options.outfile, facecolor = fig.get_facecolor(), bbox_inches='tight', pad_inches=0, dpi=300, format=options.outformat)