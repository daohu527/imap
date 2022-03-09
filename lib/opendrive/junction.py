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


class Connection:
  def __init__(self, connection_id, connection_type, incoming_road, connecting_road, contact_point):
    self.connection_id = connection_id
    self.connection_type = connection_type
    self.incoming_road = incoming_road
    self.connecting_road = connecting_road
    self.contact_point = contact_point

class Junction:
  def __init__(self, junction_id, name, junction_type):
    self.junction_id = junction_id
    self.name = name
    self.junction_type = junction_type
    self.connections = []

  def add_connection(self, connection):
    self.connections.append(connection)
