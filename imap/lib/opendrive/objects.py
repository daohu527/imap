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

import abc
from enum import Enum

from imap.lib.common import shift_t, binary_search, get_rotated_rectangle_points


class ObjectType(Enum):
    BARRIER = "barrier"
    BUILDING = "building"
    CROSSWALK = "crosswalk"
    GANTRY = "gantry"
    OBSTACLE = "obstacle"
    PARKING_SPACE = "parkingSpace"
    POLE = "pole"
    ROAD_MARK = "roadMark"
    TRAFFIC_ISLAND = "trafficIsland"
    TREE = "tree"
    VEGETATION = "vegetation"


class Object(metaclass=abc.ABCMeta):
    def parse_from(self, raw_object):
        self.id = raw_object.attrib.get('id')
        self.name = raw_object.attrib.get('name')
        self.type = raw_object.attrib.get('type')
        self.subtype = raw_object.attrib.get('subtype')
        self.s = float(raw_object.attrib.get('s'))
        self.t = float(raw_object.attrib.get('t'))
        self.zOffset = float(raw_object.attrib.get('zOffset'))
        self.orientation = raw_object.attrib.get('orientation')
        self.length = float(raw_object.attrib.get('length'))
        self.width = float(raw_object.attrib.get('width'))
        self.height = float(raw_object.attrib.get('height'))
        self.hdg = float(raw_object.attrib.get('hdg'))
        self.pitch = float(raw_object.attrib.get('pitch'))
        self.roll = float(raw_object.attrib.get('roll'))
        self.radius = raw_object.attrib.get('radius')
        self.validLength = float(raw_object.attrib.get('validLength'))
        self.dynamic = raw_object.attrib.get('dynamic')
        self.perpToRoad = raw_object.attrib.get('perpToRoad')


class Barrier(Object):
    def __init__(self) -> None:
        pass


class Building(Object):
    def __init__(self) -> None:
        pass


class Crosswalk(Object):
    def __init__(self) -> None:
        pass


class Gantry(Object):
    def __init__(self) -> None:
        pass


class Obstacle(Object):
    def __init__(self) -> None:
        pass


class ParkingSpace(Object):
    def __init__(self) -> None:
        pass

    def process_corners(self, reference_line):
        # Find the point closest to s, considering adding interpolation
        idx = binary_search([point3d.s for point3d in reference_line], self.s)
        reference_point3d = reference_line[idx]
        inertial_point3d = shift_t(reference_point3d, self.t)
        center = [inertial_point3d.x, inertial_point3d.y]
        # todo(zero): Because the object's angle is relative to the road,
        # the road's angle needs to be added 'self.hdg + reference_point3d.yaw',
        # but do we need to consider the inclination of the road?
        corners = get_rotated_rectangle_points(
            center, self.hdg + reference_point3d.yaw, self.length, self.width)
        return corners


class Pole(Object):
    def __init__(self) -> None:
        pass


class RoadMark(Object):
    def __init__(self) -> None:
        pass


class TrafficIsland(Object):
    def __init__(self) -> None:
        pass


class Tree(Object):
    def __init__(self) -> None:
        pass


class Vegetation(Object):
    def __init__(self) -> None:
        pass


class Objects:
    def __init__(self) -> None:
        self.objects = []

    def parse_from(self, raw_objects):
        if raw_objects is None:
            return

        for raw_object in raw_objects.iter('object'):
            object_type = ObjectType(raw_object.attrib.get('type'))
            if object_type == ObjectType.BARRIER:
                obj = Barrier()
            elif object_type == ObjectType.BUILDING:
                obj = Building()
            elif object_type == ObjectType.CROSSWALK:
                obj = Crosswalk()
            elif object_type == ObjectType.GANTRY:
                obj = Gantry()
            elif object_type == ObjectType.OBSTACLE:
                obj = Obstacle()
            elif object_type == ObjectType.PARKING_SPACE:
                obj = ParkingSpace()
            elif object_type == ObjectType.POLE:
                obj = Pole()
            elif object_type == ObjectType.ROAD_MARK:
                obj = RoadMark()
            elif object_type == ObjectType.TRAFFIC_ISLAND:
                obj = TrafficIsland()
            elif object_type == ObjectType.TREE:
                obj = Tree()
            elif object_type == ObjectType.VEGETATION:
                obj = Vegetation()
            else:
                raise NotImplementedError(f"{object_type}")

            obj.parse_from(raw_object)
            self.objects.append(obj)
