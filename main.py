# -*- coding: utf-8 -*-
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


import argparse

import global_var

from lib.draw import add_editor, show_map
from lib.convertor import Opendrive2Apollo


def convert_map_format():
    opendrive2apollo = Opendrive2Apollo(args.input, args.output)
    opendrive2apollo.set_parameters(only_driving=True)
    opendrive2apollo.convert()


def show_open_drive_map():
    pb_map = open_drive_utils.get_map_from_xml_file(args.map)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mapshow is a tool to display hdmap info on a map.",
        prog="mapshow.py")

    parser.add_argument(
        "-m", "--map", action="store", type=str, required=False,
        help="Specify the map file in txt or binary format")

    parser.add_argument(
        "-f", "--format", action="store", type=str, required=False,
        nargs='?', const="0", help="Convert format")
    parser.add_argument(
        "-i", "--input", action="store", type=str, required=False,
        help="map input path")
    parser.add_argument(
        "-o", "--output", action="store", type=str, required=False,
        help="map output path")


    args = parser.parse_args()

    # 1. Init global var
    global_var._init()

    # 2. show map
    if args.map is not None:
        # TODO(zero): fix two windows
        suffix = args.map.split(".")[1]
        if suffix == "bin" or suffix == "txt":
            add_editor()
            show_map(args.map)
        elif suffix == "xodr":
            show_open_drive_map()
        else:
            pass

    # 3. convert opendrive map to apllo
    if args.format is not None:
        convert_map_format()
