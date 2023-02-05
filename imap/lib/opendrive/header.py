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



class GeoReference:
  def __init__(self):
    self.text = None

  def parse_from(self, raw_geo_reference):
    if raw_geo_reference is not None:
      self.text = raw_geo_reference.text


class Header:
  def __init__(self, rev_major = None, rev_minor = None, name = None,
               version = None, date = None, north = None, south = None, \
               east = None, west = None, vendor = None):
    self.rev_major = rev_major
    self.rev_minor = rev_minor
    self.name = name
    self.version = version
    self.date = date
    self.north = north
    self.south = south
    self.east = east
    self.west = west
    self.vendor = vendor
    self.geo_reference = GeoReference()

  def parse_from(self, raw_header):
    self.rev_major = raw_header.attrib.get('revMajor').encode()
    self.rev_minor = raw_header.attrib.get('revMinor').encode()
    if raw_header.attrib.get('name') is not None:
      self.name = raw_header.attrib.get('name').encode()
    if raw_header.attrib.get('version') is not None:
      self.version = raw_header.attrib.get('version').encode()
    if raw_header.attrib.get('date') is not None:
      self.date = raw_header.attrib.get('date').encode()
    if raw_header.attrib.get('east') is not None:
      self.east = float(raw_header.attrib.get('east'))
    if raw_header.attrib.get('west') is not None:
      self.west = float(raw_header.attrib.get('west'))
    if raw_header.attrib.get('south') is not None:
      self.south = float(raw_header.attrib.get('south'))
    if raw_header.attrib.get('north') is not None:
      self.north = float(raw_header.attrib.get('north'))
    if raw_header.attrib.get('vendor') is not None:
      self.vendor = raw_header.attrib.get('vendor').encode()

    raw_geo_reference = raw_header.find("geoReference")
    self.geo_reference.parse_from(raw_geo_reference)
