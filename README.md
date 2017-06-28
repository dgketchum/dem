# dem
Collect elevation data from MapZen or Thredds, merge, reproject, resample.

Return elevation, aspect, or slope, that has been correctly transformed to fit rasters you are already working on.

Pulls a web map tile service (MapZen) list of tiles, based on input zoom level and bounding box, merges it,
reprojects it, and resamples it to a raster you are working with.

This is intended for work where one needs a dem (elevation), slope, or aspect in a grid that matches another
dataset they are working on.  

For example, I work on Landsat images that come in WGS UTM coordinate reference systems.  With [bounds](),
[satellite_image](), and [Landsat578](), I can easily download and unzip a Landsat scene, read it into a
Landsat5 (7, 8) object, get pass the object attributes to dem, and get back a numpy array that is reprojected
into the same local coordinate system for accurate scientific analysis.

This is intended to replace the task of downloading NED files and going through a long process in a GIS to 
reproject, resample, etc, which often requires time consuming file management and use of proprietary software.


