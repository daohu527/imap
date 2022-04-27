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


import math


class Transform:
  def __init__(self, x, y, z, yaw, roll, pitch) -> None:
    self.origin_x = x
    self.origin_y = y
    self.origin_z = z
    self.yaw = yaw
    self.roll = roll
    self.pitch = pitch

  def set_rotate(self, yaw = 0.0, roll = 0.0, pitch = 0.0) -> None:
    self.yaw = yaw
    self.roll = roll
    self.pitch = pitch

  def set_translate(self, x = 0.0, y = 0.0, z = 0.0) -> None:
    self.origin_x = x
    self.origin_y = y
    self.origin_z = z

  def transform(self, x, y, z):
    self.x, self.y, self.z = x, y, z
    self.r_yaw()
    self.r_roll()
    self.r_pitch()
    return self.translate()

  def r_yaw(self):
    x, y = self.x, self.y
    self.x = x * math.cos(self.yaw) - y * math.sin(self.yaw)
    self.y = x * math.sin(self.yaw) + y * math.cos(self.yaw)

  def r_roll(self):
    y, z = self.y, self.z
    self.y = y * math.cos(self.roll) + z * math.sin(self.roll)
    self.z = -y * math.sin(self.roll) + z * math.cos(self.roll)

  def r_pitch(self):
    x, z = self.x, self.z
    self.x = x * math.cos(self.pitch) - z * math.sin(self.pitch)
    self.z = x * math.sin(self.pitch) + z * math.cos(self.pitch)

  def translate(self):
    self.x += self.origin_x
    self.y += self.origin_y
    self.z += self.origin_z
    return self.x, self.y, self.z
