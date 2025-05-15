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


import logging
import math

from modules.map.proto import map_pb2
from modules.map.proto import map_road_pb2
from modules.map.proto import map_lane_pb2

import imap.global_var as global_var

from imap.lib.opendrive.map import Map
from imap.lib.proto_utils import (
    write_pb_to_text_file,
    write_pb_to_bin_file
)

from imap.lib.draw import draw_line, show
from imap.lib.convex_hull import convex_hull, aabb_box
from imap.lib.proj_helper import latlon2projected


# Distance between stop line and pedestrian crossing
STOP_LINE_DISTANCE = 1.0


def to_pb_lane_type(open_drive_type):
    if open_drive_type is None:
        return map_lane_pb2.Lane.NONE

    lower_type = open_drive_type.lower()
    if lower_type == 'none':
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'driving':
        return map_lane_pb2.Lane.CITY_DRIVING
    elif lower_type == 'biking':
        return map_lane_pb2.Lane.BIKING
    elif lower_type == 'sidewalk':
        return map_lane_pb2.Lane.SIDEWALK
    elif lower_type == 'parking':
        return map_lane_pb2.Lane.PARKING
    elif lower_type == 'shoulder':
        return map_lane_pb2.Lane.SHOULDER
    elif lower_type == 'border':     # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'stop':       # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'restricted':  # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'median':     # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'curb':       # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'exit':       # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'entry':      # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'onramp':     # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'offRamp':    # not support
        return map_lane_pb2.Lane.NONE
    elif lower_type == 'connectingRamp':  # not support
        return map_lane_pb2.Lane.NONE
    else:
        logging.info("Unsupported lane type: {}".format(open_drive_type))
        return map_lane_pb2.Lane.NONE


def to_pb_boundary_type(opendrive_boundary_type):
    if (opendrive_boundary_type.boundary_type is None or
            opendrive_boundary_type.color is None):
        return map_lane_pb2.LaneBoundaryType.UNKNOWN

    lower_type = opendrive_boundary_type.boundary_type.lower()
    lower_color = opendrive_boundary_type.color.lower()

    # Table 38. Attributes of the road lanes laneSection lcr lane roadMark element
    # e_roadMarkColor & e_roadMarkType
    if lower_type == 'solid solid' and lower_color == 'yellow':
        return map_lane_pb2.LaneBoundaryType.DOUBLE_YELLOW

    if lower_type == 'broken':
        if lower_color == 'yellow':
            return map_lane_pb2.LaneBoundaryType.DOTTED_YELLOW
        elif lower_color == 'white':
            return map_lane_pb2.LaneBoundaryType.DOTTED_WHITE

    if lower_type == 'solid':
        if lower_color == 'yellow':
            return map_lane_pb2.LaneBoundaryType.SOLID_YELLOW
        elif lower_color == 'white':
            return map_lane_pb2.LaneBoundaryType.SOLID_WHITE

    if lower_type == 'curb':
        return map_lane_pb2.LaneBoundaryType.CURB

    return map_lane_pb2.LaneBoundaryType.UNKNOWN


class Convertor:
    def __init__(self) -> None:
        pass

    def convert(self):
        pass


