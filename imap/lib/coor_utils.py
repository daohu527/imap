#!/usr/bin/env python

# Copyright 2022 daohu527 <daohu527@gmail.com>
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
"""Convert between latitude and longitude and Utm coordinates
"""

from pyproj import Proj


def latlon_to_utm(latitude, longitude, zone_id):
    """latitude and longitude to UTM

    Args:
        latitude (float): latitude
        longitude (float): longitude
        zone_id (int): zone id

    Returns:
        float, float: utm_x, utm_y
    """
    p = Proj(proj='utm', zone=zone_id, ellps='WGS84', preserve_units=True)
    return p(latitude, longitude)

def utm_to_latlon(x, y, zone_id):
    """UTM to latitude and longitude

    Args:
        x (float): utm_x
        y (float): utm_y
        zone_id (int): zone id

    Returns:
        float, float: latitude, longitude
    """
    p = Proj(proj='utm', zone=zone_id, ellps='WGS84', preserve_units=True)
    return p(x, y, inverse=True)
