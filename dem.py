# =============================================================================================
# Copyright 2017 dgketchum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================================

from future.standard_library import hooks

with hooks():
    from urllib.parse import urlunparse

import os
import copy
from numpy import pi, log, tan, empty, float32, arctan, rad2deg, gradient
from numpy import arctan2, reshape, where
from itertools import product
from rasterio import open as rasopen
from rasterio.merge import merge
from rasterio.transform import Affine
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling, calculate_default_transform
from rasterio.crs import CRS
from requests import get
from scipy.ndimage import gaussian_gradient_magnitude
from tempfile import mkdtemp
from xarray import open_dataset


class BadRequestError(Exception):
    pass


class Dem(object):
    def __init__(self):
        pass

    @staticmethod
    def save(array, geometry, output_filename, crs=None, return_array=False):
        try:
            array = array.reshape(1, array.shape[1], array.shape[2])
        except IndexError:
            array = array.reshape(1, array.shape[0], array.shape[1])
        geometry['dtype'] = str(array.dtype)
        if crs:
            geometry['crs'] = CRS({'init': crs})
        with rasopen(output_filename, 'w', **geometry) as dst:
            dst.write(array)
        if return_array:
            return array
        return None


class ThreddsDem(Dem):
    """ Digital Elevation Model and Dertivatives from Gridmet
    
    4 km resolution
    
    This is usefull because it matches the resolution and grid geometry
    of the Gridmet meteorological datasets.
    
    :param BBox, bounding box
    """

    def __init__(self, bbox=None):
        Dem.__init__(self)
        self.bbox = bbox

    def thredds_dem(self):
        service = 'thredds.northwestknowledge.net:8080'
        scheme = 'http'

        url = urlunparse([scheme, service,
                          '/thredds/dodsC/MET/elev/metdata_elevationdata.nc',
                          '', '', ''])

        xray = open_dataset(url)

        subset = xray.loc[dict(lat=slice(self.bbox.north, self.bbox.south),
                               lon=slice(self.bbox.west, self.bbox.east))]

        xray.close()

        return subset


