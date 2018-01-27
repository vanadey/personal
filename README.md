# personal
Short programs for Linux workstation administration and hobby stuff

## photo
Photography-related stuff

> ### file-organizer-by-exif.sh
> Rename image files according to a uniform scheme, sorted by EXIF timestamp.
> Written to sort photos captured with different cameras using different naming schemes.
> 
> ### dir-renamer-by-exif.py
> Rename image directories by EXIF dates. Written to organise a large repository of photos, organised in directories by event.

## redirect_links.sh
Batch-redirect softlinks after moving the target directory.

## unzip_pl.sh
Unpack a ZIP archive created on MS Windows and containing Polish characters in filenames. (MS Windows uses an 8-bit codepage, CP-1250, for encoding Polish chars in this context).

## unzip_win.py
Unpack a (non-standard-compliant) ZIP archive created on MS Windows and containing Windows path separators (\). (ZIP file format specification mandates using slashes / regardless of OS, but some Windows archivers disobey this.)

## grepdoc
Search ODT and DOC files in the current directory for the specified term (`grep -ql {}`)

## running
Utilities related to running and presenting run tracks

> ### bpmcalc.sh
> Analyse MP3 files in the specified directories and compute their tempo (BPM).
> Useful for composing playlists for training running with specific cadence.
>
> ### gpxedit.py
> Modify GPX tracks: alter exercise date&time, scale track duration.
> 
> ### gpxplot.py
> Plot multiple GPX data files on single canvas, visualising overall track distribution.
> Slightly modified code by Andy Kee (http://andykee.com/visualizing-strava-tracks-with-python.html).

More to come...
