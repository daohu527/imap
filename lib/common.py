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


class Vector3d:
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z

  def __add__(self, other):
    self.x += other.x
    self.y += other.y
    self.z += other.z
    return self

  def __str__(self):
    return "Vector3d x: {}, y: {}, z: {}".format(self.x, self.y, self.z)

class Point3d:
  def __init__(self, x, y, z, s):
    self.x = x
    self.y = y
    self.z = z
    self.s = s

  def set_rotate(self, yaw = 0.0, roll = 0.0, pitch = 0.0):
    self.yaw = yaw
    self.roll = roll
    self.pitch = pitch

  def __str__(self):
    return "Point3d x: {}, y: {}, z: {}, s: {}, heading: {}".format(self.x, \
        self.y, self.z, self.s, self.yaw)
