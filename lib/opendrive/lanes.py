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
  def __init__(self, s = None, a = None, b = None, c = None, d = None):
    self.s = s
    self.a = a
    self.b = b
    self.c = c
    self.d = d

  def parse_from(self, raw_lane_offset):
    self.s = float(raw_lane_offset.attrib.get('s'))
    self.a = float(raw_lane_offset.attrib.get('a'))
    self.b = float(raw_lane_offset.attrib.get('b'))
    self.c = float(raw_lane_offset.attrib.get('c'))
    self.d = float(raw_lane_offset.attrib.get('d'))

# Lane
class LaneLink:
  def __init__(self, link_id = None):
    self.link_id = link_id

  def parse_from(self, raw_data):
    if raw_data:
      self.link_id = raw_data.attrib.get("id")


class Link:
  def __init__(self):
    self.predecessor = LaneLink()
    self.successor = LaneLink()

  def parse_from(self, raw_link):
    if raw_link:
      raw_predecessor = raw_link.find("predecessor")
      self.predecessor.parse_from(raw_predecessor)

      raw_successor = raw_link.find("successor")
      self.successor.parse_from(raw_successor)


class Width:
  def __init__(self, sOffset = None, a = None, b = None, c = None, d = None):
    self.sOffset = sOffset
    self.a = a
    self.b = b
    self.c = c
    self.d = d

  def parse_from(self, raw_width):
    self.sOffset = float(raw_width.attrib.get("sOffset"))
    self.a = float(raw_width.attrib.get("a"))
    self.b = float(raw_width.attrib.get("b"))
    self.c = float(raw_width.attrib.get("c"))
    self.d = float(raw_width.attrib.get("d"))


class RoadMark:
  def __init__(self, sOffset = None, roadmark_type = None, material = None, \
               width = None, lane_change = None):
    self.sOffset = sOffset
    self.roadmark_type = roadmark_type
    self.material = material
    self.width = width
    self.lane_change = lane_change

  def parse_from(self, raw_road_mark):
    self.sOffset = float(raw_road_mark.attrib.get("sOffset"))
    self.roadmark_type = raw_road_mark.attrib.get("type")
    # self.width = float(raw_road_mark.attrib.get("width"))
    self.lane_change = raw_road_mark.attrib.get("lane_change")


class Lane:
  def __init__(self, lane_id = None, lane_type = None, level = None):
    self.lane_id = lane_id
    self.lane_type = lane_type
    self.level = level
    self.link = Link()
    self.widths = []
    self.road_marks = []
    self.user_data = None

  def add_width(self, width):
    self.widths.append(width)

  def add_road_mark(self, road_mark):
    self.road_marks.append(road_mark)

  def parse_from(self, raw_lane):
    self.lane_id = raw_lane.attrib.get('id')
    self.lane_type = raw_lane.attrib.get('type')
    self.level = raw_lane.attrib.get('level')

    # link
    raw_link = raw_lane.find("link")
    self.link.parse_from(raw_link)

    # width
    for raw_width in raw_lane.iter("width"):
      width = Width()
      width.parse_from(raw_width)
      self.add_width(width)

    # roadMark
    for raw_road_mark in raw_lane.iter("roadMark"):
      road_mark = RoadMark()
      road_mark.parse_from(raw_road_mark)
      self.add_road_mark(road_mark)


class LaneSection:
  def __init__(self, s = None, single_side = None):
    self.s = s
    self.single_side = single_side
    self.left = []
    self.center = Lane()
    self.right = []

  def add_left_lane(self, lane):
    self.left.append(lane)

  def add_right_lane(self, lane):
    self.right.append(lane)

  def parse_from(self, raw_lane_section):
    self.s = float(raw_lane_section.attrib.get('s'))
    self.single_side = bool(raw_lane_section.attrib.get('singleSide'))

    # left
    left = raw_lane_section.find("left")
    if left:
      for raw_lane in left.iter('lane'):
        lane = Lane()
        lane.parse_from(raw_lane)
        self.add_left_lane(lane)

    # center
    center = raw_lane_section.find("center")
    raw_lane = center.find('lane')
    self.center.parse_from(raw_lane)

    # right
    right = raw_lane_section.find("right")
    if right:
      for raw_lane in right.iter('lane'):
        lane = Lane()
        lane.parse_from(raw_lane)
        self.add_right_lane(lane)


# Lanes
class Lanes:
  def __init__(self):
    self.lane_offsets = []
    self.lane_sections = []

  def add_lane_offset(self, lane_offset):
    self.lane_offsets.append(lane_offset)

  def add_lane_section(self, lane_section):
    self.lane_sections.append(lane_section)

  def parse_from(self, raw_lanes):
    # laneOffset
    for raw_lane_offset in raw_lanes.iter('laneOffset'):
      lane_offset = LaneOffset()
      lane_offset.parse_from(raw_lane_offset)
      self.add_lane_offset(lane_offset)

    # laneSection
    for raw_lane_section in raw_lanes.iter("laneSection"):
      lane_section = LaneSection()
      lane_section.parse_from(raw_lane_section)
      self.add_lane_section(lane_section)
