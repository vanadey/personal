#/bin/bash

usage() {
    echo "Usage:"
    echo "$0 <archives>..."
    exit 1
}

if [[ $# < 0 ]]; then usage; fi

TMP_DIR=$(mktemp -d)

until [ -z "$1" ]; do
    [ -e "$1" ] || { echo "Cannot find archive $1"; continue; }
    LANG=pl_PL 7z e -o$TMP_DIR "$1"
    ls -l $TMP_DIR
    convmv --notest -f CP852 -t UTF8 -r $TMP_DIR
    mv $TMP_DIR/* .
    shift || break
    echo "$1"
done

rm -r $TMP_DIR
