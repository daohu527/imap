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

# hull.py
# Graham Scan - Tom Switzer <thomas.switzer@gmail.com>

import math
from functools import reduce

TURN_LEFT, TURN_RIGHT, TURN_NONE = (1, -1, 0)


def cmp(a, b):
    return (a > b) - (a < b)

def turn(p, q, r):
    return cmp((q[0] - p[0])*(r[1] - p[1]) - (r[0] - p[0])*(q[1] - p[1]), 0)

def _keep_left(hull, r):
    while len(hull) > 1 and turn(hull[-2], hull[-1], r) != TURN_LEFT:
            hull.pop()
    if not len(hull) or hull[-1] != r:
        hull.append(r)
    return hull

def convex_hull(points):
    """Returns points on convex hull of an array of points in CCW order."""
    points = sorted(points)
    l = reduce(_keep_left, points, [])
    u = reduce(_keep_left, reversed(points), [])
    return l.extend(u[i] for i in range(1, len(u) - 1)) or l

def aabb_box(points):
    if not points:
        return []
    x_min, y_min = points[0]
    x_max, y_max = points[0]
    for x, y in points:
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x)
        y_max = max(y_max, y)
    if math.isclose(x_min, x_max) or math.isclose(y_min, y_max):
        return []
    return [[x_min, y_min], [x_min, y_max], [x_max, y_max], [x_max, y_min]]

if __name__ == '__main__':
    points = [[0,0],[0,1],[1,0],[1,1],[2,2]]
    polygon = convex_hull(points)
    for x, y in polygon:
        print("{}, {}".format(x, y))
