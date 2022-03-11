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

from lib.opendrive.header import Header
from lib.opendrive.road import Road
from lib.opendrive.junction import Junction


class Map:
  def __init__(self):
    self.header = Header()
    self.roads = []
    self.junctions = []

  def parse_roads(self, raw_roads):
    for raw_road in raw_roads:
      road = Road()
      road.parse_from(raw_road)
      self.roads.append(road)

  def parse_junctions(self, raw_junctions):
    if not raw_junctions:
      return

    for raw_junction in raw_junctions:
      junction = Junction()
      junction.parse_from(raw_junction)
      self.junctions.append(junction)

  def load(self, filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    assert root is not None, "Map XML failed!"
    assert root.tag == 'OpenDRIVE'

    # 1. header
    raw_header = root.find('header')
    assert raw_header is not None, "Open drive map missing header"
    self.header.parse_from(raw_header)

    # 2. road
    raw_roads = root.findall('road')
    assert raw_roads is not None, "Open drive map missing roads"
    self.parse_roads(raw_roads)

    # 3. junction
    raw_junctions = root.findall('junction')
    self.parse_junctions(raw_junctions)