class AwsDem(Dem):
    def __init__(self, zoom=None, target_profile=None, bounds=None, clip_object=None):
        Dem.__init__(self)

        self.zoom = zoom
        self.target_profile = target_profile
        self.bbox = bounds
        self.clip_feature = clip_object
        self.url = 'https://s3.amazonaws.com/elevation-tiles-prod'
        self.base_gtiff = '/geotiff/{z}/{x}/{y}.tif'
        self.temp_dir = mkdtemp(prefix='collected-')
        self.files = []
        self.mask = []

    def terrain(self, out_file=None, attribute='elevation',
                mode=None, save_and_return=False):
        self.get_tiles()
        self.merge_tiles()
        self.reproject_tiles()
        if self.clip_feature:
            self.mask_dem()

        dem = self.resample()

        if attribute == 'elevation':
            if out_file:
                arr = self.save(dem, self.target_profile, out_file,
                                return_array=True)
                if save_and_return:
                    return arr
            else:
                return dem

        elif attribute == 'slope':
            slope = self.get_slope(dem, mode=mode)
            if out_file:
                if len(slope.shape) > 2:
                    slope = slope.reshape(1, dem.shape[1], dem.shape[2])
                arr = self.save(slope, self.target_profile, out_file,
                                return_array=True)
                if save_and_return:
                    return arr
            else:
                return slope

        elif attribute == 'aspect':
            aspect = self.get_aspect(dem)
            aspect = where(aspect > 2 * pi, 0, aspect)
            if out_file:
                if len(aspect.shape) > 2:
                    aspect = aspect.reshape(1, dem.shape[0], dem.shape[1])
                arr = self.save(aspect, self.target_profile, out_file,
                                return_array=True)
                if save_and_return:
                    return arr
            else:
                return aspect

        else:
            raise ValueError('Must choose attribute from '"elevation"', '"slope"', or '"aspect'.")

    @staticmethod
    def get_slope(dem, mode='percent'):
        slope = gaussian_gradient_magnitude(dem, 5, mode='nearest')
        if mode == 'percent':
            pass
        if mode == 'fraction':
            slope = slope / 100
        if mode == 'degrees':
            slope = rad2deg(arctan(slope / 100))

        return slope

    @staticmethod
    def get_aspect(dem):
        x, y = gradient(reshape(dem, (dem.shape[1], dem.shape[2])))
        aspect = arctan2(y, -x)
        return aspect

    @staticmethod
    def mercator(lat, lon, zoom):
        """ Convert latitude, longitude to z/x/y tile coordinate at given zoom.
        """
        # convert to radians
        x1, y1 = lon * pi / 180, lat * pi / 180

        # project to mercator
        x2, y2 = x1, log(tan(0.25 * pi + 0.5 * y1))

        # transform to tile space
        tiles, diameter = 2 ** zoom, 2 * pi
        x3, y3 = int(tiles * (x2 + pi) / diameter), int(tiles * (pi - y2) / diameter)

        return zoom, x3, y3

    def find_tiles(self):
        """ Convert geographic bounds into a list of tile coordinates at given zoom.
        """
        lat1, lat2 = self.bbox.south, self.bbox.north
        lon1, lon2 = self.bbox.west, self.bbox.east
        # convert to geographic bounding box
        minlat, minlon = min(lat1, lat2), min(lon1, lon2)
        maxlat, maxlon = max(lat1, lat2), max(lon1, lon2)

        # convert to tile-space bounding box
        _, xmin, ymin = self.mercator(maxlat, minlon, self.zoom)
        _, xmax, ymax = self.mercator(minlat, maxlon, self.zoom)

        # generate a list of tiles
        xs, ys = range(xmin, xmax + 1), range(ymin, ymax + 1)
        tile_list = [(self.zoom, x, y) for (y, x) in product(ys, xs)]

        return tile_list

    def get_tiles(self):

        base_url = '{}{}'.format(self.url, self.base_gtiff)

        # https://tile.nextzen.org/tilezen/terrain/v1/geotiff/{z}/{x}/{y}.tif?api_key=your-nextzen-api-key
        for (z, x, y) in self.find_tiles():
            url = base_url.format(z=z, x=x, y=y)
            req = get(url, verify=False, stream=True)
            if req.status_code != 200:
                raise BadRequestError

            temp_path = os.path.join(self.temp_dir, '{}-{}-{}.tif'.format(z, x, y))
            with open(temp_path, 'wb') as f:
                f.write(req.content)
                self.files.append(temp_path)

    def merge_tiles(self):
        raster_readers = [rasopen(f, 'r') for f in self.files]
        reproj_bounds = self.bbox.to_web_mercator()
        setattr(self, 'web_mercator_bounds', reproj_bounds)
        array, transform = merge(raster_readers, bounds=reproj_bounds)
        del raster_readers
        setattr(self, 'merged_array', array)
        setattr(self, 'merged_transform', transform)

        with rasopen(self.files[0], 'r') as f:
            setattr(self, 'merged_profile', f.profile)
        self.merged_profile.update({'height': array.shape[1], 'width': array.shape[2],
                                    'transform': transform})

    def reproject_tiles(self):

        reproj_path = os.path.join(self.temp_dir, 'tiled_reproj.tif')
        setattr(self, 'reprojection', reproj_path)

        profile = copy.deepcopy(self.target_profile)
        profile['dtype'] = float32
        bb = self.web_mercator_bounds
        bounds = (bb[0], bb[1],
                  bb[2], bb[3])
        dst_affine, dst_width, dst_height = calculate_default_transform(self.merged_profile['crs'],
                                                                        profile['crs'],
                                                                        self.merged_profile['width'],
                                                                        self.merged_profile['height'],
                                                                        *bounds)

        profile.update({'crs': profile['crs'],
                        'transform': dst_affine,
                        'width': dst_width,
                        'height': dst_height})

        with rasopen(reproj_path, 'w', **profile) as dst:
            dst_array = empty((1, dst_height, dst_width), dtype=float32)

            reproject(self.merged_array, dst_array, src_transform=self.merged_transform,
                      src_crs=self.merged_profile['crs'], dst_crs=self.target_profile['crs'],
                      dst_transform=dst_affine, resampling=Resampling.cubic,
                      num_threads=2)

            dst.write(dst_array.reshape(1, dst_array.shape[1], dst_array.shape[2]))

        delattr(self, 'merged_array')

    def mask_dem(self):

        temp_path = os.path.join(self.temp_dir, 'masked_dem.tif')

        with rasopen(self.reprojection) as src:
            out_arr, out_trans = mask(src, self.clip_feature, crop=True,
                                      all_touched=True)
            out_meta = src.meta.copy()
            out_meta.update({'driver': 'GTiff',
                             'height': out_arr.shape[1],
                             'width': out_arr.shape[2],
                             'transform': out_trans})

        with rasopen(temp_path, 'w', **out_meta) as dst:
            dst.write(out_arr)

        setattr(self, 'mask', temp_path)
        delattr(self, 'reprojection')

    def resample(self):

        temp_path = os.path.join(self.temp_dir, 'resample.tif')

        if self.mask:
            ras = self.mask
        else:
            ras = self.reprojection

        with rasopen(ras, 'r') as src:
            array = src.read(1)
            profile = src.profile
            res = src.res
            try:
                target_affine = self.target_profile['affine']
            except KeyError:
                target_affine = self.target_profile['transform']
            target_res = target_affine.a
            res_coeff = res[0] / target_res

            new_array = empty(shape=(1, round(array.shape[0] * res_coeff - 2),
                                     round(array.shape[1] * res_coeff)), dtype=float32)
            aff = src.affine
            new_affine = Affine(aff.a / res_coeff, aff.b, aff.c, aff.d, aff.e / res_coeff, aff.f)

            profile['transform'] = self.target_profile['transform']
            profile['width'] = self.target_profile['width']
            profile['height'] = self.target_profile['height']
            profile['dtype'] = str(array.dtype)

            with rasopen(temp_path, 'w', **profile) as dst:
                reproject(array, new_array, src_transform=aff,
                          dst_transform=new_affine, src_crs=src.crs,
                          dst_crs=src.crs, resampling=Resampling.bilinear)

                dst.write(new_array)

            return new_array


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
