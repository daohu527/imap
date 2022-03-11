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
    self.s = float(raw_elevation.attrib.get('a'))
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


class LateralProfile:
  def __init__(self):
    self.elevations = []

  def add_elevation(self, elevation):
    self.elevations.append(elevation)

  def parse_from(self, raw_lateral_profile):
    if not raw_lateral_profile:
      return

    for raw_elevation in raw_lateral_profile.iter('superelevation'):
      elevation = Elevation()
      elevation.parse_from(raw_elevation)
      self.add_elevation(elevation)
