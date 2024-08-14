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


def _init():
    global _artist_map, _element_map
    _artist_map = {}
    _element_map = {}


def set_artist_value(key, value):
    _artist_map[key] = value


def get_artist_value(key):
    return _artist_map.get(key)


def set_element_vaule(key, value):
    _element_map[key] = value


def get_element_value(key):
    return _element_map.get(key)
