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


from ast import parse
from modules.map.proto import map_pb2
from modules.map.proto import map_road_pb2
from modules.map.proto import map_lane_pb2

import math
import xml.etree.ElementTree as ET
# Debug use
import matplotlib.pyplot as plt

from lib.common import Vector3d, Point3d
from lib.odr_spiral import odr_spiral, odr_arc
from lib.transform import Transform

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
    return 0.0

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
  return 0.0


def get_lateral(s, lateral_profile):
  """s-t to x-y roll

  Args:
      s ([type]): [description]
      lateral_profile ([type]): [description]

  Returns:
      [type]: [description]
  """
  assert s >= 0, "start s is less then 0"
  superelevations = lateral_profile.findall('superelevation')
  if superelevations is None:
    return 0.0

  i = len(superelevations) - 1
  while i >= 0:
    superelevation = superelevations[i]
    superelevation_s = float(superelevation.attrib.get('s'))
    if s >= superelevation_s:
      a = float(superelevation.attrib.get('a'))
      b = float(superelevation.attrib.get('b'))
      c = float(superelevation.attrib.get('c'))
      d = float(superelevation.attrib.get('d'))
      ds = s - superelevation_s
      elev = a + b*ds + c*ds*ds + d*ds*ds*ds
      return elev
    i -= 1
  return 0.0


def parse_geometry_line(geometry, elevation_profile, sample_count, delta_s):
  origin_x = float(geometry.attrib.get('x'))
  origin_y = float(geometry.attrib.get('y'))

  hdg = float(geometry.attrib.get('hdg'))
  origin_s = float(geometry.attrib.get('s'))

  tf = Transform(origin_x, origin_y, 0, hdg, 0, 0)

  line = []
  for i in range(sample_count):
    s, t, h = i * delta_s, 0, 0
    x, y, _ = tf.transform(s, t, h)
    # x = origin_x + s * math.cos(hdg)
    # y = origin_y + s * math.sin(hdg)

    # get elevation
    absolute_s = origin_s + s
    z = get_elevation(absolute_s, elevation_profile)

    point3d = Point3d(x, y, z, absolute_s)
    # TODO(zero): we need to add roll(<superelevation>)
    point3d.set_rotate(hdg)
    print(point3d)
    line.append(point3d)
  return line


def parse_geometry_spiral(geometry, elevation_profile, sample_count, delta_s):
  origin_x = float(geometry.attrib.get('x'))
  origin_y = float(geometry.attrib.get('y'))

  hdg = float(geometry.attrib.get('hdg'))
  origin_s = float(geometry.attrib.get('s'))
  length = float(geometry.attrib.get('length'))

  spiral = geometry.find('spiral')
  curvStart = float(spiral.attrib.get('curvStart'))
  curvEnd = float(spiral.attrib.get('curvEnd'))
  # first derivative of curvature
  cdot = (curvEnd - curvStart) / length

  tf = Transform(origin_x, origin_y, 0, hdg, 0, 0)

  spiral_line = []
  for i in range(sample_count):
    local_s = i * delta_s
    s, t, _ = odr_spiral(local_s, cdot)
    x, y, _ = tf.transform(s, t, 0.0)

    # get elevation
    absolute_s = origin_s + local_s
    z = get_elevation(absolute_s, elevation_profile)

    point3d = Point3d(x, y, z, absolute_s)
    # TODO(zero): we need to add roll(<superelevation>)
    point3d.set_rotate(hdg)
    print(point3d)
    spiral_line.append(point3d)
  return spiral_line


def parse_geometry_arc(geometry, elevation_profile, sample_count, delta_s):
  origin_x = float(geometry.attrib.get('x'))
  origin_y = float(geometry.attrib.get('y'))

  hdg = float(geometry.attrib.get('hdg'))
  origin_s = float(geometry.attrib.get('s'))

  arc = geometry.find('arc')
  curvature = float(arc.attrib.get('curvature'))

  tf = Transform(origin_x, origin_y, 0, hdg, 0, 0)

  arc_line = []
  for i in range(sample_count):
    local_s = i * delta_s
    s, t = odr_arc(local_s, curvature)
    x, y, _ = tf.transform(s, t, 0.0)

    # get elevation
    absolute_s = origin_s + local_s
    z = get_elevation(absolute_s, elevation_profile)

    point3d = Point3d(x, y, z, absolute_s)
    # TODO(zero): we need to add roll(<superelevation>)
    point3d.set_rotate(hdg)
    print(point3d)
    arc_line.append(point3d)
  return arc_line


