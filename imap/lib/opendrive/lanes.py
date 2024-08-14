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

import imap.global_var as global_var

from imap.lib.common import shift_t, calc_length
from imap.lib.draw import draw_line

from imap.lib.opendrive.common import convert_speed


def binary_search(arr, val):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = math.floor((left + right)/2)
        if arr[mid] <= val:
            left = mid + 1
        else:
            right = mid - 1
    return left - 1


def is_adjacent(road_marks) -> bool:
    if not road_marks:
        return True

    road_mark = road_marks[0]
    if road_mark.roadmark_type == "botts dots" or \
       road_mark.roadmark_type == "broken broken" or \
       road_mark.roadmark_type == "broken solid" or \
       road_mark.roadmark_type == "broken" or \
       road_mark.roadmark_type == "none":
        return True
    return False


# LaneOffset
class LaneOffset:
    def __init__(self, s=None, a=None, b=None, c=None, d=None):
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
    def __init__(self, link_id=None):
        self.link_id = link_id

    def parse_from(self, raw_data):
        self.link_id = raw_data.attrib.get("id")


class Link:
    def __init__(self):
        self.predecessor = None
        self.successor = None

    def parse_from(self, raw_link):
        if raw_link is not None:
            raw_predecessor = raw_link.find("predecessor")
            if raw_predecessor is not None:
                self.predecessor = LaneLink()
                self.predecessor.parse_from(raw_predecessor)

            raw_successor = raw_link.find("successor")
            if raw_successor is not None:
                self.successor = LaneLink()
                self.successor.parse_from(raw_successor)


class Width:
    def __init__(self, sOffset=None, a=None, b=None, c=None, d=None):
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
    def __init__(self, sOffset=None, roadmark_type=None, material=None,
                 color=None, width=None, lane_change=None):
        self.sOffset = sOffset
        self.roadmark_type = roadmark_type
        self.material = material
        self.color = color
        self.width = width
        self.lane_change = lane_change

    def parse_from(self, raw_road_mark):
        self.sOffset = float(raw_road_mark.attrib.get("sOffset"))
        self.color = raw_road_mark.attrib.get("color")
        self.roadmark_type = raw_road_mark.attrib.get("type")
        # self.width = float(raw_road_mark.attrib.get("width"))
        self.lane_change = raw_road_mark.attrib.get("lane_change")


class Speed:
    def __init__(self, sOffset=None, raw_max_v=None, unit=None):
        self.sOffset = sOffset
        self.raw_max_v = raw_max_v
        self.unit = unit
        self.max_v = None

    def parse_from(self, raw_speed):
        if raw_speed is not None:
            self.sOffset = float(raw_speed.attrib.get("sOffset"))
            self.raw_max_v = float(raw_speed.attrib.get("max"))
            self.unit = raw_speed.attrib.get("unit")
            self.max_v = convert_speed(self.raw_max_v, self.unit)


class LaneBoundaryType:
    def __init__(self) -> None:
        self.boundary_type = None
        self.color = None


