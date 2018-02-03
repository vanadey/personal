Why process GPX data?

I use an old smartphone with flaky GPS receiver. Occasionally, I get periods of degraded GPS accuracy, resulting in 
wildly-hopping track points; these can be deleted in a GPS editor like `Viking`, but the resulting track does not 
contain all the original information and can only be used as reference template for filtering the original file.

Also, I sometimes get large gaps in recorded track. As I run a small set of routes repeatedly, I can "transplant" the 
missing fragment from an archived track, but its timestamps must then be shifted and scaled to match the rest of the run.

# gpxtxfm (GPX Transformation)
Script for transforming Strava GPX files.

Strava files are GPX, so they can be processed as generic XML or using a format-aware parser like `gpx-py`. 
However, in the beginning of 2018 no Python GPX processing library supported heart rate data (stored as GPX extension).
As these data files are formatted in a human-friendly way, one tag per line, simple transformations are much easier done
by treating the files as text. This is the approach **gpxtxfm** implements.

# gpxedit

Uses `gpx-py` to perform operations on recorded GPX tracks:
* shift track in time, so that it starts or ends at specific moment
* scale track for specific duration

I realised that `gpx-py` does not support GPX extensions and thus loses heart rate data. That is why I abandoned this 
approach and started working on **GPX Transformation**.
