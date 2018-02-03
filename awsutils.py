import sys

def error(msg, is_fatal=False):
   sys.stderr.write("{0:s} error: {1:s}\n".format("Fatal" if is_fatal else "Non-fatal", msg))
   if is_fatal: exit(1)


# references global options.debug flag, expected to be set up from invocation options
def debug_msg(msg):
   if options.debug:
      sys.stdout.write("[debug] {0:s}\n".format(msg))


