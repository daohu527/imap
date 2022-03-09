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

from lib.proto_utils import write_pb_to_text_file
from lib.common import Vector3d, Point3d, shift_t
from lib.odr_spiral import odr_spiral, odr_arc
from lib.transform import Transform
from lib.draw import draw_line, show

from lib.opendrive.junction import Junction, Connection

GEOMETRY_SKIP_LENGTH = 0.01
SAMPLING_LENGTH = 1.0

# global parameters
junctions_objs = {}


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
  road_type = road.findall('type')
  if not road_type:
    return 0

  speed = road_type[0].find('speed')
  speed_max = speed.attrib.get('max')
  if speed_max == 'no limit' or speed_max == 'undefined':
    return 0

  speed_unit = speed.attrib.get('unit')
  return convert_speed(speed_unit, speed_max)

def convert_speed(speed_unit, speed_limit) -> float:
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
  """get height of lane

  Args:
      s ([type]): [description]
      elevation_profile ([type]): [description]

  Returns:
      [type]: [description]
  """
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
    s, t, theta = odr_spiral(local_s, cdot)
    x, y, _ = tf.transform(s, t, 0.0)

    # get elevation
    absolute_s = origin_s + local_s
    z = get_elevation(absolute_s, elevation_profile)

    point3d = Point3d(x, y, z, absolute_s)
    # TODO(zero): we need to add roll(<superelevation>)
    point3d.set_rotate(hdg + theta)
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
    s, t, theta = odr_arc(local_s, curvature)
    x, y, _ = tf.transform(s, t, 0.0)

    # get elevation
    absolute_s = origin_s + local_s
    z = get_elevation(absolute_s, elevation_profile)

    point3d = Point3d(x, y, z, absolute_s)
    # TODO(zero): we need to add roll(<superelevation>)
    point3d.set_rotate(hdg + theta)
    arc_line.append(point3d)
  return arc_line


def parse_geometry_poly3(geometry, elevation_profile, sample_count, delta_s):
  origin_x = float(geometry.attrib.get('x'))
  origin_y = float(geometry.attrib.get('y'))

  hdg = float(geometry.attrib.get('hdg'))
  origin_s = float(geometry.attrib.get('s'))
  poly3 = geometry.find('poly3')

  # https://releases.asam.net/OpenDRIVE/1.6.0/ASAM_OpenDRIVE_BS_V1-6-0.html#_coordinate_systems
  a = float(poly3.attrib.get('a'))
  b = float(poly3.attrib.get('b'))
  c = float(poly3.attrib.get('c'))
  d = float(poly3.attrib.get('d'))

  # TODO(zero)
  # 1. How to get u, v based on length?
  # 2. arctan(bV/bU), au,zv

  for i in range(sample_count):
    u = i * delta_s
    v = a + b*u + c*u**2 + d*u**3

    absolute_s = origin_s + u
    # roll(rad)
    roll = get_lateral(absolute_s, lateral_profile)

    z = get_elevation(absolute_s, elevation_profile)


def parse_geometry_param_poly3(geometry, elevation_profile, delta_s):
  origin_x = float(geometry.attrib.get('x'))
  origin_y = float(geometry.attrib.get('y'))

  hdg = float(geometry.attrib.get('hdg'))
  length = float(geometry.attrib.get('length'))
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
    # [0, @length from <geometry>]
    sample_count = math.ceil(length/delta_s)
  elif p_range == 'normalized':
    # [0, 1]
    sample_count = 1
  else:
    print("Unknown pRange type")

  # TODO(zero):
  # 1. How to get P based on length?
  # 2. arctan(bV/bU), (aU, aV)
  for i in range(sample_count):
    p = i * delta_s

    u = aU + bU*p + cU*p**2 + dU*p**3
    v = aV + bV*p + cV*p**2 + dV*p**3


def parse_reference_line(plan_view, elevation_profile, lateral_profile):
  reference_line = []

  for geometry in plan_view.iter('geometry'):
    geometry_length = float(geometry.attrib.get('length'))
    if geometry_length < GEOMETRY_SKIP_LENGTH:
      continue

    delta_s = min(geometry_length, SAMPLING_LENGTH)
    sample_count = math.ceil(geometry_length/delta_s) + 1

    if geometry[0].tag == 'line':
      line = parse_geometry_line(geometry, elevation_profile, sample_count, delta_s)
    elif geometry[0].tag == 'spiral':
      line = parse_geometry_spiral(geometry, elevation_profile, sample_count, delta_s)
    elif geometry[0].tag == 'arc':
      line = parse_geometry_arc(geometry, elevation_profile, sample_count, delta_s)
    elif geometry[0].tag == 'poly3':  # deprecated in OpenDrive 1.6.0
      line = parse_geometry_poly3(geometry, elevation_profile, delta_s)
    elif geometry[0].tag == 'paramPoly3':
      line = parse_geometry_param_poly3(geometry, elevation_profile, delta_s)
    else:
      print("geometry type not support")

    reference_line.extend(line)

  return reference_line


