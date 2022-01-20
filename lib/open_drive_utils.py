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


from modules.map.proto import map_pb2
from modules.map.proto import map_road_pb2
from modules.map.proto import map_lane_pb2

import math
import xml.etree.ElementTree as ET

from lib.common import Vector3d, Point3d

GEOMETRY_SKIP_LENGTH = 0.01
SAMPLING_LENGTH = 1.0

def save_map_to_xml_file(pb_value, file_path):
  pass

def parse_geo_reference(header):
  geo_reference = header.find('geoReference')
  if geo_reference is not None:
    # TODO(zero): proj
    print(geo_reference.text)

def parse_header(pb_map, header):
  pb_map.header.version = header.attrib.get('version').encode()
  pb_map.header.date = header.attrib.get('date').encode()
  # TODO(zero): need to complete
  proj = parse_geo_reference(header)
  if proj is not None:
    pb_map.header.projection.proj = proj
  else:
    zone_id = 0
    pb_map.header.projection.proj = "+proj=utm +zone={} +ellps=WGS84 " \
        "+datum=WGS84 +units=m +no_defs".format(zone_id)

  parse_geo_reference(header)

  # TODO(zero): Inconsistent definitions
  # if header.attrib.get('name'):
  #   pb_map.header.district = header.attrib.get('name').encode()
  if header.attrib.get('revMajor'):
    pb_map.header.rev_major = header.attrib.get('revMajor').encode()
  if header.attrib.get('revMinor'):
    pb_map.header.rev_minor = header.attrib.get('revMinor').encode()
  pb_map.header.left = float(header.attrib.get('west'))
  pb_map.header.right = float(header.attrib.get('east'))
  pb_map.header.top = float(header.attrib.get('north'))
  pb_map.header.bottom = float(header.attrib.get('south'))
  if header.attrib.get('vendor'):
    pb_map.header.vendor = header.attrib.get('vendor').encode()


def parse_road_speed(road):
  road_type = road.find('type')
  if road_type is None:
    return
  speed = road_type[0].find('speed')
  speed_max = speed.attrib.get('t_maxSpeed')
  if speed_max == 'no limit' or speed_max == 'undefined':
    return 0

  speed_unit = speed.attrib.get('e_unitSpeed')
  return convert_speed(speed_unit, speed_max)

def convert_speed(speed_unit, speed_limit):
  if speed_unit == 'm/s':
    return float(speed_limit)
  elif speed_unit == 'km/h':
    return float(speed_limit) * 0.277778
  elif speed_unit == 'mph':
    return float(speed_limit) * 0.44704
  else:
    print("Not support speed unit: {}".format(speed_unit))
    return float(speed_limit)

def get_elevation(s, elevation_profile):
  assert s >= 0, "start s is less then 0"

  elevations = elevation_profile.findall('elevation')
  if elevations is None:
    return 0

  i = len(elevations) - 1
  while i >= 0:
    elevation = elevations[i]
    elevation_s = float(elevation.attrib.get('s'))
    if s >= elevation_s:
      a = float(elevation.attrib.get('a'))
      b = float(elevation.attrib.get('b'))
      c = float(elevation.attrib.get('c'))
      d = float(elevation.attrib.get('d'))
      ds = s - elevation_s
      elev = a + b*ds + c*ds*ds + d*ds*ds*ds
      return elev
    i -= 1

  return 0

def get_pos(elevation_profile, s, x, z, hdg):
  y = get_elevation(s, elevation_profile)
  pos = Vector3d(x, y, z)
  # pos = euler(0, -(hdg*180/math.pi), 0) * pos
  return pos

def parse_geometry_line(geometry, elevation_profile, sample_count, delta_s):
  geometry_x = float(geometry.attrib.get('x'))
  geometry_y = float(geometry.attrib.get('y'))
  origin = Vector3d(geometry_x, 0.0, geometry_y)

  hdg = float(geometry.attrib.get('hdg'))
  s = float(geometry.attrib.get('s'))
  for i in range(sample_count):
    x = i * delta_s
    cur_s = s + x
    pos = get_pos(elevation_profile, cur_s, x, 0, hdg)
    point3d = Point3d(origin + pos, cur_s, hdg)
    print(point3d)

def parse_geometry_spiral(geometry, elevation_profile, sample_count, delta_s):
  geometry_x = float(geometry.attrib.get('x'))
  geometry_y = float(geometry.attrib.get('y'))
  origin = Vector3d(geometry_x, 0, geometry_y)

  hdg = float(geometry.attrib.get('hdg'))
  s = float(geometry.attrib.get('s'))
  for i in range(sample_count):
    pass

def parse_geometry_arc(geometry, elevation_profile, sample_count, delta_s):
  geometry_x = float(geometry.attrib.get('x'))
  geometry_y = float(geometry.attrib.get('y'))
  origin = Vector3d(geometry_x, 0, geometry_y)

  hdg = float(geometry.attrib.get('hdg'))
  s = float(geometry.attrib.get('s'))
  for i in range(sample_count):
    pass