class Lane:
    def __init__(self, lane_id=None, lane_type=None, level=None,
                 direction=None):
        self.lane_id = lane_id
        self.lane_type = lane_type
        self.level = level
        self.link = Link()
        self.widths = []
        self.speed = Speed()
        self.road_marks = []
        self.user_data = None

        # private
        self.direction = direction
        self.length = None
        self.left_neighbor_forward = []
        self.right_neighbor_forward = []
        self.left_neighbor_reverse = []
        self.right_neighbor_reverse = []
        self.left_boundary = []
        self.left_boundary_type = LaneBoundaryType()
        self.right_boundary = []
        self.right_boundary_type = LaneBoundaryType()
        self.center_line = []

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

        # speed
        raw_speed = raw_lane.find("speed")
        self.speed.parse_from(raw_speed)

        # roadMark
        for raw_road_mark in raw_lane.iter("roadMark"):
            road_mark = RoadMark()
            road_mark.parse_from(raw_road_mark)
            self.add_road_mark(road_mark)

    def get_width_by_s(self, s):
        idx = binary_search([width.sOffset for width in self.widths], s)
        a = self.widths[idx].a
        b = self.widths[idx].b
        c = self.widths[idx].c
        d = self.widths[idx].d

        ds = s - self.widths[idx].sOffset
        return a + b*ds + c*ds**2 + d*ds**3

    def generate_boundary(self, left_boundary, start_s):
        self.left_boundary = left_boundary
        for point3d in left_boundary:
            width = self.get_width_by_s(point3d.s - start_s)

            rpoint3d = shift_t(point3d, width * self.direction)
            self.right_boundary.append(rpoint3d)

            cpoint3d = shift_t(point3d, width * self.direction / 2)
            # todo(daohu527): need update point.s?
            self.center_line.append(cpoint3d)

        # cacl lane length
        self.length = calc_length(self.center_line)

        debug_mode = global_var.get_element_value("debug_mode")
        if not debug_mode:
            if self.lane_type == "driving":
                draw_line(self.left_boundary, 'g')
                draw_line(self.right_boundary, 'r')
            else:
                draw_line(self.left_boundary)
                draw_line(self.right_boundary)
        return self.right_boundary

    def generate_boundary_type(self, left_boundary_type) -> str:
        self.left_boundary_type = left_boundary_type
        if self.road_marks:
            self.right_boundary_type.boundary_type = self.road_marks[0].roadmark_type
            self.right_boundary_type.color = self.road_marks[0].color
        return self.right_boundary_type