class Opendrive2Apollo(Convertor):
    def __init__(self, input_file_name, output_file_name=None) -> None:
        self.xodr_map = Map()
        self.xodr_map.load(input_file_name)

        # lhd for saving figure
        self.input_file_name = input_file_name

        self.pb_map = map_pb2.Map()

        self.output_file_name = self._get_file_name(output_file_name)
        # UTM coordinate
        self.origin_x = 0.0
        self.origin_y = 0.0

    def _get_file_name(self, file_name):
        if file_name and file_name.endswith((".txt", ".bin")):
            return file_name.rsplit('.', 1)[0]
        return None

    def set_parameters(self, only_driving=True):
        self.only_driving = only_driving

    def convert_proj_txt(self, proj_txt):
        if proj_txt is None:
            self.pb_map.header.projection.proj = "+proj=utm +zone={} +ellps=WGS84 " \
                "+datum=WGS84 +units=m +no_defs".format(0)
            return

        if '+proj=utm' in proj_txt:
            self.pb_map.header.projection.proj = proj_txt
        else:
            # We want just support +proj=tmerc, but some do not contain this parameter
            lat, lon, x_0, y_0 = None, None, None, None
            for p in proj_txt.split():
                if p.startswith('+lat_0'):
                    lat = float(p.split('=')[1])
                elif p.startswith('+lon_0'):
                    lon = float(p.split('=')[1])
                elif p.startswith('+x_0'):
                    x_0 = float(p.split('=')[1])
                elif p.startswith('+y_0'):
                    y_0 = float(p.split('=')[1])
            if lat is None or lon is None:
                self.pb_map.header.projection.proj = "+proj=utm +zone={} +ellps=WGS84 " \
                    "+datum=WGS84 +units=m +no_defs".format(0)
            else:
                # use projTxt run latlon2projected
                self.origin_x, self.origin_y, zone_id = latlon2projected(
                    lat, lon, self.xodr_map.header.geo_reference.text)
                if x_0:
                    self.origin_x = self.origin_x - x_0
                if y_0:
                    self.origin_y = self.origin_y - y_0
                self.pb_map.header.projection.proj = "+proj=utm +zone={} +ellps=WGS84 " \
                    "+datum=WGS84 +units=m +no_defs".format(zone_id)

    def convert_header(self):
        if self.xodr_map.header.version:
            self.pb_map.header.version = self.xodr_map.header.version
        if self.xodr_map.header.date:
            self.pb_map.header.date = self.xodr_map.header.date

        proj_txt = self.xodr_map.header.geo_reference.text
        self.convert_proj_txt(proj_txt)

        # TODO(zero): Inconsistent definitions
        # self.pb_map.header.district = self.xodr_map.header.name
        if self.xodr_map.header.rev_major:
            self.pb_map.header.rev_major = self.xodr_map.header.rev_major
        if self.xodr_map.header.rev_minor:
            self.pb_map.header.rev_minor = self.xodr_map.header.rev_minor
        if self.xodr_map.header.west:
            self.pb_map.header.left = self.xodr_map.header.west
        if self.xodr_map.header.east:
            self.pb_map.header.right = self.xodr_map.header.east
        if self.xodr_map.header.north:
            self.pb_map.header.top = self.xodr_map.header.north
        if self.xodr_map.header.south:
            self.pb_map.header.bottom = self.xodr_map.header.south
        if self.xodr_map.header.vendor:
            self.pb_map.header.vendor = self.xodr_map.header.vendor

    def add_basic_info(self, pb_lane, xodr_road, idx, lane):
        pb_lane.id.id = "road_{}_lane_{}_{}".format(xodr_road.road_id,
                                                    idx, lane.lane_id)
        pb_lane.type = to_pb_lane_type(lane.lane_type)
        pb_lane.length = lane.length
        # Lane speed first, then road, and finally the default 120km/h
        if lane.speed.max_v:
            pb_lane.speed_limit = lane.speed.max_v
        elif xodr_road.road_type.speed.max_speed:
            pb_lane.speed_limit = xodr_road.road_type.speed.max_speed
        else:
            pb_lane.speed_limit = 33.3
        pb_lane.direction = map_lane_pb2.Lane.FORWARD

    def add_lane_boundary(self, pb_lane, lane):
        # 1. left boundary
        segment = pb_lane.left_boundary.curve.segment.add()
        for point3d in lane.left_boundary:
            point = segment.line_segment.point.add()
            # lhd 2022/12/03 for 3D view
            if global_var.get_element_value("enable_z_axis"):
                point.x, point.y, point.z = point3d.x, point3d.y, point3d.z
            else:
                point.x, point.y = point3d.x, point3d.y
        segment.s = 0
        segment.start_position.x = lane.left_boundary[0].x
        segment.start_position.y = lane.left_boundary[0].y
        segment.start_position.z = lane.left_boundary[0].z
        segment.length = pb_lane.length
        pb_lane.left_boundary.length = pb_lane.length
        pb_boundary_type = to_pb_boundary_type(lane.left_boundary_type)
        boundary_type = pb_lane.left_boundary.boundary_type.add()
        boundary_type.s = 0
        boundary_type.types.append(pb_boundary_type)

        # 2. center line
        segment = pb_lane.central_curve.segment.add()
        for point3d in lane.center_line:
            point = segment.line_segment.point.add()
            # lhd 2022/12/03 for 3D view
            if global_var.get_element_value("enable_z_axis"):
                point.x, point.y, point.z = point3d.x, point3d.y, point3d.z
            else:
                point.x, point.y = point3d.x, point3d.y
        segment.s = 0
        segment.start_position.x = lane.center_line[0].x
        segment.start_position.y = lane.center_line[0].y
        segment.start_position.z = lane.center_line[0].z
        segment.length = pb_lane.length

        # 3. right boundary
        segment = pb_lane.right_boundary.curve.segment.add()
        for point3d in lane.right_boundary:
            point = segment.line_segment.point.add()
            # lhd 2022/12/03 for 3D view
            if global_var.get_element_value("enable_z_axis"):
                point.x, point.y, point.z = point3d.x, point3d.y, point3d.z
            else:
                point.x, point.y = point3d.x, point3d.y
        segment.s = 0
        segment.start_position.x = lane.right_boundary[0].x
        segment.start_position.y = lane.right_boundary[0].y
        segment.start_position.z = lane.right_boundary[0].z
        segment.length = pb_lane.length
        pb_lane.right_boundary.length = pb_lane.length
        pb_boundary_type = to_pb_boundary_type(lane.right_boundary_type)
        boundary_type = pb_lane.right_boundary.boundary_type.add()
        boundary_type.s = 0
        boundary_type.types.append(pb_boundary_type)

    def add_lane_sample(self, pb_lane, lane):
        cur_lane_id = int(lane.lane_id)
        total_s = lane.center_line[0].s
        for point3d in lane.center_line:
            lane_width = lane.get_width_by_s(point3d.s)

            # 1. left sample
            left_sample = pb_lane.left_sample.add()
            left_sample.width = lane_width / 2
            # 2. right sample
            right_sample = pb_lane.right_sample.add()
            right_sample.width = lane_width / 2
            # left lane's should be reverse
            if cur_lane_id > 0:
                left_sample.s = total_s - point3d.s
                right_sample.s = total_s - point3d.s
            else:
                left_sample.s = point3d.s
                right_sample.s = point3d.s

    def add_lane_neighbors(self, pb_lane, xodr_road, idx, lane):
        for lane_id in lane.left_neighbor_forward:
            pb_lane.left_neighbor_forward_lane_id.add().id = \
                "road_{}_lane_{}_{}".format(xodr_road.road_id, idx, lane_id)

        for lane_id in lane.right_neighbor_forward:
            pb_lane.right_neighbor_forward_lane_id.add().id = \
                "road_{}_lane_{}_{}".format(xodr_road.road_id, idx, lane_id)

        for lane_id in lane.left_neighbor_reverse:
            pb_lane.left_neighbor_reverse_lane_id.add().id = \
                "road_{}_lane_{}_{}".format(xodr_road.road_id, idx, lane_id)

    def outcoming_road_relationships(self, pb_lane, lane, predecessors, xodr_road):
        # print("--------")
        for predecessor_road, dirct in predecessors:
            # print("{}->{}".format(predecessor_road.road_id, xodr_road.road_id))
            section_id = len(predecessor_road.lanes.lane_sections) - 1
            # left
            if dirct == "predecessor":
                for predecessor_lane in predecessor_road.lanes.lane_sections[0].left:
                    if predecessor_lane.link.predecessor and \
                       predecessor_lane.link.predecessor.link_id == lane.lane_id:
                        pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format(
                            predecessor_road.road_id, 0, predecessor_lane.lane_id)
            elif dirct == "successor":
                for predecessor_lane in predecessor_road.lanes.lane_sections[section_id].right:
                    if predecessor_lane.link.successor and \
                            predecessor_lane.link.successor.link_id == lane.lane_id:
                        pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format(
                            predecessor_road.road_id, section_id, predecessor_lane.lane_id)
            else:
                print("Unknown direction!")

    def add_junction_relationships(self, pb_lane, xodr_road, lane_section, idx, lane):
        cur_n = len(xodr_road.lanes.lane_sections)
        if idx == 0:
            predecessor_junction = xodr_road.link.predecessor_junction
            if predecessor_junction is not None:
                # incoming_road
                for connection in predecessor_junction.connections:
                    lane_link = connection.incoming_lane_link(xodr_road.road_id,
                                                              lane.lane_id)
                    if lane_link is not None:
                        section_id = 0
                        pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format(
                            connection.connecting_road, section_id, lane_link.to_id)
                # outcoming_road
                predecessors = predecessor_junction.get_predecessors(
                    xodr_road.road_id)
                self.outcoming_road_relationships(
                    pb_lane, lane, predecessors, xodr_road)

        if idx == cur_n - 1:
            successor_junction = xodr_road.link.successor_junction
            if successor_junction is not None:
                # incoming_road
                for connection in successor_junction.connections:
                    lane_link = connection.incoming_lane_link(xodr_road.road_id,
                                                              lane.lane_id)
                    if lane_link is not None:
                        section_id = 0
                        pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format(
                            connection.connecting_road, section_id, lane_link.to_id)
                # outcoming_road
                predecessors = successor_junction.get_predecessors(
                    xodr_road.road_id)
                self.outcoming_road_relationships(
                    pb_lane, lane, predecessors, xodr_road)

    def add_lane_relationships(self, pb_lane, xodr_road, lane_section, idx, lane):
        cur_n = len(xodr_road.lanes.lane_sections)
        cur_lane_id = int(lane.lane_id)
        # 1. External connection
        if idx == 0:
            # 1.1 predecessor road
            predecessor_road_id = xodr_road.link.predecessor.element_id
            if predecessor_road_id and lane.link.predecessor:
                section_id = 0
                if xodr_road.link.predecessor.contact_point == "start":
                    section_id = 0
                elif xodr_road.link.predecessor.contact_point == "end":
                    section_id = len(
                        xodr_road.link.predecessor_road.lanes.lane_sections) - 1

                if cur_lane_id < 0:
                    pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format(
                        predecessor_road_id, section_id, lane.link.predecessor.link_id)
                elif cur_lane_id > 0:
                    pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format(
                        predecessor_road_id, section_id, lane.link.predecessor.link_id)
        if idx == cur_n - 1:
            # 1.2 successor road
            successor_road_id = xodr_road.link.successor.element_id
            if successor_road_id and lane.link.successor:
                section_id = 0
                if xodr_road.link.successor.contact_point == "start":
                    section_id = 0
                elif xodr_road.link.successor.contact_point == "end":
                    section_id = len(
                        xodr_road.link.successor_road.lanes.lane_sections) - 1

                if cur_lane_id < 0:
                    pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format(
                        successor_road_id, section_id, lane.link.successor.link_id)
                elif cur_lane_id > 0:
                    pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format(
                        successor_road_id, section_id, lane.link.successor.link_id)

        # 2. Internal connection
        if idx > 0 and lane.link.predecessor:
            if cur_lane_id < 0:
                pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format(
                    xodr_road.road_id, idx - 1, lane.link.predecessor.link_id)
            elif cur_lane_id > 0:
                pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format(
                    xodr_road.road_id, idx - 1, lane.link.predecessor.link_id)
        if idx < cur_n - 1 and lane.link.successor:
            if cur_lane_id < 0:
                pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format(
                    xodr_road.road_id, idx + 1, lane.link.successor.link_id)
            elif cur_lane_id > 0:
                pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format(
                    xodr_road.road_id, idx + 1, lane.link.successor.link_id)

    def create_lane(self, xodr_road, lane_section, idx, lane):
        if self.only_driving and lane.lane_type != "driving":
            return

        pb_lane = self.pb_map.lane.add()
        self.add_basic_info(pb_lane, xodr_road, idx, lane)
        # add boundary
        self.add_lane_boundary(pb_lane, lane)
        # add lane sample
        self.add_lane_sample(pb_lane, lane)
        # add neighbor
        self.add_lane_neighbors(pb_lane, xodr_road, idx, lane)
        # predecessor road
        self.add_lane_relationships(
            pb_lane, xodr_road, lane_section, idx, lane)
        self.add_junction_relationships(
            pb_lane, xodr_road, lane_section, idx, lane)
        return pb_lane

    def add_road_section_curve(self, pb_boundary_edge, boundary, length):
        segment = pb_boundary_edge.curve.segment.add()
        for point3d in boundary:
            point = segment.line_segment.point.add()
            # lhd 2022/12/03 for 3D view
            if global_var.get_element_value("enable_z_axis"):
                point.x, point.y, point.z = point3d.x, point3d.y, point3d.z
            else:
                point.x, point.y = point3d.x, point3d.y
        segment.s = 0
        segment.start_position.x = boundary[0].x
        segment.start_position.y = boundary[0].y
        segment.start_position.z = boundary[0].z
        segment.length = length

    def add_road_section_boundary(self, pb_road_section, lane_section):
        left_boundary_edge = pb_road_section.boundary.outer_polygon.edge.add()
        left_boundary_edge.type = map_road_pb2.BoundaryEdge.LEFT_BOUNDARY
        right_boundary_edge = pb_road_section.boundary.outer_polygon.edge.add()
        right_boundary_edge.type = map_road_pb2.BoundaryEdge.RIGHT_BOUNDARY

        leftmost_boundary, leftmost_length = lane_section.leftmost_boundary()
        rightmost_boundary, rightmost_length = lane_section.rightmost_boundary()

        if not leftmost_boundary or not rightmost_boundary:
            # TODO(zero): No leftmost_boundary and rightmost_boundary?
            return

        self.add_road_section_curve(left_boundary_edge,
                                    leftmost_boundary, leftmost_length)
        self.add_road_section_curve(right_boundary_edge,
                                    rightmost_boundary, rightmost_length)

    def convert_lane(self, xodr_road, pb_road):
        for idx, lane_section in enumerate(xodr_road.lanes.lane_sections):
            pb_road_section = pb_road.section.add()
            pb_road_section.id.id = str(idx)
            self.add_road_section_boundary(pb_road_section, lane_section)

            for lane in lane_section.left:
                pb_lane = self.create_lane(xodr_road, lane_section, idx, lane)
                # Not driving road is None
                if pb_lane is not None:
                    pb_road_section.lane_id.add().id = pb_lane.id.id

            # The last section of road, which used to generate stop lines for
            # traffic lights
            pb_last_section = []
            for lane in lane_section.right:
                pb_lane = self.create_lane(xodr_road, lane_section, idx, lane)
                if pb_lane is not None:
                    pb_road_section.lane_id.add().id = pb_lane.id.id
                    pb_last_section.append(pb_lane)
        return pb_last_section

    def construct_signal_overlap(self, pb_lane, pb_signal):
        # lane_overlap_info
        pb_overlap = self.pb_map.overlap.add()
        pb_overlap.id.id = "{}_{}".format(pb_lane.id.id, pb_signal.id.id)
        # lane_overlap_info
        pb_object = pb_overlap.object.add()
        pb_object.id.id = pb_lane.id.id
        # todo(zero): need to complete
        # pb_object.lane_overlap_info.start_s
        # pb_object.lane_overlap_info.end_s

        # signal_overlap_info
        pb_object = pb_overlap.object.add()
        pb_object.id.id = pb_signal.id.id

        # add overlap to lane and signal
        pb_lane_overlap_id = pb_lane.overlap_id.add()
        pb_lane_overlap_id.id = pb_overlap.id.id

        pb_signal_overlap_id = pb_signal.overlap_id.add()
        pb_signal_overlap_id.id = pb_overlap.id.id

    def _construct_signal_stopline(self, last_section_lanes, pb_signal):
        pb_left_lane, pb_right_lane = last_section_lanes[0], last_section_lanes[-1]
        left_segment = pb_left_lane.left_boundary.curve.segment[-1].line_segment
        right_segment = pb_right_lane.right_boundary.curve.segment[-1].line_segment

        sampling_length = global_var.get_element_value("sampling_length")
        index = math.ceil(STOP_LINE_DISTANCE/sampling_length)
        pb_stop_line = pb_signal.stop_line.add()
        pb_segment = pb_stop_line.segment.add()

        if len(left_segment.point) < index:
            point = pb_segment.line_segment.point.add()
            point.CopyFrom(left_segment.point[-1])
            point = pb_segment.line_segment.point.add()
            point.CopyFrom(right_segment.point[-1])
        else:
            point = pb_segment.line_segment.point.add()
            point.CopyFrom(left_segment.point[-index])
            point = pb_segment.line_segment.point.add()
            point.CopyFrom(right_segment.point[-index])

    def convert_signal(self, xodr_road, pb_last_section):
        for signal_reference in xodr_road.signals.signal_references:
            # todo(zero): need implement
            pass

        for signal in xodr_road.signals.signals:
            if signal.is_traffic_light() and pb_last_section:
                # print(signal)
                pb_signal = self.pb_map.signal.add()
                # add road_id to avoid duplication
                pb_signal.id.id = "signal_{}_{}".format(
                    xodr_road.road_id, signal.id)
                # todo(zero): needs to be completed(boundary\subsignal\type)
                self._construct_signal_stopline(pb_last_section, pb_signal)
                for pb_lane in pb_last_section:
                    self.construct_signal_overlap(pb_lane, pb_signal)

    def convert_roads(self):
        for _, xodr_road in self.xodr_map.roads.items():
            pb_road = self.pb_map.road.add()
            pb_road.id.id = xodr_road.road_id
            if xodr_road.junction_id != "-1":
                pb_road.junction_id.id = xodr_road.junction_id

            # The definition of road type is inconsistent
            if xodr_road.road_type.road_type is None:
                pb_road.type = map_road_pb2.Road.CITY_ROAD

            xodr_road.generate_reference_line()
            xodr_road.add_offset_to_reference_line()
            xodr_road.add_origin_to_reference_line(
                self.origin_x, self.origin_y)
            # Todo(zero):
            draw_line(xodr_road.reference_line, 'r',
                      reference_line=True, label="reference line " + str(pb_road.id.id))

            xodr_road.process_lanes()

            pb_last_section = self.convert_lane(xodr_road, pb_road)
            # Todo(zero): need to complete signal
            self.convert_signal(xodr_road, pb_last_section)

    def _is_valid_junction(self, xodr_junction):
        connecting_roads = set()
        incoming_roads = set()
        for connection in xodr_junction.connections:
            connecting_roads.add(connection.connecting_road)
            incoming_roads.add(connection.incoming_road)

        return len(connecting_roads) != 1 and len(incoming_roads) != 1

    def construct_junction_polygon(self, xodr_junction):
        if not self._is_valid_junction(xodr_junction):
            return []

        points = []
        for road, relation in xodr_junction.connected_roads:
            cross_section = road.get_cross_section(relation)
            if cross_section:
                start, end = cross_section
                points.append([start.x, start.y])
                points.append([end.x, end.y])

        # when point <= 4 convex_hull will not fully covered, so we change to aabb_box
        if len(points) <= 4:
            return aabb_box(points)
        else:
            return convex_hull(points)

    def convert_junctions(self):
        for _, xodr_junction in self.xodr_map.junctions.items():
            polygon = self.construct_junction_polygon(xodr_junction)
            if len(polygon) < 3:
                logging.warning(
                    "junction {} polygon size < 3.".format(xodr_junction.junction_id))
                continue

            pb_junction = self.pb_map.junction.add()
            pb_junction.id.id = xodr_junction.junction_id
            for x, y in polygon:
                pb_point = pb_junction.polygon.point.add()
                pb_point.x, pb_point.y, pb_point.z = x, y, 0

    def convert(self):
        self.convert_header()
        # Don't change the order. "convert_roads" must before "convert_junctions"
        self.convert_roads()
        self.convert_junctions()

        # Todo(zero): display xodr map
        if self.output_file_name is None:
            show(need_save=global_var.get_element_value("need_save_figure"),
                 path=self.input_file_name.replace(".xodr", ".png"))

    def save_map(self):
        output_file_name = self.output_file_name
        if output_file_name is None:
            output_file_name = "default"
        write_pb_to_text_file(self.pb_map, output_file_name)
        write_pb_to_bin_file(self.pb_map, output_file_name)
