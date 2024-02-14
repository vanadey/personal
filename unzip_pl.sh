#/bin/bash

usage() {
    printf "$0 : Unpack ZIP archive with Windows-encoded Polish characters in file/dir names\n"
    printf "Usage:\n"
    printf "$0 <archives>...\n"
    exit 1
}

if [[ $# < 0 ]]; then usage; fi
if [[ $# == 1 ]] && [[ "$1" == "--help" || "$1" == "-h" ]]; then usage; fi

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
