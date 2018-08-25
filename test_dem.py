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

from bounds import RasterBounds
from dem import MapzenDem
from sat_image.image import Landsat8


class MapzenDemTestCase(unittest.TestCase):
    def setUp(self):

        self.api_key = 'BJ5OM0JVTsWMEy_1kirKJA'
        self.dir_name_LC8 = '/home/dgketchum/IrrigationGIS/tests/gridmet/LC80380272014227LGN01'

    def test_dem(self):
        l8 = Landsat8(self.dir_name_LC8)
        polygon = l8.get_tile_geometry()
        profile = l8.rasterio_geometry
        bb = RasterBounds(affine_transform=profile['affine'],
                          profile=profile, latlon=True)

        dem = MapzenDem(zoom=10, bounds=bb, target_profile=profile,
                        clip_object=polygon,
                        api_key=self.api_key)

        elev = dem.terrain(attribute='elevation',
                           out_file='/home/dgketchum/IrrigationGIS/tests/mapzen_'
                                    '{}_{}.tif'.format(l8.target_wrs_path,
                                                       l8.target_wrs_row))
        self.assertEqual(elev.shape, (1, 7429, 8163))

        aspect = dem.terrain(attribute='aspect')
        self.assertEqual(aspect.shape, (7429, 8163))

        slope = dem.terrain(attribute='slope')
        self.assertEqual(slope.shape, (1, 7429, 8163))


if __name__ == '__main__':
    unittest.main()

# ===============================================================================
