# ===============================================================================
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
# ===============================================================================

import unittest

from rasterio import open as rasopen

from bounds import RasterBounds
from dem import AwsDem
from sat_image.image import Landsat8


class AwsDemTestCase(unittest.TestCase):
    def setUp(self):
        self.dir_name_LC8 = '/home/dgketchum/IrrigationGIS/tests/gridmet/LC80380272014227LGN01'
        self.raster = '/home/dgketchum/IrrigationGIS/tests/LE07_clip_L1TP_039027_20130726_20160907_01_T1_B3.TIF'

    def test_dem(self):
        l8 = Landsat8(self.dir_name_LC8)
        polygon = l8.get_tile_geometry()
        profile = l8.rasterio_geometry
        bb = RasterBounds(affine_transform=profile['affine'],
                          profile=profile, latlon=True)

        dem = AwsDem(zoom=10, target_profile=profile, bounds=bb, clip_object=polygon)

        elev = dem.terrain(attribute='elevation',
                           out_file='/home/dgketchum/IrrigationGIS/tests/mapzen_'
                                    '{}_{}.tif'.format(l8.target_wrs_path,
                                                       l8.target_wrs_row))
        self.assertEqual(elev.shape, (1, 7429, 8163))

        aspect = dem.terrain(attribute='aspect')
        self.assertEqual(aspect.shape, (7429, 8163))

        slope = dem.terrain(attribute='slope')
        self.assertEqual(slope.shape, (1, 7429, 8163))

    def test_other_raster_dem(self):
        with rasopen(self.raster) as src:
            profile = src.profile
        bound_box = RasterBounds(affine_transform=profile['affine'],
                                 profile=profile)
        dem = AwsDem(zoom=10, target_profile=profile, bounds=bound_box)
        dem.terrain(attribute='elevation',
                    out_file='/home/dgketchum/IrrigationGIS/tests/mapzen_'
                             'image_clip_dem.tif')

    def test_other_raster_slope(self):
        with rasopen(self.raster) as src:
            profile = src.profile
        bound_box = RasterBounds(affine_transform=profile['affine'],
                                 profile=profile)
        dem = AwsDem(zoom=10, target_profile=profile, bounds=bound_box)
        dem.terrain(attribute='slope',
                    out_file='/home/dgketchum/IrrigationGIS/tests/mapzen_'
                             'image_clip_slope.tif')

    def test_other_raster_aspect(self):
        with rasopen(self.raster) as src:
            profile = src.profile
        bound_box = RasterBounds(affine_transform=profile['affine'],
                                 profile=profile)
        dem = AwsDem(zoom=10, target_profile=profile, bounds=bound_box)
        dem.terrain(attribute='aspect',
                    out_file='/home/dgketchum/IrrigationGIS/tests/mapzen_'
                             'image_clip_aspect.tif')


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
