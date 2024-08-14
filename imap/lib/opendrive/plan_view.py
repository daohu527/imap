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


import math

from imap.lib.common import Point3d
from imap.lib.odr_spiral import odr_spiral, odr_arc
from imap.lib.polynoms import cubic_polynoms, parametric_cubic_curve
from imap.lib.transform import Transform


class Geometry:
    def __init__(self, s=None, x=None, y=None, hdg=None, length=None):
        self.s = s
        self.x = x
        self.y = y
        self.hdg = hdg
        self.length = length

    def parse_from(self, raw_geometry):
        self.s = float(raw_geometry.attrib.get('s'))
        self.x = float(raw_geometry.attrib.get('x'))
        self.y = float(raw_geometry.attrib.get('y'))
        self.hdg = float(raw_geometry.attrib.get('hdg'))
        self.length = float(raw_geometry.attrib.get('length'))

    def sampling(self, delta_s, elevation_profile):
        sample_count = math.ceil(self.length / delta_s) + 1

        tf = Transform(self.x, self.y, 0, self.hdg, 0, 0)

        points = []
        for i in range(sample_count):
            s, t, h = min(i * delta_s, self.length), 0, 0
            x, y, z = tf.transform(s, t, h)

            absolute_s = self.s + s

            point3d = Point3d(x, y, z, absolute_s)
            point3d.set_rotate(self.hdg)
            points.append(point3d)
        return points


class Spiral(Geometry):
    def __init__(self, s=None, x=None, y=None, hdg=None, length=None,
                 curv_start=None, curv_end=None):
        super().__init__(s, x, y, hdg, length)
        self.curv_start = curv_start
        self.curv_end = curv_end

    def parse_from(self, raw_geometry):
        super().parse_from(raw_geometry)
        raw_spiral = raw_geometry.find('spiral')
        self.curv_start = float(raw_spiral.attrib.get('curvStart'))
        self.curv_end = float(raw_spiral.attrib.get('curvEnd'))

        self.cdot = (self.curv_end - self.curv_start) / self.length
        self.s0_spiral = self.curv_start / self.cdot
        self.s0, self.t0, self.theta0 = odr_spiral(self.s0_spiral, self.cdot)

    def sampling(self, delta_s, elevation_profile):
        sample_count = math.ceil(self.length / delta_s) + 1

        tf = Transform(self.x, self.y, 0, self.hdg - self.theta0, 0, 0)

        points = []
        for i in range(sample_count):
            local_s = min(i * delta_s, self.length)
            s, t, theta = odr_spiral(local_s + self.s0_spiral, self.cdot)
            x, y, z = tf.transform(s - self.s0, t - self.t0, 0.0)
            z = elevation_profile.get_elevation_by_s(local_s)

            absolute_s = self.s + local_s

            point3d = Point3d(x, y, z, absolute_s)
            point3d.set_rotate(self.hdg + theta - self.theta0)
            points.append(point3d)
        return points


class Arc(Geometry):
    def __init__(self, s=None, x=None, y=None, hdg=None, length=None,
                 curvature=None):
        super().__init__(s, x, y, hdg, length)
        self.curvature = curvature

    def parse_from(self, raw_geometry):
        super().parse_from(raw_geometry)
        raw_arc = raw_geometry.find('arc')
        self.curvature = float(raw_arc.attrib.get('curvature'))

    def sampling(self, delta_s, elevation_profile):
        sample_count = math.ceil(self.length / delta_s) + 1
        tf = Transform(self.x, self.y, 0, self.hdg, 0, 0)

        points = []
        for i in range(sample_count):
            local_s = min(i * delta_s, self.length)
            s, t, theta = odr_arc(local_s, self.curvature)
            x, y, z = tf.transform(s, t, 0.0)
            z = elevation_profile.get_elevation_by_s(local_s)

            # get elevation
            absolute_s = self.s + local_s

            point3d = Point3d(x, y, z, absolute_s)
            point3d.set_rotate(self.hdg + theta)
            points.append(point3d)
        return points


