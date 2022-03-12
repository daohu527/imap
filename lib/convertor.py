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


from modules.map.proto import map_pb2
from modules.map.proto import map_road_pb2
from modules.map.proto import map_lane_pb2

from lib.opendrive.map import Map
from lib.proto_utils import write_pb_to_text_file

from lib.draw import draw_line, show


def to_pb_lane_type(open_drive_type):
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
  elif lower_type == 'restricted': # not support
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
  elif lower_type == 'connectingRamp': # not support
    return map_lane_pb2.Lane.NONE


class Convertor:
  def __init__(self) -> None:
    pass

  def convert(self):
    pass


class Opendrive2Apollo(Convertor):
  def __init__(self, input_file_name, output_file_name) -> None:
    self.xodr_map = Map()
    self.xodr_map.load(input_file_name)

    self.pb_map = map_pb2.Map()
    self.output_file_name = output_file_name


  def convert_header(self):
    self.pb_map.header.version = self.xodr_map.header.version
    self.pb_map.header.date = self.xodr_map.header.date
    proj = self.xodr_map.header.parse_geo_reference()
    if proj is not None:
      self.pb_map.header.projection.proj = proj
    else:
      zone_id = 0
      self.pb_map.header.projection.proj = "+proj=utm +zone={} +ellps=WGS84 " \
          "+datum=WGS84 +units=m +no_defs".format(zone_id)

    # TODO(zero): Inconsistent definitions
    # self.pb_map.header.district = self.xodr_map.header.name
    self.pb_map.header.rev_major = self.xodr_map.header.rev_major
    self.pb_map.header.rev_minor = self.xodr_map.header.rev_minor
    self.pb_map.header.left = self.xodr_map.header.west
    self.pb_map.header.right = self.xodr_map.header.east
    self.pb_map.header.top = self.xodr_map.header.north
    self.pb_map.header.bottom = self.xodr_map.header.south
    self.pb_map.header.vendor = self.xodr_map.header.vendor


  def add_basic_info(self, pb_lane, xodr_road, idx, lane):
    pb_lane.id.id = "road_{}_lane_{}_{}".format(xodr_road.road_id, \
        idx, lane.lane_id)
    pb_lane.type = to_pb_lane_type(lane.lane_type)
    pb_lane.length = lane.length
    if lane.speed.max_v:
      pb_lane.speed_limit = lane.speed.max_v
    pb_lane.direction = map_lane_pb2.Lane.FORWARD


  def add_lane_boundary(self, pb_lane, lane):
    # 1. left boundary
    segment = pb_lane.left_boundary.curve.segment.add()
    for point3d in lane.left_boundary:
      point = segment.line_segment.point.add()
      point.x, point.y = point3d.x, point3d.y
    segment.s = 0
    segment.start_position.x = lane.left_boundary[0].x
    segment.start_position.y = lane.left_boundary[0].y
    segment.start_position.z = lane.left_boundary[0].z
    segment.length = pb_lane.length
    pb_lane.left_boundary.length = pb_lane.length

    # 2. center line
    segment = pb_lane.central_curve.segment.add()
    for point3d in lane.center_line:
      point = segment.line_segment.point.add()
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
      point.x, point.y = point3d.x, point3d.y
    segment.s = 0
    segment.start_position.x = lane.right_boundary[0].x
    segment.start_position.y = lane.right_boundary[0].y
    segment.start_position.z = lane.right_boundary[0].z
    segment.length = pb_lane.length
    pb_lane.right_boundary.length = pb_lane.length

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

  def add_lane_relationships(self, pb_lane, xodr_road, lane_section, idx, lane):
    if lane_section == xodr_road.lanes.lane_sections[0]:
      # road link
      predecessor_road = xodr_road.link.predecessor_road
      if predecessor_road and lane.link.predecessor:
        n = len(predecessor_road.lanes.lane_sections)
        pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format( \
            predecessor_road.road_id, n-1, lane.link.predecessor.link_id)
      if lane.link.successor:
        pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format( \
            xodr_road.road_id, idx + 1, lane.link.successor.link_id)
      # junction
      predecessor_junction = xodr_road.link.predecessor_junction
      if predecessor_junction:
        for connection in predecessor_junction.connections:
          if connection.connecting_road == xodr_road.road_id:
            n = len(connection.incoming_road_obj.lanes.lane_sections)
            pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format( \
                connection.incoming_road, n-1, connection.lane_link.from_id)
    # successor road
    elif lane_section == xodr_road.lanes.lane_sections[-1]:
      if lane.link.predecessor:
        pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format( \
            xodr_road.road_id, idx - 1, lane.link.predecessor.link_id)
      if lane.link.successor:
        pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format( \
            xodr_road.link.successor.element_id, 0, lane.link.successor.link_id)
      # junction
      successor_junction = xodr_road.link.successor_junction
      if successor_junction:
        for connection in successor_junction.connections:
          if connection.incoming_road == xodr_road.road_id:
            pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format( \
                connection.connecting_road, 0, connection.lane_link.to_id)
    else:
      if lane.link.predecessor:
        pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format( \
            xodr_road.road_id, idx - 1, lane.link.predecessor.link_id)
      if lane.link.successor:
        pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format( \
            xodr_road.road_id, idx + 1, lane.link.successor.link_id)

  def create_lane(self, xodr_road, lane_section, idx, lane):
    pb_lane = self.pb_map.lane.add()
    self.add_basic_info(pb_lane, xodr_road, idx, lane)
    # add boundary
    self.add_lane_boundary(pb_lane, lane)
    # add neighbor
    self.add_lane_neighbors(pb_lane, xodr_road, idx, lane)
    # predecessor road
    self.add_lane_relationships(pb_lane, xodr_road, lane_section, idx, lane)

  def convert_lane(self, xodr_road):
    for idx, lane_section in enumerate(xodr_road.lanes.lane_sections):
      for lane in lane_section.left:
        self.create_lane(xodr_road, lane_section, idx, lane)

      for lane in lane_section.right:
        self.create_lane(xodr_road, lane_section, idx, lane)


  def convert_roads(self):
    for _, xodr_road in self.xodr_map.roads.items():
      pb_road = self.pb_map.road.add()
      pb_road.id.id = xodr_road.road_id
      pb_road.junction_id.id = xodr_road.junction_id

      # The definition of road type is inconsistent
      if xodr_road.road_type.road_type is None:
        pb_road.type = map_road_pb2.Road.CITY_ROAD

      xodr_road.generate_reference_line()
      xodr_road.add_offset_to_reference_line()
      # Todo(zero):
      draw_line(xodr_road.reference_line, 'r')

      xodr_road.process_lanes()

      self.convert_lane(xodr_road)


  def convert_junctions(self):
    for _, xodr_junction in self.xodr_map.junctions.items():
      pb_junction = self.pb_map.junction.add()
      pb_junction.id.id = xodr_junction.junction_id
      # TODO(zero): pb_junction polygon
      # pb_junction.polygon.point.add()


  def convert(self):
    self.convert_header()
    self.convert_junctions()
    self.convert_roads()
    self.save_map()
    show()

  def save_map(self):
    write_pb_to_text_file(self.pb_map, self.output_file_name)

