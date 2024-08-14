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
    def __init__(self, from_id=None, to_id=None):
        self.from_id = from_id
        self.to_id = to_id

    def parse_from(self, raw_lane_link):
        if raw_lane_link is not None:
            self.from_id = raw_lane_link.attrib.get('from')
            self.to_id = raw_lane_link.attrib.get('to')


class Connection:
    def __init__(self, connection_id=None, connection_type=None,
                 incoming_road=None, connecting_road=None,
                 contact_point=None):
        self.connection_id = connection_id
        self.connection_type = connection_type
        self.incoming_road = incoming_road
        self.connecting_road = connecting_road
        self.contact_point = contact_point
        self.lane_links = []

        # private
        self.incoming_road_obj = None
        self.connecting_road_obj = None

    def parse_from(self, raw_connection):
        if raw_connection is None:
            return

        self.connection_id = raw_connection.attrib.get('id')
        self.connection_type = raw_connection.attrib.get('type')
        self.incoming_road = raw_connection.attrib.get('incomingRoad')
        self.connecting_road = raw_connection.attrib.get('connectingRoad')
        self.contact_point = raw_connection.attrib.get('contactPoint')

        for raw_lane_link in raw_connection.iter('laneLink'):
            lane_link = Link()
            lane_link.parse_from(raw_lane_link)
            self.lane_links.append(lane_link)

    def incoming_lane_link(self, road_id, lane_id):
        if self.incoming_road != road_id:
            return None

        for lane_link in self.lane_links:
            if lane_link.from_id == lane_id:
                return lane_link

        return None


class Junction:
    def __init__(self, junction_id=None, name=None, junction_type=None):
        self.junction_id = junction_id
        self.name = name
        self.junction_type = junction_type
        self.connections = []

        # private
        self.predecessor_dict = {}
        self.connected_roads = []

    def add_connection(self, connection):
        self.connections.append(connection)

    def parse_from(self, raw_junction):
        self.junction_id = raw_junction.attrib.get('id')
        self.name = raw_junction.attrib.get('name')
        self.junction_type = raw_junction.attrib.get('type')

        for raw_connection in raw_junction.iter('connection'):
            connection = Connection()
            connection.parse_from(raw_connection)
            self.add_connection(connection)

    def get_predecessors(self, road_id):
        return self.predecessor_dict.get(road_id, [])

    def is_incoming_road(self, incoming_road, connecting_road):
        for connection in self.connections:
            if connection.incoming_road == incoming_road and \
               connection.connecting_road == connecting_road:
                return True
        return False