def reference_line_add_offset(lanes, road_length, reference_line):
  """Adjust reference line by offset

  Args:
      lanes (_type_): _description_
      road_length (_type_): _description_
      reference_line (_type_): _description_
  """
  lane_offset_list = []
  for lane_offset in lanes.iter('laneOffset'):
    s = float(lane_offset.attrib.get('s'))
    a = float(lane_offset.attrib.get('a'))
    b = float(lane_offset.attrib.get('b'))
    c = float(lane_offset.attrib.get('c'))
    d = float(lane_offset.attrib.get('d'))
    lane_offset_list.append((s, a, b, c, d))

  if not lane_offset_list:
    return

  # Add offset to reference line
  i, n = 0, len(lane_offset_list)
  cur_s = lane_offset_list[i][0]
  next_s = lane_offset_list[i+1][0] if i+1 < n else road_length
  for idx in range(len(reference_line)):
    if reference_line[idx].s < cur_s:
      continue

    if reference_line[idx].s > next_s:
      i += 1
      # if i >= n:
      #   break
      i = min(n-1, i)
      cur_s = lane_offset_list[i][0]
      next_s = lane_offset_list[i+1][0] if i+1 < n else road_length

    ds = reference_line[idx].s - cur_s

    a = lane_offset_list[i][1]
    b = lane_offset_list[i][2]
    c = lane_offset_list[i][3]
    d = lane_offset_list[i][4]
    offset = a + b*ds + c*ds**2 + d*ds**3

    # if offset:
    #   print(reference_line[idx])
    reference_line[idx].shift_t(offset)
    # if offset:
    #   print(reference_line[idx])


def parse_lane_widths(widths, sec_cur_s, sec_next_s, direction, reference_line):
  width_list = []
  for width in widths:
    sOffset = float(width.attrib.get("sOffset"))
    a = float(width.attrib.get("a"))
    b = float(width.attrib.get("b"))
    c = float(width.attrib.get("c"))
    d = float(width.attrib.get("d"))
    width_list.append((sOffset, a, b, c, d))

  # cacl width
  boundary_line, center_line = [], []
  i, n = 0, len(width_list)
  cur_s = sec_cur_s + width_list[i][0]
  next_s = width_list[i+1][0] if i+1 < n else sec_next_s
  for idx in range(len(reference_line)):
    if reference_line[idx].s < cur_s:
      continue

    if reference_line[idx].s > next_s:
      i += 1
      # Todo(zero): Adding will cause inexplicable line segments, and they are very long
      if i >= n:
        break
      # i = min(n-1, i)
      cur_s = width_list[i][0]
      next_s = width_list[i+1][0] if i+1 < n else sec_next_s

    ds = reference_line[idx].s - cur_s
    a = width_list[i][1]
    b = width_list[i][2]
    c = width_list[i][3]
    d = width_list[i][4]
    width = a + b*ds + c*ds**2 + d*ds**3

    direct = -1 if direction == "left" else 1

    point3d = shift_t(reference_line[idx], width * direct)
    boundary_line.append(point3d)

    point3d = shift_t(reference_line[idx], width * direct / 2)
    center_line.append(point3d)

  return boundary_line, center_line


def parse_lane_border(pb_lane, border):
  pass


def is_adjacent(road_mark) -> bool:
  if road_mark is None:
    return True
  road_mark_type = road_mark.attrib.get("type")
  if road_mark_type == "botts dots" or \
     road_mark_type == "broken broken" or \
     road_mark_type == "broken solid" or \
     road_mark_type == "broken" or \
     road_mark_type == "none":
    return True
  return False

