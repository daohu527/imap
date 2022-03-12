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


class Link:
  def __init__(self, from_id = None, to_id = None):
    self.from_id = from_id
    self.to_id = to_id

  def parse_from(self, raw_lane_link):
    self.from_id = raw_lane_link.attrib.get('from')
    self.to_id = raw_lane_link.attrib.get('to')


class Connection:
  def __init__(self, connection_id, connection_type, incoming_road, \
               connecting_road, contact_point):
    self.connection_id = connection_id
    self.connection_type = connection_type
    self.incoming_road = incoming_road
    self.connecting_road = connecting_road
    self.contact_point = contact_point
    self.lane_link = Link()

    # private
    self.incoming_road_obj = None

class Junction:
  def __init__(self, junction_id = None, name = None, junction_type = None):
    self.junction_id = junction_id
    self.name = name
    self.junction_type = junction_type
    self.connections = []

  def add_connection(self, connection):
    self.connections.append(connection)

  def parse_from(self, raw_junction):
    self.junction_id = raw_junction.attrib.get('id')
    self.name = raw_junction.attrib.get('name')
    self.junction_type = raw_junction.attrib.get('type')

    for raw_connection in raw_junction.iter('connection'):
      connection_id = raw_connection.attrib.get('id')
      connection_type = raw_connection.attrib.get('type')
      incoming_road = raw_connection.attrib.get('incomingRoad')
      connecting_road = raw_connection.attrib.get('connectingRoad')
      contact_point = raw_connection.attrib.get('contactPoint')
      connection = Connection(connection_id, connection_type, incoming_road, \
                      connecting_road, contact_point)

      raw_lane_link = raw_junction.find('laneLink')
      if raw_lane_link:
        connection.lane_link.parse_from(raw_lane_link)
      self.add_connection(connection)
