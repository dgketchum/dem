# dem
See test_dem.py for examples of how this is used.

Collect elevation data from AWS or Thredds, merge, reproject, resample.

No API key needed!

Return elevation, aspect, or slope, that has been correctly transformed to fit rasters you are already working on.

![alt text](http://url/to/img.png)

Pulls a web map tile service (AWS) list of tiles, based on input zoom level and bounding box, merges it,
reprojects it, and resamples it to a raster you are working with.

This is intended for work where one needs a dem (elevation), slope, or aspect in a grid that matches another
dataset they are working on.  

For example, I work on Landsat images that come in WGS UTM coordinate reference systems.  With [bounds](https://github.com/dgketchum/bounds),
[satellite_image](https://github.com/dgketchum/satellite_image), and [Landsat578](https://github.com/dgketchum/Landsat578), I can easily download and unzip a Landsat scene, read it into a
Landsat5 (or 7, 8) object, pass the object attributes to dem, and get back a numpy array that is reprojected
into the same local coordinate system for accurate scientific analysis with the cloud mask, reflectance, albedo and other
handy data returned by methods in satellite_image.

This is intended to replace the task of downloading NED files and going through a long process in a GIS to 
merge, reproject, resample, etc, which often requires time consuming file management and use of proprietary software.

This pulls elevation data from the web, much like an app on your phone does.  Don't spend all your time dealing with
NED tiles!

Big ups to [rasterio](https://github.com/mapbox/rasterio).
