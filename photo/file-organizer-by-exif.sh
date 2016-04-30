#!/bin/bash

PREFIX="PHOTO_"

usage() {
  echo "Usage:"
  echo "   ${0##*/} {-h|--help}"
  echo "   ${0##*/} [photo_prefix] PHOTO_DIR"
  echo
  echo "This script will unify the names of all JPEG photos in the given directory (possibly with accompanying CR2 raw images), numbering them according to their EXIF timestamps."
  echo "It was written to deal with events photographed with several devices using different file naming schemes, e.g. a DSLR and mobile phone."
  echo "Resulting photo filenames will have the scheme:"
  echo "   PHOTO_0001.jpg"
  echo "(If photo_prefix is specified, it will replace the PHOTO part.)"
  [[ $# == 0 ]] && exit 0 || exit $1
}

error() {
  echo "[Error] $1" >&2
  exit 1
}

# sanity checks
which exiv2 >/dev/null || error "exiv2 tool is not available, aborting."

[[ $# == 1 || $# == 2 ]] || usage 1
[[ {"-h","--help"} =~ $1 ]] && usage 0
[[ $# == 2 ]] && { PREFIX=$1; shift; }

PHOTO_DIR=$1
[ -d "$PHOTO_DIR" ] || error "Photo directory $PHOTO_DIR does not exist!"
cd "$PHOTO_DIR"

PHOTO_CNT=$(ls -1 *.JPG *.jpg *.JPEG *.jpeg 2>/dev/null | wc -l)
[[ $PHOTO_CNT > 0 ]] && echo "Directory $PHOTO_DIR: $PHOTO_CNT photos found" || error "Photo directory $PHOTO_DIR contains no JPEG photos."
PHOTO_CNT_LEN=${#PHOTO_CNT}
#echo PHOTO_CNT_LEN = $PHOTO_CNT_LEN

# unify all filenames to *.jpg
echo "Unifying photo file extensions"
for FILE in $(ls *.JPG *.JPEG *.jpeg 2>/dev/null ); do mv "$FILE" "${FILE%\.*}.jpg"; done

# rename files to start with timestamp
echo "Renaming photos to include timestamps"
for i in *.jpg *.CR2; do exiv2 -r '%Y%m%d.%H%M%S.:basename:' rename $i; done

# rename files to uniform counter form
echo "Unifying photo names according to scheme ${PREFIX}nnnn.jpg"
N=0
for PHOTO in *.jpg; do
  printf -v FILENAME "${PREFIX}%0${PHOTO_CNT_LEN}d.jpg" $N
  #echo FILENAME = $FILENAME
  mv "$PHOTO" "$FILENAME"
  [ -e ${PHOTO/jpg/CR2} ] && mv "${PHOTO/jpg/CR2}" "${FILENAME/jpg/CR2"
  (( N += 1 ))
done

echo "Done. $N photos were processed."
