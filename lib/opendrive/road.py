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

from lib.opendrive.plan_view import PlanView
from lib.opendrive.profile import ElevationProfile, LateralProfile
from lib.opendrive.lanes import Lanes

# Type
class Speed:
  def __init__(self, max_speed, unit):
    self.max_speed = max_speed
    self.unit = unit

class RoadType():
  def __init__(self, s, road_type):
    self.s = s
    self.road_type = road_type

  def add_speed(self, speed):
    self.speed = speed

# Link
class RoadLink:
  def __init__(self, element_type, element_id, contact_point):
    self.element_type = element_type
    self.element_id = element_id
    self.contact_point = contact_point

class Link:
  def __init__(self, predecessor, successor):
    self.predecessor = predecessor
    self.successor = successor


# Road
class Road:
  def __init__(self, name, length, road_id, junction_id):
    self.name = name
    self.length = length
    self.road_id = road_id
    self.junction_id = junction_id

    self.link = None
    self.plan_view = None
    self.elevation_profile = None
    self.lateral_profile = None
    self.lanes = None