class LaneSection:
    def __init__(self, s=None, single_side=None):
        self.s = s
        self.single_side = single_side
        self.left = []
        self.center = Lane()
        self.right = []

        # private
        self.end_s = None

    def add_left_lane(self, lane):
        self.left.append(lane)

    def add_right_lane(self, lane):
        self.right.append(lane)

    def parse_from(self, raw_lane_section):
        self.s = float(raw_lane_section.attrib.get('s'))

        self.single_side = bool(raw_lane_section.attrib.get('singleSide'))

        # left
        left = raw_lane_section.find("left")
        if left is not None:
            for raw_lane in left.iter('lane'):
                lane = Lane(direction=1)
                lane.parse_from(raw_lane)
                self.add_left_lane(lane)

        # center
        center = raw_lane_section.find("center")
        raw_lane = center.find('lane')
        self.center.parse_from(raw_lane)

        # right
        right = raw_lane_section.find("right")
        if right is not None:
            for raw_lane in right.iter('lane'):
                lane = Lane(direction=-1)
                lane.parse_from(raw_lane)
                self.add_right_lane(lane)

    def add_neighbors(self):
        n = len(self.left)
        for idx in range(n):
            if idx+1 < n and self.left[idx+1].lane_type == "driving":
                self.left[idx].left_neighbor_forward.append(
                    self.left[idx+1].lane_id)
            if idx > 0 and self.left[idx-1].lane_type == "driving":
                self.left[idx].right_neighbor_forward.append(
                    self.left[idx-1].lane_id)

        n = len(self.right)
        for idx in range(n):
            if idx+1 < n and self.right[idx+1].lane_type == "driving":
                self.right[idx].right_neighbor_forward.append(
                    self.right[idx+1].lane_id)
            if idx > 0 and self.right[idx-1].lane_type == "driving":
                self.right[idx].left_neighbor_forward.append(
                    self.right[idx-1].lane_id)

        if self.left and self.right and is_adjacent(self.center.road_marks):
            if self.right[0].lane_type == "driving":
                self.left[-1].left_neighbor_reverse.append(
                    self.right[0].lane_id)
            if self.left[-1].lane_type == "driving":
                self.right[0].left_neighbor_reverse.append(
                    self.left[-1].lane_id)

    def process_lane(self, reference_line_in_section):
        left_boundary = reference_line_in_section.copy()
        left_boundary_type = self.center.generate_boundary_type(None)
        # The left lane is opposite to the reference line
        left_boundary.reverse()
        for lane in self.left[::-1]:
            left_boundary = lane.generate_boundary(left_boundary, self.s)
            left_boundary_type = lane.generate_boundary_type(
                left_boundary_type)

        left_boundary = reference_line_in_section.copy()
        left_boundary_type = self.center.generate_boundary_type(None)
        for lane in self.right:
            left_boundary = lane.generate_boundary(left_boundary, self.s)
            left_boundary_type = lane.generate_boundary_type(
                left_boundary_type)

    def get_cross_section(self, direction):
        if direction == "start":
            if self.left and self.right:
                leftmost_lane, rightmost_lane = self.left[0], self.right[-1]
                return [leftmost_lane.right_boundary[-1], rightmost_lane.right_boundary[0]]
            elif self.left:
                leftmost_lane, rightmost_lane = self.left[0], self.left[-1]
                return [leftmost_lane.right_boundary[-1], rightmost_lane.left_boundary[-1]]
            elif self.right:
                leftmost_lane, rightmost_lane = self.right[0], self.right[-1]
                return [leftmost_lane.left_boundary[0], rightmost_lane.right_boundary[0]]
            else:
                return []
        elif direction == "end":
            if self.left and self.right:
                leftmost_lane, rightmost_lane = self.left[0], self.right[-1]
                return [leftmost_lane.right_boundary[0], rightmost_lane.right_boundary[-1]]
            elif self.left:
                leftmost_lane, rightmost_lane = self.left[0], self.left[-1]
                return [leftmost_lane.right_boundary[0], rightmost_lane.left_boundary[0]]
            elif self.right:
                leftmost_lane, rightmost_lane = self.right[0], self.right[-1]
                return [leftmost_lane.left_boundary[-1], rightmost_lane.right_boundary[-1]]
            else:
                return []
        else:
            return []

    def leftmost_boundary(self):
        for lane in self.left:
            if lane.lane_type == "driving":
                return lane.right_boundary[::-1], lane.length

        for lane in self.right:
            if lane.lane_type == "driving":
                return lane.left_boundary, lane.length

        return [], 0

    def rightmost_boundary(self):
        for lane in self.right[::-1]:
            if lane.lane_type == "driving":
                return lane.right_boundary, lane.length

        for lane in self.left[::-1]:
            if lane.lane_type == "driving":
                return lane.left_boundary[::-1], lane.length

        return [], 0

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
        i = 0
        for raw_lane_section in raw_lanes.iter("laneSection"):
            lane_section = LaneSection()
            lane_section.parse_from(raw_lane_section)
            self.add_lane_section(lane_section)
            i += 1

    def have_offset(self):
        return len(self.lane_offsets) != 0

    def get_offset_by_s(self, s):
        idx = binary_search(
            [lane_offset.s for lane_offset in self.lane_offsets], s)
        a = self.lane_offsets[idx].a
        b = self.lane_offsets[idx].b
        c = self.lane_offsets[idx].c
        d = self.lane_offsets[idx].d
        ds = s - self.lane_offsets[idx].s
        return a + b*ds + c*ds**2 + d*ds**3

    def process_lane_sections(self, reference_line):
        for lane_section in self.lane_sections:
            start_s = lane_section.s
            end_s = lane_section.end_s
            reference_line_in_section = []
            for (idx, point3d) in enumerate(reference_line):
                # Todo(zero): Remove judgment because there may be exceptions? For example, judge the last 2 points instead of 1
                # if start_s <= point3d.s <= end_s or \
                #   (point3d.s < start_s and idx + 1 < len(reference_line) and start_s <= reference_line[idx + 1].s <= end_s) or \
                #     (end_s < point3d.s and idx - 1 >= 0 and start_s <= reference_line[idx - 1].s <= end_s):
                reference_line_in_section.append(point3d)
            lane_section.process_lane(reference_line_in_section)

    def get_cross_section(self, relation):
        if relation == "predecessor":
            return self.lane_sections[0].get_cross_section("start")
        elif relation == "successor":
            return self.lane_sections[-1].get_cross_section("end")
        else:
            print("Unknown relation!")
            return []
