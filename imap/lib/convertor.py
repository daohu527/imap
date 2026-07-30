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
import json

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
        self.only_driving = True
        self.enable_association = False
        self.lane_details = {}
        self.conversion_report = {
            "source": input_file_name,
            "counts": {
                "signals": 0,
                "stop_signs": 0,
                "yield_signs": 0,
                "parking_spaces": 0
            },
            "unresolved": []
        }

    def _get_file_name(self, file_name):
        if file_name and file_name.endswith((".txt", ".bin")):
            return file_name.rsplit('.', 1)[0]
        return None

    def set_parameters(self, only_driving=True, enable_association=False):
        self.only_driving = only_driving
        self.enable_association = enable_association

    def _append_unresolved(self, category, road_id, object_id, reason, extra=None):
        item = {
            "category": category,
            "road_id": str(road_id),
            "id": str(object_id),
            "reason": reason
        }
        if extra is not None:
            item["extra"] = extra
        self.conversion_report["unresolved"].append(item)

    def _has_field(self, pb_obj, field_name):
        if not hasattr(pb_obj, "DESCRIPTOR"):
            return False
        for field in pb_obj.DESCRIPTOR.fields:
            if field.name == field_name:
                return True
        return False

    def _get_repeated_field(self, pb_obj, candidates):
        for name in candidates:
            if self._has_field(pb_obj, name):
                return getattr(pb_obj, name)
        return None

    def _set_pb_id(self, pb_obj, object_id):
        if not self._has_field(pb_obj, "id"):
            return
        try:
            pb_obj.id.id = object_id
        except AttributeError:
            pb_obj.id = object_id

    def _get_pb_id(self, pb_obj):
        if not self._has_field(pb_obj, "id"):
            return None
        try:
            return pb_obj.id.id
        except AttributeError:
            return str(pb_obj.id)

    def _add_overlap_reference(self, pb_obj, overlap_id):
        if not self._has_field(pb_obj, "overlap_id"):
            return
        ref = pb_obj.overlap_id.add()
        ref.id = overlap_id

    def _to_float(self, value, default=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _classify_signal(self, signal):
        if signal.is_traffic_light() or (signal.dynamic or "").lower() == "yes":
            return "traffic_light"

        text_tokens = " ".join(filter(None, [signal.name, signal.text])).lower()
        if "stop" in text_tokens:
            return "stop_sign"
        if "yield" in text_tokens:
            return "yield_sign"
        if "speed" in text_tokens:
            return "speed_sign"
        return "unknown"

    def _build_virtual_point(self, x, y, z, s, yaw):
        class Point:
            pass

        point = Point()
        point.x = x
        point.y = y
        point.z = z
        point.s = s
        point.yaw = yaw
        return point

    def _point_on_reference_line(self, reference_line, query_s):
        if not reference_line:
            return None
        if query_s <= reference_line[0].s:
            point = reference_line[0]
            return self._build_virtual_point(point.x, point.y, point.z, query_s, point.yaw)
        if query_s >= reference_line[-1].s:
            point = reference_line[-1]
            return self._build_virtual_point(point.x, point.y, point.z, query_s, point.yaw)

        left = reference_line[0]
        right = reference_line[-1]
        for idx, point in enumerate(reference_line):
            if point.s >= query_s:
                right = point
                left = reference_line[idx - 1]
                break

        if right.s == left.s:
            return left
        ratio = (query_s - left.s) / (right.s - left.s)
        x = left.x + (right.x - left.x) * ratio
        y = left.y + (right.y - left.y) * ratio
        z = left.z + (right.z - left.z) * ratio
        yaw = left.yaw + (right.yaw - left.yaw) * ratio

        return self._build_virtual_point(x, y, z, query_s, yaw)

    def _find_lane_section_index(self, xodr_road, query_s):
        lane_sections = xodr_road.lanes.lane_sections
        if not lane_sections:
            return 0
        for idx, section in enumerate(lane_sections):
            if section.s <= query_s <= section.end_s:
                return idx
        if query_s < lane_sections[0].s:
            return 0
        return len(lane_sections) - 1

    def _lane_candidates_in_section(self, lane_context, section_idx):
        lane_groups = lane_context.get("section_lanes", [])
        if not lane_groups:
            return []
        if 0 <= section_idx < len(lane_groups) and lane_groups[section_idx]:
            return lane_groups[section_idx]

        # fallback to nearest section with lanes
        candidates = []
        best_dist = None
        for idx, group in enumerate(lane_groups):
            if not group:
                continue
            dist = abs(idx - section_idx)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                candidates = group
        return candidates

    def _filter_lanes_by_validity(self, lanes, validity):
        if not lanes:
            return []
        if validity is None or validity.from_lane is None or validity.to_lane is None:
            return lanes
        try:
            from_lane = int(validity.from_lane)
            to_lane = int(validity.to_lane)
        except (TypeError, ValueError):
            return lanes
        lower = min(from_lane, to_lane)
        upper = max(from_lane, to_lane)
        filtered = []
        for lane in lanes:
            raw_lane_id = self.lane_details[lane.id.id]["raw_lane_id"]
            try:
                lane_no = int(raw_lane_id)
            except (TypeError, ValueError):
                continue
            if lower <= lane_no <= upper:
                filtered.append(lane)
        return filtered

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
        self.lane_details[pb_lane.id.id] = {
            "road_id": xodr_road.road_id,
            "section_idx": idx,
            "raw_lane_id": lane.lane_id,
            "center_s": [point.s for point in lane.center_line]
        }
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
        lane_context = {
            "section_lanes": [],
            "pb_lane_map": {}
        }
        for idx, lane_section in enumerate(xodr_road.lanes.lane_sections):
            pb_road_section = pb_road.section.add()
            pb_road_section.id.id = str(idx)
            self.add_road_section_boundary(pb_road_section, lane_section)

            section_pb_lanes = []
            for lane in lane_section.left:
                pb_lane = self.create_lane(xodr_road, lane_section, idx, lane)
                # Not driving road is None
                if pb_lane is not None:
                    pb_road_section.lane_id.add().id = pb_lane.id.id
                    section_pb_lanes.append(pb_lane)
                    lane_context["pb_lane_map"][pb_lane.id.id] = pb_lane

            for lane in lane_section.right:
                pb_lane = self.create_lane(xodr_road, lane_section, idx, lane)
                if pb_lane is not None:
                    pb_road_section.lane_id.add().id = pb_lane.id.id
                    section_pb_lanes.append(pb_lane)
                    lane_context["pb_lane_map"][pb_lane.id.id] = pb_lane
            lane_context["section_lanes"].append(section_pb_lanes)
        return lane_context

    def _construct_overlap(self, pb_lane, pb_object):
        if not self._has_field(self.pb_map, "overlap"):
            return
        object_id = self._get_pb_id(pb_object)
        lane_id = self._get_pb_id(pb_lane)
        if object_id is None or lane_id is None:
            return
        pb_overlap = self.pb_map.overlap.add()
        overlap_id = "{}_{}".format(lane_id, object_id)
        pb_overlap.id.id = overlap_id
        pb_overlap.object.add().id.id = lane_id
        pb_overlap.object.add().id.id = object_id
        self._add_overlap_reference(pb_lane, overlap_id)
        self._add_overlap_reference(pb_object, overlap_id)

    def _construct_stopline(self, section_lanes, pb_map_object, signal_s=None):
        if not section_lanes:
            return
        if not self._has_field(pb_map_object, "stop_line"):
            return
        pb_left_lane = section_lanes[0]
        pb_right_lane = section_lanes[-1]
        if not pb_left_lane.left_boundary.curve.segment or \
                not pb_right_lane.right_boundary.curve.segment:
            return
        left_points = pb_left_lane.left_boundary.curve.segment[-1].line_segment.point
        right_points = pb_right_lane.right_boundary.curve.segment[-1].line_segment.point
        if not left_points or not right_points:
            return

        left_idx = len(left_points) - 1
        right_idx = len(right_points) - 1
        if signal_s is not None:
            left_meta = self.lane_details.get(pb_left_lane.id.id)
            right_meta = self.lane_details.get(pb_right_lane.id.id)
            if left_meta and left_meta["center_s"]:
                left_idx = min(range(len(left_meta["center_s"])),
                               key=lambda i: abs(left_meta["center_s"][i] - signal_s))
                left_idx = min(left_idx, len(left_points) - 1)
            if right_meta and right_meta["center_s"]:
                right_idx = min(range(len(right_meta["center_s"])),
                                key=lambda i: abs(right_meta["center_s"][i] - signal_s))
                right_idx = min(right_idx, len(right_points) - 1)
        else:
            sampling_length = global_var.get_element_value("sampling_length")
            index = math.ceil(STOP_LINE_DISTANCE/sampling_length)
            if len(left_points) >= index:
                left_idx = len(left_points) - index
            if len(right_points) >= index:
                right_idx = len(right_points) - index

        pb_stop_line = pb_map_object.stop_line.add()
        pb_segment = pb_stop_line.segment.add()
        point = pb_segment.line_segment.point.add()
        point.CopyFrom(left_points[left_idx])
        point = pb_segment.line_segment.point.add()
        point.CopyFrom(right_points[right_idx])

    def _append_signal_object(self, field_names):
        target = self._get_repeated_field(self.pb_map, field_names)
        if target is None:
            return None
        return target.add()

    def _apply_signal_core_fields(self, pb_obj, object_id):
        self._set_pb_id(pb_obj, object_id)

    def _convert_traffic_light(self, xodr_road, signal, section_lanes):
        signal_s = self._to_float(signal.s)
        pb_signal = self._append_signal_object(["signal"])
        if pb_signal is None:
            self._append_unresolved("signal", xodr_road.road_id, signal.id,
                                    "apollo map has no signal field")
            return
        self._apply_signal_core_fields(
            pb_signal, "signal_{}_{}".format(xodr_road.road_id, signal.id))
        if self.enable_association and section_lanes:
            self._construct_stopline(section_lanes, pb_signal, signal_s=signal_s)
            for pb_lane in section_lanes:
                self._construct_overlap(pb_lane, pb_signal)
        else:
            self._append_unresolved("signal_association_todo", xodr_road.road_id, signal.id,
                                    "signal-lane association is deferred")
        self.conversion_report["counts"]["signals"] += 1

    def _convert_stop_sign(self, xodr_road, signal, section_lanes):
        signal_s = self._to_float(signal.s)
        pb_stop_sign = self._append_signal_object(["stop_sign"])
        if pb_stop_sign is None:
            self._append_unresolved("stop_sign", xodr_road.road_id, signal.id,
                                    "apollo map has no stop_sign field")
            return
        self._apply_signal_core_fields(
            pb_stop_sign, "stop_sign_{}_{}".format(xodr_road.road_id, signal.id))
        if self.enable_association and section_lanes:
            self._construct_stopline(section_lanes, pb_stop_sign, signal_s=signal_s)
            for pb_lane in section_lanes:
                self._construct_overlap(pb_lane, pb_stop_sign)
        else:
            self._append_unresolved("stop_sign_association_todo", xodr_road.road_id, signal.id,
                                    "stop_sign-lane association is deferred")
        self.conversion_report["counts"]["stop_signs"] += 1

    def _convert_yield_sign(self, xodr_road, signal, section_lanes):
        signal_s = self._to_float(signal.s)
        pb_yield_sign = self._append_signal_object(["yield_sign", "yield"])
        if pb_yield_sign is None:
            self._append_unresolved("yield_sign", xodr_road.road_id, signal.id,
                                    "apollo map has no yield_sign/yield field")
            return
        self._apply_signal_core_fields(
            pb_yield_sign, "yield_{}_{}".format(xodr_road.road_id, signal.id))
        if self.enable_association and section_lanes:
            self._construct_stopline(section_lanes, pb_yield_sign, signal_s=signal_s)
            for pb_lane in section_lanes:
                self._construct_overlap(pb_lane, pb_yield_sign)
        else:
            self._append_unresolved("yield_sign_association_todo", xodr_road.road_id, signal.id,
                                    "yield_sign-lane association is deferred")
        self.conversion_report["counts"]["yield_signs"] += 1

    def _convert_generic_signal(self, xodr_road, signal, section_lanes):
        signal_s = self._to_float(signal.s)
        pb_signal = self._append_signal_object(["signal"])
        if pb_signal is None:
            self._append_unresolved("signal", xodr_road.road_id, signal.id,
                                    "apollo map has no signal field")
            return
        self._apply_signal_core_fields(
            pb_signal, "signal_{}_{}".format(xodr_road.road_id, signal.id))
        self._append_unresolved("traffic_sign_type_todo", xodr_road.road_id, signal.id,
                                "signal type mapping is deferred", {
                                    "name": signal.name,
                                    "type": signal.type,
                                    "subtype": signal.subtype
                                })
        if self.enable_association and section_lanes:
            self._construct_stopline(section_lanes, pb_signal, signal_s=signal_s)
            for pb_lane in section_lanes:
                self._construct_overlap(pb_lane, pb_signal)
        else:
            self._append_unresolved("signal_association_todo", xodr_road.road_id, signal.id,
                                    "signal-lane association is deferred")
        self.conversion_report["counts"]["signals"] += 1

    def convert_signal(self, xodr_road, lane_context):
        for signal_reference in xodr_road.signals.signal_references:
            self._append_unresolved("signal_reference", xodr_road.road_id,
                                    signal_reference.id,
                                    "signalReference is not linked automatically yet")
        for signal in xodr_road.signals.signals:
            signal_s = self._to_float(signal.s, 0.0)
            section_idx = self._find_lane_section_index(xodr_road, signal_s)
            section_lanes = self._lane_candidates_in_section(lane_context, section_idx)
            section_lanes = self._filter_lanes_by_validity(section_lanes, signal.validity)

            signal_kind = self._classify_signal(signal)
            if signal_kind == "traffic_light":
                self._convert_traffic_light(xodr_road, signal, section_lanes)
            elif signal_kind == "stop_sign":
                self._convert_stop_sign(xodr_road, signal, section_lanes)
            elif signal_kind == "yield_sign":
                self._convert_yield_sign(xodr_road, signal, section_lanes)
            else:
                self._convert_generic_signal(xodr_road, signal, section_lanes)

    def _distance_to_lane(self, x, y, pb_lane):
        min_dist = None
        for segment in pb_lane.central_curve.segment:
            for point in segment.line_segment.point:
                dist = math.hypot(x - point.x, y - point.y)
                if min_dist is None or dist < min_dist:
                    min_dist = dist
        return min_dist if min_dist is not None else 1e9

    def _associate_lanes_for_parking(self, lane_context, anchor_point, section_idx):
        section_lanes = self._lane_candidates_in_section(lane_context, section_idx)
        if not section_lanes:
            return []
        best_lane = min(section_lanes,
                        key=lambda lane: self._distance_to_lane(anchor_point.x,
                                                                anchor_point.y,
                                                                lane))
        distance = self._distance_to_lane(anchor_point.x, anchor_point.y, best_lane)
        if distance > 15.0:
            return []
        return [best_lane]

    def _build_parking_polygon(self, xodr_object, anchor_point):
        heading = anchor_point.yaw + self._to_float(xodr_object.hdg, 0.0)
        cos_h = math.cos(heading)
        sin_h = math.sin(heading)

        local_points = []
        if xodr_object.outline is not None and xodr_object.outline.corners:
            for corner in xodr_object.outline.corners:
                local_points.append((corner.u, corner.v, corner.z))
        elif xodr_object.length and xodr_object.width:
            hl = xodr_object.length / 2.0
            hw = xodr_object.width / 2.0
            local_points = [
                (-hl, -hw, 0.0),
                (hl, -hw, 0.0),
                (hl, hw, 0.0),
                (-hl, hw, 0.0),
            ]
        else:
            return []

        polygon = []
        for u, v, z in local_points:
            x = anchor_point.x + u * cos_h - v * sin_h
            y = anchor_point.y + u * sin_h + v * cos_h
            polygon.append((x, y, anchor_point.z + z + self._to_float(xodr_object.z_offset, 0.0)))
        return polygon

    def _convert_parking_space(self, xodr_road, xodr_object, lane_context):
        anchor = self._point_on_reference_line(
            xodr_road.reference_line, self._to_float(xodr_object.s, 0.0))
        if anchor is None:
            self._append_unresolved("parking_space", xodr_road.road_id, xodr_object.id,
                                    "cannot locate anchor on reference line")
            return
        # object t-offset uses lane normal
        offset_t = self._to_float(xodr_object.t, 0.0)
        offset_z = self._to_float(xodr_object.z_offset, 0.0)
        anchor_x = anchor.x + offset_t * (-math.sin(anchor.yaw))
        anchor_y = anchor.y + offset_t * math.cos(anchor.yaw)
        anchor.z = anchor.z + offset_z
        anchor.x = anchor_x
        anchor.y = anchor_y

        polygon = self._build_parking_polygon(xodr_object, anchor)
        if len(polygon) < 3:
            self._append_unresolved("parking_space", xodr_road.road_id, xodr_object.id,
                                    "parking object misses outline and size")
            return

        parking_spaces = self._get_repeated_field(self.pb_map, ["parking_space"])
        if parking_spaces is None:
            self._append_unresolved("parking_space", xodr_road.road_id, xodr_object.id,
                                    "apollo map has no parking_space field")
            return

        pb_parking = parking_spaces.add()
        self._set_pb_id(
            pb_parking, "parking_{}_{}".format(xodr_road.road_id, xodr_object.id))
        for x, y, z in polygon:
            pb_point = pb_parking.polygon.point.add()
            pb_point.x = x
            pb_point.y = y
            pb_point.z = z

        section_idx = self._find_lane_section_index(
            xodr_road, self._to_float(xodr_object.s, 0.0))
        if self.enable_association:
            lanes = self._associate_lanes_for_parking(
                lane_context, anchor, section_idx)
            if not lanes:
                self._append_unresolved("parking_space", xodr_road.road_id, xodr_object.id,
                                        "cannot find nearby lane")
            for pb_lane in lanes:
                self._construct_overlap(pb_lane, pb_parking)
        else:
            self._append_unresolved("parking_space_association_todo", xodr_road.road_id,
                                    xodr_object.id,
                                    "parking_space-lane association is deferred")
        self.conversion_report["counts"]["parking_spaces"] += 1

    def convert_objects(self, xodr_road, lane_context):
        for xodr_object in xodr_road.objects.objects:
            if xodr_object.is_parking_space():
                self._convert_parking_space(xodr_road, xodr_object, lane_context)

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

            lane_context = self.convert_lane(xodr_road, pb_road)
            self.convert_signal(xodr_road, lane_context)
            self.convert_objects(xodr_road, lane_context)

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

    def _save_conversion_report(self, output_file_name):
        report_path = "{}_conversion_report.json".format(output_file_name)
        with open(report_path, "w", encoding="utf-8") as fp:
            json.dump(self.conversion_report, fp, ensure_ascii=False, indent=2)

    def save_map(self):
        output_file_name = self.output_file_name
        if output_file_name is None:
            output_file_name = "default"
        write_pb_to_text_file(self.pb_map, output_file_name)
        write_pb_to_bin_file(self.pb_map, output_file_name)
        self._save_conversion_report(output_file_name)