def parse_road_marks(road_marks):
  road_mark_list = []
  # t_road_lanes_laneSection_lcr_lane_roadMark
  for road_mark in road_marks:
    sOffset = float(road_mark.attrib.get("sOffset"))

    road_mark_type = road_mark.attrib.get("type")
    if road_mark_type == "botts dots":
      pass
    elif road_mark_type == "broken broken":
      pass
    elif road_mark_type == "broken solid":
      pass
    elif road_mark_type == "broken":
      pass
    elif road_mark_type == "curb":
      pass
    elif road_mark_type == "custom":
      pass
    elif road_mark_type == "edge":
      pass
    elif road_mark_type == "grass":
      pass
    elif road_mark_type == "none":
      pass
    elif road_mark_type == "solid broken":
      pass
    elif road_mark_type == "solid solid":
      pass
    elif road_mark_type == "solid":
      pass

    # TODO(zero): Not used for now
    # weight = road_mark.attrib.get("weight")
    # color = road_mark.attrib.get("color")
    # width = float(road_mark.attrib.get("width"))

    lane_change = road_mark.attrib.get("lane_change")
    if lane_change == "both":
      pass
    elif lane_change == "decrease":
      pass
    elif lane_change == "increase":
      pass
    elif lane_change == "none":
      pass

    road_mark_list.append((sOffset, road_mark_type, lane_change))


def parse_lane_speed(lane) -> float:
  # TODO(zero): according to the spec, there're multi speed limit, but we just deal with one.
  # If there are multiple lane speed limit elements per lane section,
  # the elements shall be defined in ascending order.
  speed = lane.find("speed")
  if not speed:
    return 0.0

  speed_max = speed.attrib.get('max')
  speed_unit = speed.attrib.get('unit')
  return convert_speed(speed_unit, speed_max)


def parse_lane_link(pb_lane, road_id, section_id, lane):
  link = lane.find("link")
  if not link:
    return

  predecessors = link.findall("predecessor")
  if predecessors:
    for predecessor in predecessors:
      # normal
      predecessor_id = predecessor.attrib.get("id")
      if predecessor_id:
        # TODO(zero): deal with begin and end
        pb_lane.predecessor_id.add().id = "road_{}_lane_{}_{}".format(road_id, section_id - 1, predecessor_id)
      # junction
      element_type = predecessor.attrib.get("elementType")
      if element_type:
        element_id = predecessor.attrib.get("elementId")
        # TODO(zero): todo


  successors = link.findall("successor")
  if successors:
    for successor in successors:
      successor_id = successor.attrib.get("id")
      if successor_id:
        pb_lane.successor_id.add().id = "road_{}_lane_{}_{}".format(road_id, section_id + 1, successor_id)
      # junction
      element_type = successor.attrib.get("elementType")
      if element_type:
        element_id = successor.attrib.get("elementId")
        # TODO(zero): todo


def add_lane_boundary(pb_lane, left_boundary_line, center_line, right_boundary_line):
  if not left_boundary_line or not right_boundary_line or not center_line:
    print("lane boundary length is zero")
    return

  # 1. left boundary
  segment = pb_lane.left_boundary.curve.segment.add()
  for point3d in left_boundary_line:
    point = segment.line_segment.point.add()
    point.x, point.y = point3d.x, point3d.y
  segment.s = 0
  segment.start_position.x = left_boundary_line[0].x
  segment.start_position.y = left_boundary_line[0].y
  segment.start_position.z = left_boundary_line[0].z
  segment.length = pb_lane.length
  pb_lane.left_boundary.length = pb_lane.length

  # 2. center line
  segment = pb_lane.central_curve.segment.add()
  for point3d in center_line:
    point = segment.line_segment.point.add()
    point.x, point.y = point3d.x, point3d.y
  segment.s = 0
  segment.start_position.x = center_line[0].x
  segment.start_position.y = center_line[0].y
  segment.start_position.z = center_line[0].z
  segment.length = pb_lane.length

  # 3. right boundary
  segment = pb_lane.right_boundary.curve.segment.add()
  for point3d in right_boundary_line:
    point = segment.line_segment.point.add()
    point.x, point.y = point3d.x, point3d.y
  segment.s = 0
  segment.start_position.x = right_boundary_line[0].x
  segment.start_position.y = right_boundary_line[0].y
  segment.start_position.z = right_boundary_line[0].z
  segment.length = pb_lane.length
  pb_lane.right_boundary.length = pb_lane.length


