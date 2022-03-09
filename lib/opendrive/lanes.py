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


## LaneOffset
class LaneOffset:
  def __init__(self, s, a, b, c, d):
    self.s = s
    self.a = a
    self.b = b
    self.c = c
    self.d = d

# Lane
class LaneLink:
  def __init__(self, lane_id):
    self.lane_id = lane_id


class Link:
  def __init__(self, predecessor, successor):
    self.predecessor = predecessor
    self.successor = successor


class Width:
  def __init__(self, sOffset, a, b, c, d):
    self.sOffset = sOffset
    self.a = a
    self.b = b
    self.c = c
    self.d = d

class RoadMark:
  def __init__(self, sOffset, roadmark_type, material, width, lane_change):
    self.sOffset = sOffset
    self.roadmark_type = roadmark_type
    self.material = material
    self.width = width
    self.lane_change = lane_change


## UserData
class VectorLane:
  def __init__(self, travel_dir):
    self.travel_dir = travel_dir

class UserData:
  def __init__(self):
    self.vector_lane = None

class Lane:
  def __init__(self, lane_id, lane_type, level):
    self.lane_id = lane_id
    self.lane_type = lane_type
    self.level = level
    self.link = None
    self.width = None
    self.road_mark = None
    self.user_data = None

class LaneSection:
  def __init__(self):
    self.left = []
    self.center = None
    self.right = []

# Lanes
class Lanes:
  def __init__(self):
    self.lane_offsets = []
    self.lane_sections = []
