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
    pass


class Header:
  def __init__(self, rev_major, rev_minor, name, version, date, north, south, \
               east, west, vendor):
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
