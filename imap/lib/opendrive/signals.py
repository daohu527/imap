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

class Validity():
  def __init__(self, fromLane = None, toLane = None) -> None:
    self.from_lane = fromLane
    self.to_lane = toLane

  def parse_from(self, raw_validity):
    if raw_validity:
      self.from_lane = raw_validity.attrib.get('fromLane')
      self.to_lane = raw_validity.attrib.get('toLane')

class Dependency():
  def __init__(self, id = None, type = None):
    self.id = id
    self.type = type

  def parse_from(self, raw_dependency):
    if raw_dependency:
      self.id = raw_dependency.attrib.get('id')
      self.type = raw_dependency.attrib.get('type')

class Signal():
  def __init__(self, s=None, t=None, s_id=None, name=None, dynamic=None,
      orientation=None, pitch = None, roll = None, zOffset=None, country=None,
      countryRevision=None, s_type=None, subtype=None, text = None, value=None,
      unit=None, height=None, width=None, hOffset=None):
    self.s = s
    self.t = t
    self.id = s_id
    self.name = name
    self.dynamic = dynamic
    self.orientation = orientation
    self.pitch = pitch
    self.roll = roll

    self.zOffset = zOffset
    self.country = country
    self.countryRevision = countryRevision
    self.type = s_type
    self.subtype = subtype
    self.text = text
    self.value = value
    self.unit = unit
    self.height = height
    self.width = width
    self.hOffset = hOffset

    self.validity = Validity()
    self.dependency = Dependency()

  def parse_from(self, raw_signal):
    self.s = raw_signal.attrib.get('s')
    self.t = raw_signal.attrib.get('t')
    self.id = raw_signal.attrib.get('id')
    self.name = raw_signal.attrib.get('name')
    self.dynamic = raw_signal.attrib.get('dynamic')
    self.orientation = raw_signal.attrib.get('orientation') # "+" "-" "none"
    self.pitch = raw_signal.attrib.get('pitch') # rad
    self.roll = raw_signal.attrib.get('roll') # rad
    self.zOffset = raw_signal.attrib.get('zOffset')
    self.country = raw_signal.attrib.get('country')
    self.countryRevision = raw_signal.attrib.get('countryRevision')
    self.type = raw_signal.attrib.get('type')
    self.subtype = raw_signal.attrib.get('subtype')
    self.text = raw_signal.attrib.get('text')
    self.value = raw_signal.attrib.get('value')
    self.unit = raw_signal.attrib.get('unit')
    self.height = raw_signal.attrib.get('height')
    self.width = raw_signal.attrib.get('width')
    self.hOffset = raw_signal.attrib.get('hOffset')

    raw_validity = raw_signal.find("validity")
    self.validity.parse_from(raw_validity)
    raw_dependency = raw_signal.find("dependency")
    self.dependency.parse_from(raw_dependency)

  def is_traffic_light(self):
    # Todo(zero): Need add more country code, ref to "12. Signals"
    if self.country == "OpenDRIVE":
      if self.type == "1000001" and self.subtype == "-1":
        return True
    return False

class SignalReference():
  def __init__(self, id = None, orientation = None, s = None, t = None):
    self.id = id
    self.orientation = orientation
    self.s = s
    self.t = t

    self.validity = Validity()

  def parse_from(self, raw_signal_reference):
    self.id = raw_signal_reference.attrib.get('id')
    self.orientation = raw_signal_reference.attrib.get('orientation')
    self.s = raw_signal_reference.attrib.get('s')
    self.t = raw_signal_reference.attrib.get('t')

    raw_validity = raw_signal_reference.find("validity")
    self.validity.parse_from(raw_validity)


class Signals():
  def __init__(self):
    self.signals = []
    self.signal_references = []

  def parse_from(self, raw_signals):
    if raw_signals is None:
      return

    for raw_signal in raw_signals.iter('signal'):
      signal = Signal()
      signal.parse_from(raw_signal)
      self.signals.append(signal)

    for raw_signal_reference in raw_signals.iter('signalReference'):
      signal_reference = SignalReference()
      signal_reference.parse_from(raw_signal_reference)
      self.signal_references.append(signal_reference)
