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


def cubic_polynoms(a, b, c, d, u):
    v = a + b*u + c*u**2 + d*u**3
    theta = math.atan(b + 2*c*u + 3*d*u**2)
    return u, v, theta


def parametric_cubic_curve(aU, bU, cU, dU, aV, bV, cV, dV, p):
    u = aU + bU*p + cU*p**2 + dU*p**3
    v = aV + bV*p + cV*p**2 + dV*p**3
    theta = math.atan2(bV + 2*cV*p + 3*dV*p**2, bU + 2*cU*p + 3*dU*p**2)
    return u, v, theta