def parse_lanes(pb_map, lanes_in_section, section_id, sec_cur_s, sec_next_s, direction, reference_line):
  assert sec_cur_s < sec_next_s, "lane section length is below zero"

  if not lanes_in_section:
    return

  left_boundary_line = reference_line
  n = len(lanes_in_section)
  pb_lane_section = []
  for idx, lane in enumerate(lanes_in_section):
    pb_lane = pb_map.lane.add()
    pb_lane_section.append(pb_lane)

    road_id = pb_map.road[-1].id.id

    pb_lane.id.id = "road_{}_lane_{}_{}".format(road_id, section_id, lane.attrib.get('id'))
    pb_lane.type = to_pb_lane_type(lane.attrib.get('type'))
    pb_lane.length = sec_next_s - sec_cur_s
    pb_lane.speed_limit = parse_lane_speed(lane)
    pb_lane.direction = map_lane_pb2.Lane.FORWARD

    # add neighbor
    if idx > 0:
      pb_lane.left_neighbor_forward_lane_id.add().id = \
          "road_{}_lane_{}_{}".format(road_id, section_id, lanes_in_section[idx - 1].attrib.get('id'))
    if idx + 1 < n:
      pb_lane.right_neighbor_forward_lane_id.add().id = \
          "road_{}_lane_{}_{}".format(road_id, section_id, lanes_in_section[idx + 1].attrib.get('id'))

    # TODO(zero):
    # "true" = keep lane on level, that is, do not apply superelevation;
    # "false" = apply superelevation to this lane
    # (default, also used if attribute level is missing)
    # level = lane.attrib.get('level')
    print("road id : {}, lane id: {}, type: {}".format( \
        pb_map.road[-1].id.id, pb_lane.id.id, pb_lane.type))

    parse_lane_link(pb_lane, road_id, section_id, lane)

    # If both width and lane border elements are present for a lane section in
    # the OpenDRIVE file, the application must use the information from the
    # <width> elements.
    widths = lane.findall("width")
    if widths:
      right_boundary_line, center_line = parse_lane_widths(widths, sec_cur_s, \
          sec_next_s, direction, left_boundary_line)
    else:
      border = lane.findall("border")
      parse_lane_border(pb_lane, border)

    # Not used for now
    road_marks = lane.findall("roadMark")
    parse_road_marks(road_marks)

    # TODO(zero): debug use
    if lane.attrib.get('type') == "driving":
      draw_line(left_boundary_line, 'g')
      draw_line(right_boundary_line, 'g')
    else:
      draw_line(left_boundary_line)
      draw_line(right_boundary_line)

    # add lane to map
    add_lane_boundary(pb_lane, left_boundary_line, center_line, right_boundary_line)

    left_boundary_line = right_boundary_line
  return pb_lane_section


def post_process_predecessor(predecessor_road, pb_lane_section):
  element_type = predecessor_road.attrib.get('elementType')
  element_id = predecessor_road.attrib.get('elementId')
  if element_type == "road":
    for pb_lane in pb_lane_section:
      for predecessor_id in pb_lane.predecessor_id:
        # TODO(zero): section_id is element_id's
        predecessor_id.id = "road_{}_lane_{}_{}".format(element_id, section_id, successor_id)


def parse_lane_sections(pb_map, predecessor_road, successor_road, lanes, road_length, reference_line):
  # TODO(zero): add road sections
  # pb_road_section = pb_map.road[-1].section.add()

  lane_sections = lanes.findall("laneSection")
  n = len(lane_sections)
  for idx, lane_section in enumerate(lane_sections):
    # TODO(zero): predecessor
    if idx == 0:
      pass

    # parse
    cur_s = float(lane_section.attrib.get('s'))
    single_side = bool(lane_section.attrib.get('singleSide'))

    # lane section length
    next_s = float(lane_sections[idx+1].attrib.get('s')) if (idx+1 < n) else road_length

    left = lane_section.find("left")
    if left:
      direction = "left"
      left_lanes = left.findall('lane')
      left_lanes.reverse()
      pb_lane_section = parse_lanes(pb_map, left_lanes, idx, cur_s, next_s, direction, reference_line)
      first_left_pb_lane = pb_lane_section[0]

    right = lane_section.find("right")
    if right:
      direction = "right"
      right_lanes = right.findall('lane')
      pb_lane_section = parse_lanes(pb_map, right_lanes, idx, cur_s, next_s, direction, reference_line)
      first_right_pb_lane = pb_lane_section[0]

    # add left_neighbor_reverse_lane_id/right_neighbor_reverse_lane_id
    center = lane_section.find("center")
    road_mark = center.find("roadMark")
    if left and right and is_adjacent(road_mark):
      first_left_pb_lane.left_neighbor_reverse_lane_id.add().id = first_right_pb_lane.id.id
      first_right_pb_lane.left_neighbor_reverse_lane_id.add().id = first_left_pb_lane.id.id


