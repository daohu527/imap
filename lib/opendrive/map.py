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


from lib.opendrive.header import Header


class Map:
  def __init__(self):
    self.header = None
    self.roads = []
    self.junctions = []

  def parse_header(self, raw_header):
    rev_major = raw_header.attrib.get('revMajor').encode()
    rev_minor = raw_header.attrib.get('revMinor').encode()
    name = raw_header.attrib.get('name').encode()
    version = raw_header.attrib.get('version').encode()
    date = raw_header.attrib.get('date').encode()
    west = float(raw_header.attrib.get('west'))
    east = float(raw_header.attrib.get('east'))
    north = float(raw_header.attrib.get('north'))
    south = float(raw_header.attrib.get('south'))
    vendor = raw_header.attrib.get('vendor').encode()

    self.header = Header(rev_major, rev_minor, name, version, date, north, \
                         south, east, west, vendor)


  def parse_junctions(self, raw_junctions):
    if not raw_junctions:
      return

    for raw_junction in raw_junctions:
      junction_id = raw_junction.attrib.get('id')
      name = raw_junction.attrib.get('name')
      junction_type = raw_junction.attrib.get('type')
      junction = Junction(junction_id, name, junction_type)

      for raw_connection in raw_junction.iter('connection'):
        connection_id = raw_connection.attrib.get('id')
        connection_type = conraw_connectionnection.attrib.get('type')
        incoming_road = raw_connection.attrib.get('incomingRoad')
        connecting_road = raw_connection.attrib.get('connectingRoad')
        contact_point = raw_connection.attrib.get('contactPoint')
        connection = Connection(connection_id, connection_type, incoming_road, \
                        connecting_road, contact_point)
        junction.add_connection(connection)

      self.junctions.append(junction)


  def load(self, filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    assert root is not None, "Map XML failed!"
    assert root.tag == 'OpenDRIVE'

    # 1. header
    raw_header = root.find('header')
    assert raw_header is not None, "Open drive map missing header"
    self.parse_header(raw_header)

    # 2. road


    # 3. junction
    raw_junctions = root.findall('junction')
    self.parse_junctions(raw_junctions)