def parse_geometry_poly3(geometry, elevation_profile, sample_count, delta_s):
  geometry_x = float(geometry.attrib.get('x'))
  geometry_y = float(geometry.attrib.get('y'))
  origin = Vector3d(geometry_x, 0, geometry_y)

  hdg = float(geometry.attrib.get('hdg'))
  s = float(geometry.attrib.get('s'))
  for i in range(sample_count):
    pass

def parse_geometry_param_poly3(geometry, elevation_profile, sample_count, \
    delta_s):
  geometry_x = float(geometry.attrib.get('x'))
  geometry_y = float(geometry.attrib.get('y'))
  origin = Vector3d(geometry_x, 0, geometry_y)

  hdg = float(geometry.attrib.get('hdg'))
  s = float(geometry.attrib.get('s'))
  for i in range(sample_count):
    pass

def parse_reference_line(plan_view, elevation_profile):
  for geometry in plan_view.iter('geometry'):
    geometry_length = float(geometry.attrib.get('length'))
    if geometry_length < GEOMETRY_SKIP_LENGTH:
      continue

    delta_s = min(geometry_length, SAMPLING_LENGTH)
    sample_count = math.floor(geometry_length/delta_s)

    if geometry[0].tag == 'line':
      parse_geometry_line(geometry, elevation_profile, sample_count, delta_s)
    elif geometry[0].tag == 'spiral':
      parse_geometry_spiral(geometry, elevation_profile, sample_count, delta_s)
    elif geometry[0].tag == 'arc':
      parse_geometry_arc(geometry, elevation_profile, sample_count, delta_s)
    elif geometry[0].tag == 'poly3':  # deprecated in OpenDrive 1.6.0
      parse_geometry_poly3(geometry, elevation_profile, sample_count, delta_s)
    elif geometry[0].tag == 'paramPoly3':
      parse_geometry_param_poly3(geometry, elevation_profile, sample_count,\
          delta_s)
    else:
      print("geometry type not support")

def parse_road(pb_map, road):
  pb_road = pb_map.road.add()
  road_length = road.attrib.get('length')
  pb_road.id.id = road.attrib.get('id')
  pb_road.junction_id.id = road.attrib.get('junction')
  if pb_road.junction_id.id != "-1":
    pass

  # The definition of road type is inconsistent
  # https://releases.asam.net/OpenDRIVE/1.6.0/ASAM_OpenDRIVE_BS_V1-6-0.html#_road_type
  if road.attrib.get('type') is None:
    pb_road.type = map_road_pb2.Road.CITY_ROAD  # default

  # child node "type"
  road_speed_limit = parse_road_speed(road)

  # child node "elevationProfile"
  elevation_profile = road.find('elevationProfile')

  # reference line
  lanes = road.find('lanes')
  assert lanes is not None, "Road {} has no lanes!".format(pb_road.id.id)

  plan_view = road.find('planView')
  assert plan_view is not None, \
      "Road {} has no reference line!".format(pb_road.id.id)

  parse_reference_line(plan_view, elevation_profile)


def parse_lane(pb_map, lanes):
  for lane_section in lanes.iter('laneSection'):
    left = lane_section.find('left')
    center = lane_section.find('center')
    right = lane_section.find('right')

def to_pb_lane_type(open_drive_type):
  lower_type = open_drive_type.lower()
  if lower_type == 'none':
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'driving':
    return map_lane_pb2.Lane.CITY_DRIVING
  elif lower_type == 'biking':
    return map_lane_pb2.Lane.BIKING
  elif lower_type == 'sidewalk':
    return map_lane_pb2.Lane.SIDEWALK
  elif lower_type == 'parking':
    return map_lane_pb2.Lane.PARKING
  elif lower_type == 'shoulder':
    return map_lane_pb2.Lane.SHOULDER
  elif lower_type == 'border':     # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'stop':       # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'restricted': # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'median':     # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'curb':       # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'exit':       # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'entry':      # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'onramp':     # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'offRamp':    # not support
    return map_lane_pb2.Lane.NONE
  elif lower_type == 'connectingRamp': # not support
    return map_lane_pb2.Lane.NONE

def parse_lane_section_left(pb_lane, left):
  for lane in left.iter('lane'):
    pb_lane.id.id = lane.attrib.get('id')
    pb_lane.type = to_pb_lane_type(lane.attrib.get('type'))


def parse_junction(pb_map):
  pass

def parse_crosswalk(pb_map):
  pass

def parse_signal(pb_map, road):
  pass

def parse_stop_sign(pb_map):
  pass

def parse_yield_sign(pb_map):
  pass


def get_map_from_xml_file(filename, pb_map):
  tree = ET.parse(filename)
  root = tree.getroot()
  assert root is not None, "Map XML failed!"
  assert root.tag == 'OpenDRIVE'

  # header
  header = root.find('header')
  assert header is not None, "Open drive map missing header"
  parse_header(pb_map, header)

  # road
  for road in root.iter('road'):
    print(road.attrib)
    # 1. road
    parse_road(pb_map, road)
    # 2. signals
    parse_signal(pb_map, road)
    # 3. objects

