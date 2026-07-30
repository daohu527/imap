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


def _to_float(raw_value, default=None):
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


class CornerLocal:
    def __init__(self):
        self.u = None
        self.v = None
        self.z = 0.0

    def parse_from(self, raw_corner):
        self.u = _to_float(raw_corner.attrib.get("u"), 0.0)
        self.v = _to_float(raw_corner.attrib.get("v"), 0.0)
        self.z = _to_float(raw_corner.attrib.get("z"), 0.0)


class Outline:
    def __init__(self):
        self.corners = []

    def parse_from(self, raw_outline):
        for raw_corner in raw_outline.iter("cornerLocal"):
            corner = CornerLocal()
            corner.parse_from(raw_corner)
            self.corners.append(corner)


class RoadObject:
    def __init__(self):
        self.id = None
        self.name = None
        self.s = None
        self.t = None
        self.z_offset = 0.0
        self.hdg = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.orientation = None
        self.length = None
        self.width = None
        self.radius = None
        self.type = None
        self.subtype = None
        self.outline = None

    def parse_from(self, raw_object):
        self.id = raw_object.attrib.get("id")
        self.name = raw_object.attrib.get("name")
        self.s = _to_float(raw_object.attrib.get("s"), 0.0)
        self.t = _to_float(raw_object.attrib.get("t"), 0.0)
        self.z_offset = _to_float(raw_object.attrib.get("zOffset"), 0.0)
        self.hdg = _to_float(raw_object.attrib.get("hdg"), 0.0)
        self.pitch = _to_float(raw_object.attrib.get("pitch"), 0.0)
        self.roll = _to_float(raw_object.attrib.get("roll"), 0.0)
        self.orientation = raw_object.attrib.get("orientation")
        self.length = _to_float(raw_object.attrib.get("length"))
        self.width = _to_float(raw_object.attrib.get("width"))
        self.radius = _to_float(raw_object.attrib.get("radius"))
        self.type = raw_object.attrib.get("type")
        self.subtype = raw_object.attrib.get("subtype")

        raw_outline = raw_object.find("outline")
        if raw_outline is not None:
            outline = Outline()
            outline.parse_from(raw_outline)
            self.outline = outline

    def is_parking_space(self):
        lower_type = (self.type or "").lower()
        lower_subtype = (self.subtype or "").lower()
        lower_name = (self.name or "").lower()
        return "parking" in lower_type or \
            "parking" in lower_subtype or \
            "parking" in lower_name


class Objects:
    def __init__(self):
        self.objects = []

    def parse_from(self, raw_objects):
        if raw_objects is None:
            return

        for raw_object in raw_objects.iter("object"):
            road_object = RoadObject()
            road_object.parse_from(raw_object)
            self.objects.append(road_object)