def parse_geometry_poly3(geometry, elevation_profile, sample_count, delta_s):
  origin_x = float(geometry.attrib.get('x'))
  origin_y = float(geometry.attrib.get('y'))
  origin = Vector3d(origin_x, origin_y, 0.0)

  heading = float(geometry.attrib.get('hdg'))
  origin_s = float(geometry.attrib.get('s'))
  poly3 = geometry.find('poly3')

  # https://releases.asam.net/OpenDRIVE/1.6.0/ASAM_OpenDRIVE_BS_V1-6-0.html#_coordinate_systems
  a = float(poly3.attrib.get('a'))
  b = float(poly3.attrib.get('b'))
  c = float(poly3.attrib.get('c'))
  d = float(poly3.attrib.get('d'))

  # TODO(zero)
  # if a != 0 and b != 0:
  #   tf_uv2st = arctan(bV/bU)
  # elif a == 0 and b == 0:

  for i in range(sample_count):
    u = i * delta_s
    cur_s = origin_s + u
    # roll(rad)
    roll = get_lateral(cur_s, lateral_profile)

    h = get_elevation(cur_s, elevation_profile)
    pos = Vector3d(cur_s, 0.0, h)
    v = a + b*u + c*u*u + d*u*u*u
    pos = Vector3d(u, v, h)



def parse_geometry_param_poly3(geometry, elevation_profile, sample_count, \
    delta_s):
  origin_x = float(geometry.attrib.get('x'))
  origin_y = float(geometry.attrib.get('y'))
  origin = Vector3d(origin_x, origin_y, 0.0)

  heading = float(geometry.attrib.get('hdg'))
  origin_s = float(geometry.attrib.get('s'))
  param_poly3 = geometry.find('paramPoly3')

  # https://releases.asam.net/OpenDRIVE/1.6.0/ASAM_OpenDRIVE_BS_V1-6-0.html#_coordinate_systems
  aU = float(param_poly3.attrib.get('aU'))
  bU = float(param_poly3.attrib.get('bU'))
  cU = float(param_poly3.attrib.get('cU'))
  dU = float(param_poly3.attrib.get('dU'))
  aV = float(param_poly3.attrib.get('aV'))
  bV = float(param_poly3.attrib.get('bV'))
  cV = float(param_poly3.attrib.get('cV'))
  dV = float(param_poly3.attrib.get('dV'))


  p_range = param_poly3.attrib.get('pRange')
  if p_range == 'arcLength':
    pass # [0, @length from <geometry>]
  elif p_range == 'normalized':
    pass # [0, 1]
  else:
    print("Unknown pRange type")

  for i in range(sample_count):
    p = i * delta_s
    cur_s = origin_s + p
    # roll(rad)
    roll = get_lateral(cur_s, lateral_profile)

    h = get_elevation(cur_s, elevation_profile)

    u = aU + bU*p + cU*p*p + dU*p*p*p
    v = aV + bV*p + cV*p*p + dV*p*p*p
    pos = Vector3d(u, v, h)

# test
reference_line = []

def draw_reference_line(reference_line):
  x = [point.x for point in reference_line]
  y = [point.y for point in reference_line]
  plt.plot(x, y)
  plt.show()


def parse_reference_line(plan_view, elevation_profile, lateral_profile):
  for geometry in plan_view.iter('geometry'):
    geometry_length = float(geometry.attrib.get('length'))
    if geometry_length < GEOMETRY_SKIP_LENGTH:
      continue

    delta_s = min(geometry_length, SAMPLING_LENGTH)
    sample_count = math.ceil(geometry_length/delta_s)

    # reference_line = []
    if geometry[0].tag == 'line':
      line = parse_geometry_line(geometry, elevation_profile, sample_count, delta_s)
      reference_line.extend(line)
    elif geometry[0].tag == 'spiral':
      spiral_line = parse_geometry_spiral(geometry, elevation_profile, sample_count, delta_s)
      reference_line.extend(spiral_line)
    elif geometry[0].tag == 'arc':
      arc_line = parse_geometry_arc(geometry, elevation_profile, sample_count, delta_s)
      reference_line.extend(arc_line)
    elif geometry[0].tag == 'poly3':  # deprecated in OpenDrive 1.6.0
      poly3_line = parse_geometry_poly3(geometry, elevation_profile, sample_count, delta_s)
      reference_line.extend(poly3_line)
    elif geometry[0].tag == 'paramPoly3':
      paramPoly3_line = parse_geometry_param_poly3(geometry, elevation_profile, sample_count,\
          delta_s)
      reference_line.extend(paramPoly3_line)
    else:
      print("geometry type not support")