class Poly3(Geometry):
    def __init__(self, s=None, x=None, y=None, hdg=None, length=None,
                 a=None, b=None, c=None, d=None):
        super().__init__(s, x, y, hdg, length)
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def parse_from(self, raw_geometry):
        super().parse_from(raw_geometry)

        raw_poly3 = raw_geometry.find('poly3')
        self.a = float(raw_poly3.attrib.get('a'))
        self.b = float(raw_poly3.attrib.get('b'))
        self.c = float(raw_poly3.attrib.get('c'))
        self.d = float(raw_poly3.attrib.get('d'))

    def sampling(self, delta_s, elevation_profile):
        sample_count = math.ceil(self.length / delta_s) + 1
        tf = Transform(self.x, self.y, 0, self.hdg, 0, 0)

        points = []
        for i in range(sample_count):
            local_s = min(i * delta_s, self.length)
            s, t, theta = cubic_polynoms(
                self.a, self.b, self.c, self.d, local_s)
            x, y, z = tf.transform(s, t, 0.0)
            z = elevation_profile.get_elevation_by_s(local_s)

            absolute_s = self.s + local_s

            point3d = Point3d(x, y, z, absolute_s)
            point3d.set_rotate(self.hdg + theta)
            points.append(point3d)
        return points


class ParamPoly3(Geometry):
    def __init__(self, s=None, x=None, y=None, hdg=None, length=None,
                 aU=None, bU=None, cU=None, dU=None,
                 aV=None, bV=None, cV=None, dV=None, pRange=None):
        super().__init__(s, x, y, hdg, length)
        self.aU = aU
        self.bU = bU
        self.cU = cU
        self.dU = dU
        self.aV = aV
        self.bV = bV
        self.cV = cV
        self.dV = dV
        self.pRange = pRange

    def parse_from(self, raw_geometry):
        super().parse_from(raw_geometry)
        raw_param_poly3 = raw_geometry.find('paramPoly3')

        self.aU = float(raw_param_poly3.attrib.get('aU'))
        self.bU = float(raw_param_poly3.attrib.get('bU'))
        self.cU = float(raw_param_poly3.attrib.get('cU'))
        self.dU = float(raw_param_poly3.attrib.get('dU'))
        self.aV = float(raw_param_poly3.attrib.get('aV'))
        self.bV = float(raw_param_poly3.attrib.get('bV'))
        self.cV = float(raw_param_poly3.attrib.get('cV'))
        self.dV = float(raw_param_poly3.attrib.get('dV'))
        self.pRange = raw_param_poly3.attrib.get('pRange')

    def sampling(self, delta_s, elevation_profile):
        sample_count = math.ceil(self.length / delta_s) + 1
        tf = Transform(self.x, self.y, 0, self.hdg, 0, 0)

        points = []
        for i in range(sample_count):
            local_s = min(i * delta_s, self.length)
            if self.pRange == "arcLength":
                s, t, theta = parametric_cubic_curve(
                    self.aU, self.bU, self.cU, self.dU,
                    self.aV, self.bV, self.cV, self.dV, local_s)
            elif self.pRange == "normalized":
                s, t, theta = parametric_cubic_curve(
                    self.aU, self.bU, self.cU, self.dU,
                    self.aV, self.bV, self.cV, self.dV, local_s/self.length)
            else:
                print("Unsupported pRange type: {}".format(self.pRange))
                return []
            x, y, z = tf.transform(s, t, 0.0)
            z = elevation_profile.get_elevation_by_s(local_s)

            absolute_s = self.s + local_s

            point3d = Point3d(x, y, z, absolute_s)
            point3d.set_rotate(self.hdg + theta)
            points.append(point3d)
        return points


class PlanView:
    def __init__(self):
        self.geometrys = []

    def add_geometry(self, geometry):
        self.geometrys.append(geometry)

    def parse_from(self, raw_plan_view):
        for raw_geometry in raw_plan_view.iter('geometry'):
            if raw_geometry[0].tag == 'line':
                geometry = Geometry()
            elif raw_geometry[0].tag == 'spiral':
                geometry = Spiral()
            elif raw_geometry[0].tag == 'arc':
                geometry = Arc()
            elif raw_geometry[0].tag == 'poly3':  # deprecated in OpenDrive 1.6.0
                geometry = Poly3()
            elif raw_geometry[0].tag == 'paramPoly3':
                geometry = ParamPoly3()
            else:
                # Todo(zero): raise an exception
                print("geometry type not support")

            geometry.parse_from(raw_geometry)
            self.add_geometry(geometry)
