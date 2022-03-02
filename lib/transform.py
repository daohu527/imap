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
    self.x = x
    self.y = y
    self.z = z
    self.yaw = yaw
    self.roll = roll
    self.pitch = pitch

  def roll(self):
    y, z = self.y, self.z
    self.y = y * math.cos() + z * math.sin()
    self.z = -y * math.sin() + z * math.cos()

  def pitch(self):
    x, z = self.x, self.z
    self.x = x * math.cos() - z * math.sin()
    self.z = x * math.sin() + z * math.cos()

  def yaw(self):
    x, y = self.x, self.y
    self.x = x * math.cos() - y * math.sin()
    self.y = x * math.sin() + y * math.cos()
