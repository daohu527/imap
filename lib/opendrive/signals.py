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



class Signal:
  def __init__(self, name = None, signal_id = None, s = None, t = None, \
        zOffset = None, hOffset = None, roll = None, pitch = None, \
        orientation = None, dynamic = None, country = None, \
        signal_type = None, subtype = None, value = None, \
        text = None, height = None, width = None) -> None:
    self.name = name
    self.signal_id = signal_id
    self.s = s
    self.t = t
    self.zOffset = zOffset
    self.hOffset = hOffset
    self.roll = roll
    self.pitch = pitch
    self.orientation = orientation
    self.dynamic = dynamic
    self.country = country
    self.signal_type = signal_type
    self.subtype = subtype
    self.value = value
    self.text = text
    self.height = height
    self.width = width

    # private
    self.boundary = None


  def parse_from(self, raw_signal):
    if raw_signal is not None:
      self.name = raw_signal.attrib.get('name')
      self.signal_id = raw_signal.attrib.get('id')
      self.s = float(raw_signal.attrib.get('s'))
      self.t = float(raw_signal.attrib.get('t'))
      self.zOffset = float(raw_signal.attrib.get('zOffset'))
      self.hOffset = float(raw_signal.attrib.get('hOffset'))
      self.roll = float(raw_signal.attrib.get('roll'))
      self.pitch = float(raw_signal.attrib.get('pitch'))
      self.orientation = raw_signal.attrib.get('orientation')
      self.dynamic = raw_signal.attrib.get('dynamic')
      self.country = raw_signal.attrib.get('country')
      self.signal_type = float(raw_signal.attrib.get('type'))
      self.subtype = float(raw_signal.attrib.get('subtype'))
      self.value = float(raw_signal.attrib.get('value'))
      self.text = raw_signal.attrib.get('text')
      if raw_signal.attrib.get('height') is not None:
        self.height = float(raw_signal.attrib.get('height'))
      if raw_signal.attrib.get('width') is not None:
        self.width = float(raw_signal.attrib.get('width'))
      self.generate_boundary()

  def generate_boundary(self):
    if self.width and self.height:
      self.boundary = [[0, self.width/2, 0], \
                       [0, -self.width/2, 0], \
                       [0, -self.width/2, self.height], \
                       [0, self.width/2, self.height]]

  def get_boundary(self, x, y):
    pass


class Signals:
  def __init__(self) -> None:
    self.signals = []

  def add_signal(self, signal):
    self.signals.append(signal)

  def parse_from(self, raw_signals):
    if raw_signals is None:
      return

    for raw_signal in raw_signals.iter("signal"):
      signal = Signal()
      signal.parse_from(raw_signal)
      self.add_signal(signal)
