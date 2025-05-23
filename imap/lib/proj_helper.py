#!/usr/bin/env python3

# Copyright 2021 daohu527 <daohu527@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

###############################################################################
# Copyright 2022 The Apollo Authors. All Rights Reserved.
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
###############################################################################

import pyproj
import math


def projected2latlon(x, y, zone_id=None, proj_txt=None):
    """utm to latlon"""
    if proj_txt is None or '+proj' not in proj_txt:
        # Default: Inverse Standard UTM
        if zone_id is None:
            raise ValueError(
                "For default inverse UTM, 'zone_id' parameter is required.")
        proj = pyproj.Proj(proj='utm', zone=zone_id, ellps='WGS84')
    else:
        proj = pyproj.Proj(proj_txt)
    lon, lat = proj(x, y, inverse=True)
    return lat, lon


def latlon2projected(lat, lon, proj_txt=None):
    """latlon to utm use proj info"""
    zone_id = latlon2utmzone(lat, lon)
    if proj_txt is None or '+proj' not in proj_txt:
        # Default: Standard UTM
        proj = pyproj.Proj(proj='utm', zone=zone_id, ellps='WGS84')
    else:
        proj = pyproj.Proj(proj_txt)
    x, y = proj(lon, lat)
    return x, y, zone_id


def latlon2utmzone(lat, lon):
    """latlon to utm zone"""
    zone_num = math.floor((lon + 180) / 6) + 1
    if 56.0 <= lat < 64.0 and 3.0 <= lon < 12.0:
        zone_num = 32
    if 72.0 <= lat < 84.0:
        if 0.0 <= lon < 9.0:
            zone_num = 31
        elif 9.0 <= lon < 21.0:
            zone_num = 33
        elif 21.0 <= lon < 33.0:
            zone_num = 35
        elif 33.0 <= lon < 42.0:
            zone_num = 37
    return zone_num
