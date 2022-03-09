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
  def __init__(self, s, a, b, c, d):
    self.s = s
    self.a = a
    self.b = b
    self.c = c
    self.d = d


class ElevationProfile:
  def __init__(self):
    self.elevations = []

  def add_elevation(self, elevation):
    self.elevations.append(elevation)

class LateralProfile:
  def __init__(self):
    self.elevations = []

  def add_elevation(self, elevation):
    self.elevations.append(elevation)