def parse_road(pb_map, road):
  pb_road = pb_map.road.add()
  road_length = float(road.attrib.get('length'))
  pb_road.id.id = road.attrib.get('id')
  pb_road.junction_id.id = road.attrib.get('junction')
  if pb_road.junction_id.id != "-1":
    # Todo(zero): need complete
    pass

  road_link = road.find('link')
  if road_link:
    predecessor_road = road_link.findall('predecessor')
    successor_road = road_link.findall('successor')

  # The definition of road type is inconsistent
  # https://releases.asam.net/OpenDRIVE/1.6.0/ASAM_OpenDRIVE_BS_V1-6-0.html#_road_type
  if road.attrib.get('type') is None:
    pb_road.type = map_road_pb2.Road.CITY_ROAD  # default

  # speed
  road_speed_limit = parse_road_speed(road)

  # Elevation in reference line
  elevation_profile = road.find('elevationProfile')
  # Superelevation causes a roll in the reference line
  lateral_profile = road.find('lateralProfile')

  # reference line
  plan_view = road.find('planView')
  assert plan_view is not None, \
      "Road {} has no reference line!".format(pb_road.id.id)

  reference_line = parse_reference_line(plan_view, elevation_profile, lateral_profile)

  # TODO(zero): Need to confirm that there is only one lanes element! If not
  # we should use findall
  lanes = road.find('lanes')
  assert lanes is not None, "Road {} has no lanes!".format(pb_road.id.id)

  reference_line_add_offset(lanes, road_length, reference_line)

  draw_line(reference_line, 'r')

  parse_lane_sections(pb_map, predecessor_road, successor_road, lanes, road_length, reference_line)


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


def parse_junction(pb_map, junction):
  junction_id = junction.attrib.get('id')
  name = junction.attrib.get('name')
  junction_type = junction.attrib.get('type')

  junction_obj = Junction(junction_id, name, junction_type)

  pb_junction = pb_map.junction.add()
  pb_junction.id.id = junction_id
  # TODO(zero): pb_junction polygon
  # pb_junction.polygon.point.add()

  for connection in junction.iter('connection'):
    connection_id = connection.attrib.get('id')
    connection_type = connection.attrib.get('type')
    incoming_road = connection.attrib.get('incomingRoad')
    connecting_road = connection.attrib.get('connectingRoad')
    contact_point = connection.attrib.get('contactPoint')

    connection_obj = Connection(connection_id, connection_type, incoming_road, connecting_road, contact_point)

    junction_obj.add_connection(connection_obj)
  return junction_obj


def parse_object(pb_map, obj):
  # parse_crosswalk()
  # parse_stop_sign()
  # parse_overlap()
  # parse_parking_space()
  pass


def parse_crosswalk(pb_map):
  pass

def parse_stop_sign(pb_map):
  pass

def parse_yield_sign(pb_map):
  pass

def parse_parking_space(pb_map):
  pass

def parse_overlap(pb_map):
  pass


def parse_signal(pb_map, signal):
  signal.attrib.get('s')
  signal.attrib.get('t')
  signal.attrib.get('id')
  signal.attrib.get('name')
  signal.attrib.get('dynamic')
  signal.attrib.get('orientation')
  signal.attrib.get('zOffset')
  signal.attrib.get('value')
  signal.attrib.get('unit')
  signal.attrib.get('height')
  signal.attrib.get('width')
  signal.attrib.get('text')
  signal.attrib.get('hOffset')
  signal.attrib.get('pitch')
  signal.attrib.get('roll')

  # inertial coordinate
  position_inertial = signal.find('positionInertial')
  pb_map.signal.id.id = signal.attrib.get('id')
  # pb_map.signal.boundary
  # pb_map.signal.subsignal.add()
  # pb_map.signal.overlap_id
  # pb_map.signal.type
  # pb_map.signal.stop_line.add()


  # s-t coordinate
  position_road = signal.find('positionRoad')


def get_map_from_xml_file(filename):
  pb_map = map_pb2.Map()
  tree = ET.parse(filename)
  root = tree.getroot()
  assert root is not None, "Map XML failed!"
  assert root.tag == 'OpenDRIVE'

  # 1. header
  header = root.find('header')
  assert header is not None, "Open drive map missing header"
  parse_header(pb_map, header)

  # 2. junctions
  junctions = root.findall('junction')
  if not junctions:
    for junction in junctions:
      junctions_obj = parse_junction(pb_map, junction)
      junctions_objs[junctions_obj.junction_id] = junctions_obj

  # 3. road
  roads = root.findall('road')
  for _, road in enumerate(roads):
    parse_road(pb_map, road)
    # TODO(zero): add successor_id and predecessor_id

  # 4. signals
  signals = root.findall('signals')
  if not signals:
    for signal in signals:
      parse_signal(pb_map, signal)

  # 5. objects
  objects = root.findall('objects')
  if not objects:
    for obj in objects:
      parse_object(pb_map, obj)

  show()

  return pb_map

def save_map_to_xml_file(pb_map, file_path):
  write_pb_to_text_file(pb_map, file_path)
