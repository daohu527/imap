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


class Object:
  def __init__(self, object_id = None, name = None, s = None, t = None, \
        zOffset = None, hdg = None, roll = None, pitch = None, \
        orientation = None, object_type = None, height = None, \
        width = None, length = None) -> None:
    self.object_id = object_id
    self.name = name
    self.s = s
    self.t = t
    self.zOffset = zOffset
    self.hdg = hdg
    self.roll = roll
    self.pitch = pitch
    self.orientation = orientation
    self.object_type = object_type
    self.height = height
    self.width = width
    self.length = length


  def parse_from(self, raw_object):
    if raw_object is not None:
      self.object_id = raw_object.attrib.get('id')
      self.name = raw_object.attrib.get('name')
      self.s = float(raw_object.attrib.get('s'))
      self.t = float(raw_object.attrib.get('t'))
      self.zOffset = float(raw_object.attrib.get('zOffset'))
      self.hdg = float(raw_object.attrib.get('hdg'))
      self.roll = float(raw_object.attrib.get('roll'))
      self.pitch = float(raw_object.attrib.get('pitch'))
      self.orientation = raw_object.attrib.get('orientation')
      self.object_type = float(raw_object.attrib.get('type'))
      self.height = float(raw_object.attrib.get('height'))
      self.width = float(raw_object.attrib.get('width'))
      self.length = float(raw_object.attrib.get('length'))


class Objects:
  def __init__(self) -> None:
    self.objects = []

  def add_object(self, object):
    self.objects.append(object)

  def parse_from(self, raw_objects):
    if raw_objects is None:
      return

    for raw_object in raw_objects.iter("object"):
      object = Object()
      object.parse_from(raw_object)
      self.add_object(object)
