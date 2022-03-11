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


class Converter:
  def __init__(self) -> None:
    pass

  def convert(self):
    pass


class Opendrive2Apollo(Converter):
  def __init__(self, input_file_name, output_file_name) -> None:
    self.load_input_file(input_file_name)
    self.pb_map = map_pb2.Map()
    self.output_file_name = output_file_name


  def load_input_file(self, input_file_name):
    self.xodr_map = Map()
    self.xodr_map.load(input_file_name)


  def parse_header(self):
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

  def parse_roads(self):
    for xodr_road in self.xodr_map.roads:
      pb_road = self.pb_map.road.add()
      pb_road.id.id = xodr_road.road_id
      pb_road.junction_id.id = xodr_road.junction_id

      # The definition of road type is inconsistent
      # https://releases.asam.net/OpenDRIVE/1.6.0/ASAM_OpenDRIVE_BS_V1-6-0.html#_road_type
      if xodr_road.road_type.road_type is None:
        pb_road.type = map_road_pb2.Road.CITY_ROAD

      xodr_road.generate_reference_line()

      # Todo(zero):
      draw_line(reference_line, 'r')


  def parse_junctions(self):
    for xodr_junction in self.xodr_map.junctions:
      pb_junction = self.pb_map.junction.add()
      pb_junction.id.id = xodr_junction.junction_id
      # TODO(zero): pb_junction polygon
      # pb_junction.polygon.point.add()


  def convert(self):
    self.parse_header()
    self.parse_junctions()
    self.parse_roads()
    self.save_map()

  def save_map(self):
    write_pb_to_text_file(self.pb_map, self.output_file_name)

