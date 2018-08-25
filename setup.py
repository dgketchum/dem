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

import os

from setuptools import setup

os.environ['TRAVIS_CI'] = 'True'

try:
    from setuptools import setup

    setup_kwargs = {}
except ImportError:
    from distutils.core import setup

    setup_kwargs = {}

with open('README.md') as f:
    readme = f.read()

tag = '0.0.1'

setup(name='opendem',
      version=tag,
      description='Very simple API to download, merge, resample, project DEM tiles from AWS and Thredds',
      long_description=readme,
      setup_requires=['nose>=1.0'],
      py_modules=[],
      license='Apache',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering :: GIS',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.6'],
      keywords='DEM digital elevation model',
      author='David Ketchum',
      author_email='dgketchum@gmail.com',
      platforms='Posix; MacOS X; Windows',
      packages=[],
      download_url='https://github.com/{}/{}/archive/{}.tar.gz'.format('dgketchum', 'dem', tag),
      url='https://github.com/dgketchum',
      test_suite='tests.test_dem',
      install_requires=['numpy', 'requests', 'scipy', 'future', 'rasterio', 'xarray'],
      **setup_kwargs)


# ============= EOF ==============================================================
