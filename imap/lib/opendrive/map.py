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


import xml.etree.ElementTree as ET

from imap.lib.opendrive.header import Header
from imap.lib.opendrive.road import Road
from imap.lib.opendrive.junction import Junction


class Map:
  def __init__(self):
    self.header = Header()
    self.roads = {}
    self.junctions = {}

  def post_process(self):
    # add link
    for road_id, road in self.roads.items():
      # Todo(zero):
      if road.link.predecessor.element_type == "junction":
        road.link.predecessor_junction = \
            self.junctions[road.link.predecessor.element_id]
      elif road.link.predecessor.element_type == "road":
        road.link.predecessor_road = self.roads[road.link.predecessor.element_id]

      if road.link.successor.element_type == "junction":
        road.link.successor_junction = \
            self.junctions[road.link.successor.element_id]
      elif road.link.successor.element_type == "road":
        road.link.successor_road = self.roads[road.link.successor.element_id]

      # add connect relation in junctions
      if road.junction_id != "-1":
        successor_id = road.link.successor.element_id
        if not self.junctions[road.junction_id].is_incoming_road( \
                  successor_id, road.road_id):
          if successor_id not in self.junctions[road.junction_id].predecessor_dict:
            self.junctions[road.junction_id].predecessor_dict[successor_id] = []
          self.junctions[road.junction_id].predecessor_dict[successor_id]. \
              append([road, "successor"])

        predecessor_id = road.link.predecessor.element_id
        if not self.junctions[road.junction_id].is_incoming_road( \
                  predecessor_id, road.road_id):
          if predecessor_id not in self.junctions[road.junction_id].predecessor_dict:
            self.junctions[road.junction_id].predecessor_dict[predecessor_id] = []
          self.junctions[road.junction_id].predecessor_dict[predecessor_id]. \
              append([road, "predecessor"])

      # add connected roads to junctions
      if road.link.predecessor.element_type == "junction":
        junction_id = road.link.predecessor.element_id
        connected_roads = self.junctions[junction_id].connected_roads
        connected_roads.append([road, "predecessor"])
      if road.link.successor.element_type == "junction":
        junction_id = road.link.successor.element_id
        connected_roads = self.junctions[junction_id].connected_roads
        connected_roads.append([road, "successor"])

    # add junction link
    for junction_id, junction in self.junctions.items():
      for connection in junction.connections:
        connection.incoming_road_obj = self.roads[connection.incoming_road]
        connection.connecting_road_obj = self.roads[connection.connecting_road]

  def parse_roads(self, raw_roads):
    for raw_road in raw_roads:
      road = Road()
      road.parse_from(raw_road)
      self.roads[road.road_id] = road


  def parse_junctions(self, raw_junctions):
    if not raw_junctions:
      return

    for raw_junction in raw_junctions:
      junction = Junction()
      junction.parse_from(raw_junction)
      self.junctions[junction.junction_id] = junction

  def load(self, filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    assert root is not None, "Map XML failed!"
    assert root.tag == 'OpenDRIVE'

    # 1. header
    raw_header = root.find('header')
    assert raw_header is not None, "Open drive map missing header"
    self.header.parse_from(raw_header)

    # 3. junction.
    raw_junctions = root.findall('junction')
    self.parse_junctions(raw_junctions)

    # 2. road
    raw_roads = root.findall('road')
    assert raw_roads is not None, "Open drive map missing roads"
    self.parse_roads(raw_roads)

    self.post_process()
