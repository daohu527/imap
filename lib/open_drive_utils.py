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


from ast import Assert
from modules.map.proto import map_pb2

import xml.etree.ElementTree as ET


def save_map_to_xml_file(pb_value, file_path):
  pass

def parse_header(pb_map, header):
  pb_map.header.version = header.attrib.get('version')
  pb_map.header.date = header.attrib.get('date')
  # TODO(zero): need to complete
  # pb_map.header.projection.proj = \
      # "+proj=utm +zone={} +ellps=WGS84 +datum=WGS84 +units=m +no_defs".format(zone_id)

  # pb_map.header.district = header.attrib.get('name')
  pb_map.header.rev_major = header.attrib.get('revMajor')
  pb_map.header.rev_minor = header.attrib.get('revMinor')
  pb_map.header.left = header.attrib.get('west')
  pb_map.header.right = header.attrib.get('east')
  pb_map.header.south = header.attrib.get('north')
  pb_map.header.north = header.attrib.get('south')
  pb_map.header.vendor = header.attrib.get('vendor')


def parse_lane():
  pass

def parse_road():
  pass

def parse_junction():
  pass

def parse_crosswalk():
  pass

def parse_signal():
  pass

def parse_stop_sign():
  pass

def parse_yield_sign():
  pass


def get_map_from_xml_file(filename, pb_map):
  tree = ET.parse(filename)
  root = tree.getroot()
  Assert(root.tag == 'OpenDRIVE')

  header = root.find('header')
  parse_header(pb_map, header)


if __name__ == '__main__':
  map = map_pb2.Map()
  get_map_from_xml_file("data/sample.odr", map)
