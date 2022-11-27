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

class Signal():
  def __init__(self, s=None, t=None, s_id=None, name=None, dynamic=None,
      orientation=None, zOffset=None, country=None, countryRevision=None,
      s_type=None, subtype=None, value=None, unit=None, height=None,
      width=None, hOffset=None):
    self.s = s
    self.t = t
    self.id = s_id
    self.name = name
    self.dynamic = dynamic
    self.orientation = orientation
    self.zOffset = zOffset
    self.country = country
    self.countryRevision = countryRevision
    self.type = s_type
    self.subtype = subtype
    self.value = value
    self.unit = unit
    self.height = height
    self.width = width
    self.hOffset = hOffset

  def parse_from(self, raw_signal):
    self.s = raw_signal.attrib.get('s')
    self.t = raw_signal.attrib.get('t')
    self.id = raw_signal.attrib.get('id')
    self.name = raw_signal.attrib.get('name')
    self.dynamic = raw_signal.attrib.get('dynamic')
    self.orientation = raw_signal.attrib.get('orientation')
    self.zOffset = raw_signal.attrib.get('zOffset')
    self.country = raw_signal.attrib.get('country')
    self.countryRevision = raw_signal.attrib.get('countryRevision')
    self.type = raw_signal.attrib.get('type')
    self.subtype = raw_signal.attrib.get('subtype')
    self.value = raw_signal.attrib.get('value')
    self.unit = raw_signal.attrib.get('unit')
    self.height = raw_signal.attrib.get('height')
    self.width = raw_signal.attrib.get('width')
    self.hOffset = raw_signal.attrib.get('hOffset')


class Signals():
  def __init__(self):
    self.signals = []

  def parse_from(self, raw_signals):
    if raw_signals is None:
      return

    for raw_signal in raw_signals.iter('signal'):
      signal = Signal()
      signal.parse_from(raw_signal)
      self.signals.append(signal)
