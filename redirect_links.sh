#!/bin/bash

usage() {
  echo "Usage:"
  echo "   ${0##*/} {-h|--help}"
  echo "   ${0##*/} [-b|--brokenonly] OLD NEW DIR"
  echo
  echo "This script will redirect all symbolic links, changing OLD to NEW in their target paths. Example:"
  echo "   ${0##*/} /usr/local/bin/ /opt/ ."
  echo "will redirect all symlinks to /usr/local/bin/... to analogous subpaths under /opt/"
  [[ $# == 0 ]] && exit 0 || exit $1
}

while [ 1 ]; do
  case $1 in 
    -h|--help) usage 0;;
    -b|--broken-only) COND="-xtype l"; shift ;;
    -v|--verbose) VERBOSE=1; shift ;;
    -n|--no-op) NOOP=1; shift ;;
    *) break;;
  esac
done

[[ $# == 3 ]] || usage 1

[ $NOOP ] && echo "Dry run only"

OLD=$1
NEW=$2
find "$3" -type l $COND -print0 | while IFS= read -r -d '' LINK; do
#for LINK in $( find "$3" -type l $COND -print0); do
  [ $VERBOSE ] && echo "Processing $LINK"
  DEST=$(readlink "$LINK")
  if echo $DEST | grep -q $OLD; then
    [ $VERBOSE ] && echo "Executing ln -fs \"${DEST/$OLD/$NEW}\" \"$LINK\""
    [ $NOOP ] || ln -fs "${DEST/$OLD/$NEW}" "$LINK"
  fi
done
