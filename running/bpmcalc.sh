#!/bin/bash
usage() {
  echo "Usage:"
  echo "$0 PATH [PATH1] [PATH2] ..."
  echo "     – will look for *.mp3 files in PATHs,"
  echo "       compute their bpm and print tab-delimited output"
  [[ $# == 0 ]] && exit 0 || exit $1
}

[[ $# > 0 ]] || usage 1


process() {
  echo "Processing directory $1..."
  find "$1" -name "*.mp3" -type f \
    -exec echo -ne "{}\t" \; \
    -exec sh -c 'sox "{}" -t raw -r 44100 -e float -c 1 -V1 - | bpm -m 40 -x 220 -f "%0.f" 2>/dev/null' \;
}

while [ "$1" ]; do
  case "$1" in
    -h|--help) usage 0;;
    *) process "$1"; shift;;
  esac
done

