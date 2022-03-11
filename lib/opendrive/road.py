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

from lib.opendrive.common import convert_speed
from lib.opendrive.plan_view import PlanView
from lib.opendrive.profile import ElevationProfile, LateralProfile
from lib.opendrive.lanes import Lanes


GEOMETRY_SKIP_LENGTH = 0.01
SAMPLING_LENGTH = 1.0


# Type
class Speed:
  def __init__(self, max_speed = None, unit = None):
    self.max_speed = max_speed
    self.unit = unit

  def parse_from(self, raw_speed):
    raw_max_speed = raw_speed.attrib.get('max')
    self.unit = raw_speed.attrib.get('unit')
    self.max_speed = convert_speed(raw_max_speed, self.unit)


class RoadType:
  def __init__(self, s = None, road_type = None):
    self.s = s
    self.road_type = road_type

  def add_speed(self, speed):
    self.speed = speed

  def parse_from(self, raw_road_type):
    if raw_road_type:
      self.s = raw_road_type.attrib.get('s')
      self.road_type = raw_road_type.attrib.get('type')

      raw_speed = raw_road_type.find('speed')
      speed = Speed()
      speed.parse_from(raw_speed)
      self.add_speed(speed)

# Link
class RoadLink:
  def __init__(self, element_type = None, element_id = None, \
               contact_point = None):
    self.element_type = element_type
    self.element_id = element_id
    self.contact_point = contact_point

  def parse_from(self, raw_data):
    self.element_type = raw_data.attrib.get('elementType')
    self.element_id = raw_data.attrib.get('elementId')
    self.contact_point = raw_data.attrib.get('contactPoint')

class Link:
  def __init__(self, predecessor = None, successor = None):
    self.predecessor = RoadLink()
    self.successor = RoadLink()

  def parse_from(self, raw_link):
    raw_predecessor = raw_link.find('predecessor')
    self.predecessor.parse_from(raw_predecessor)

    raw_successor = raw_link.find('successor')
    self.successor.parse_from(raw_successor)

# Road
class Road:
  def __init__(self, name = None, length = None, road_id = None, \
               junction_id = None):
    self.name = name
    self.length = length
    self.road_id = road_id
    self.junction_id = junction_id

    self.link = Link()
    self.road_type = RoadType()
    self.plan_view = PlanView()
    self.elevation_profile = ElevationProfile()
    self.lateral_profile = LateralProfile()
    self.lanes = Lanes()

    # private
    self.reference_line = []

  def parse_from(self, raw_road):
    self.name = raw_road.attrib.get('name')
    self.length = float(raw_road.attrib.get('length'))
    self.road_id = raw_road.attrib.get('id')
    self.junction_id = raw_road.attrib.get('junction')

    raw_link = raw_road.find('link')
    self.link.parse_from(raw_link)

    raw_road_type = raw_road.find('type')
    self.road_type.parse_from(raw_road_type)

    # reference line
    raw_plan_view = raw_road.find('planView')
    assert raw_plan_view is not None, \
        "Road {} has no reference line!".format(self.road_id)
    self.plan_view.parse_from(raw_plan_view)

    # elevationProfile
    raw_elevation_profile = raw_road.find('elevationProfile')
    self.elevation_profile.parse_from(raw_elevation_profile)

    # lateralProfile
    raw_lateral_profile = raw_road.find('lateralProfile')
    self.lateral_profile.parse_from(raw_lateral_profile)

    # lanes
    raw_lanes = raw_road.find('lanes')
    assert raw_lanes is not None, "Road {} has no lanes!".format(self.road_id)
    self.lanes.parse_from(raw_lanes)

  def generate_reference_line(self):
    for geometry in self.plan_view.geometrys:
      if geometry.length < GEOMETRY_SKIP_LENGTH:
        continue

      points = geometry.sampling(SAMPLING_LENGTH)
      self.reference_line.extend(points)

      self.reference_line_add_offset()


  def reference_line_add_offset(self):
    lane_offsets = self.lanes.lane_offsets
    i, n = 0, len()
    cur_s = lane_offsets[i].s
    next_s = lane_offsets[i+1].s if i+1 < n else self.road_length
    for idx in range(len(self.reference_line)):
      if self.reference_line[idx].s < cur_s:
        continue

      if self.reference_line[idx].s > next_s:
        i += 1
        # if i >= n:
        #   break
        i = min(n-1, i)
        cur_s = lane_offsets[i].s
        next_s = lane_offsets[i+1].s if i+1 < n else self.road_length

      ds = self.reference_line[idx].s - cur_s

      a = lane_offsets[i].a
      b = lane_offsets[i].b
      c = lane_offsets[i].c
      d = lane_offsets[i].d
      offset = a + b*ds + c*ds**2 + d*ds**3

      # if offset:
      #   print(reference_line[idx])
      self.reference_line[idx].shift_t(offset)
      # if offset:
      #   print(reference_line[idx])