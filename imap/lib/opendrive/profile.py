#!/usr/bin/env python

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


class Elevation:
  def __init__(self, s = None, a = None, b = None, c = None, d = None):
    self.s = s
    self.a = a
    self.b = b
    self.c = c
    self.d = d

  def parse_from(self, raw_elevation):
    self.s = float(raw_elevation.attrib.get('s'))
    self.a = float(raw_elevation.attrib.get('a'))
    self.b = float(raw_elevation.attrib.get('b'))
    self.c = float(raw_elevation.attrib.get('c'))
    self.d = float(raw_elevation.attrib.get('d'))


class ElevationProfile:
  def __init__(self):
    self.elevations = []

  def add_elevation(self, elevation):
    self.elevations.append(elevation)

  def parse_from(self, raw_elevation_profile):
    if not raw_elevation_profile:
      return

    for raw_elevation in raw_elevation_profile.iter('elevation'):
      elevation = Elevation()
      elevation.parse_from(raw_elevation)
      self.add_elevation(elevation)

  def get_elevation_by_s(self, s):
    i = len(self.elevations) - 1
    while i >= 0:
      elevation = self.elevations[i]
      if s >= elevation.s:
        a, b, c, d = elevation.a, elevation.b, elevation.c, elevation.d
        ds = s - elevation.s
        elev = a + b*ds + c*ds*ds + d*ds**3
        return elev
      i -= 1
    return 0.0


class LateralProfile:
  def __init__(self):
    self.superelevations = []

  def add_elevation(self, elevation):
    self.superelevations.append(elevation)

  def parse_from(self, raw_lateral_profile):
    if not raw_lateral_profile:
      return

    for raw_elevation in raw_lateral_profile.iter('superelevation'):
      elevation = Elevation()
      elevation.parse_from(raw_elevation)
      self.add_elevation(elevation)

  def get_superelevation_by_s(self, s):
    i = len(self.superelevations) - 1
    while i >= 0:
      superelevation = self.superelevations[i]
      if s >= superelevation.s:
        a = superelevation.a
        b = superelevation.b
        c = superelevation.c
        d = superelevation.d
        ds = s - superelevation.s
        elev = a + b*ds + c*ds*ds + d*ds**3
        return elev
      i -= 1
    return 0.0