def reference_line_add_offset(lanes):
  for lane_offset in lanes.iter('laneOffset'):
    s = float(lane_offset.attrib.get('s'))
    a = float(lane_offset.attrib.get('a'))
    b = float(lane_offset.attrib.get('b'))
    c = float(lane_offset.attrib.get('c'))
    d = float(lane_offset.attrib.get('d'))

    # TODO(zero) : how to calc the length
    length = 0
    delta_s = min(length, SAMPLING_LENGTH)
    for i in range(length):
      ds = i * delta_s
      offset = a + b*ds + c*ds**2 + d*ds**3

      absolute_s = s + ds
      # TODO(zero): Convert coordinates


def parse_lane_link(lane):
  link = lane.find("link")
  if link is not None:
    link.find("predecessor")
    link.find("successor")


def parse_lane_width(lane) -> bool:
  width = lane.find("width")
  if width is None:
    return False

  sOffset = float(width.attrib.get("sOffset"))
  a = float(width.attrib.get("a"))
  b = float(width.attrib.get("b"))
  c = float(width.attrib.get("c"))
  d = float(width.attrib.get("d"))
  # a + b*ds + c*ds**2 + d*ds**3
  return True


def parse_road_mark(lane):
  road_mark = lane.find("roadMark")
  if road_mark is not None:
    sOffset = float(road_mark.attrib.get("sOffset"))
    lane_type = road_mark.attrib.get("type")
    weight = road_mark.attrib.get("weight")
    color = road_mark.attrib.get("color")
    width = float(road_mark.attrib.get("width"))


def parse_lanes(lanes_in_section):
  if lanes_in_section is None:
    return

  for lane in lanes_in_section.iter('lane'):
    id = lane.attrib.get('id')
    lane_type = lane.attrib.get('type')
    level = lane.attrib.get('level')
    print("lane id: {}, type: {}".format(id, lane_type))

    parse_lane_link(lane)

    success = parse_lane_width(lane)

    # If both width and lane border elements are present for a lane section in
    # the OpenDRIVE file, the application must use the information from the
    # <width> elements.
    if not success:
      parse_road_mark(lane)


def parse_lane_sections(lanes):
  for lane_section in lanes.iter('laneSection'):
    s = float(lane_section.attrib.get('s'))
    single_side = bool(lane_section.attrib.get('singleSide'))
    left = lane_section.find("left")
    right = lane_section.find("right")
    # Todo(zero): Check if 'left' or 'right' is None
    parse_lanes(left)
    parse_lanes(right)


def parse_road(pb_map, road):
  pb_road = pb_map.road.add()
  road_length = road.attrib.get('length')
  pb_road.id.id = road.attrib.get('id')
  pb_road.junction_id.id = road.attrib.get('junction')
  if pb_road.junction_id.id != "-1":
    # Todo(zero): need complete
    pass

  # The definition of road type is inconsistent
  # https://releases.asam.net/OpenDRIVE/1.6.0/ASAM_OpenDRIVE_BS_V1-6-0.html#_road_type
  if road.attrib.get('type') is None:
    pb_road.type = map_road_pb2.Road.CITY_ROAD  # default

  # child node "type"
  road_speed_limit = parse_road_speed(road)

  # Elevation in reference line
  elevation_profile = road.find('elevationProfile')
  # Superelevation causes a roll in the reference line
  lateral_profile = road.find('lateralProfile')

  # reference line
  lanes = road.find('lanes')
  assert lanes is not None, "Road {} has no lanes!".format(pb_road.id.id)

  plan_view = road.find('planView')
  assert plan_view is not None, \
      "Road {} has no reference line!".format(pb_road.id.id)

  parse_reference_line(plan_view, elevation_profile, lateral_profile)

  # TODO(zero): lane0 add offset, not reference line
  reference_line_add_offset(lanes)

  parse_lane_sections(lanes)


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

  # test
  draw_reference_line(reference_line)
