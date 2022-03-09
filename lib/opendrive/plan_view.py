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


class Geometry:
  def __init__(self, s, x, y, hdg, length):
    self.s = s
    self.x = x
    self.y = y
    self.hdg = hdg
    self.length = length

class Spiral(Geometry):
  def __init__(self, curv_start, curv_end):
    self.curv_start = curv_start
    self.curv_end = curv_end

class Arc(Geometry):
  def __init__(self, curvature):
    self.curvature = curvature

class ParamPoly3(Geometry):
  def __init__(self, aU, bU, cU, dU, aV, bV, cV, dV, pRange):
    self.aU = aU
    self.bU = bU
    self.cU = cU
    self.dU = dU
    self.aV = aV
    self.bV = bV
    self.cV = cV
    self.dV = dV
    self.pRange = pRange


class PlanView:
  def __init__(self):
    self.geometrys = None

  def add_geometry(self, geometry):
    self.geometrys.append(geometry)
