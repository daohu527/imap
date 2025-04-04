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


import imap.global_var as global_var
import imap.lib.proto_utils as proto_utils
from modules.map.proto import map_pb2

from matplotlib.patches import Polygon


class Map:
    def __init__(self):
        self.map_pb = map_pb2.Map()

    def load(self, map_file_name):
        res = proto_utils.get_pb_from_file(map_file_name, self.map_pb)
        return res is not None

    def save(self, map_output_file):
        proto_utils.write_pb_to_text_file(self.map_pb, map_output_file)

    def draw_roads(self, ax, road_ids):
        pass

    def draw_lanes(self, ax, lane_id):
        for lane in self.map_pb.lane:
            if lane.id.id == lane_id:
                self._draw_lane_central(lane, ax, 'r', 1)
            else:
                self._draw_lane_central(lane, ax, 'g', 0.5)

    def draw_junctions(self, ax, junction_ids):
        for junction in self.map_pb.junction:
            if len(junction_ids) == 0 or junction.id.id in junction_ids:
                self._draw_polygon_boundary(junction.polygon, ax, 'c')
                # self._draw_polygon(junction.polygon, ax, 'c')

    def draw_signals(self, ax):
        for signal in self.map_pb.signal:
            for stop_line in signal.stop_line:
                for curve in stop_line.segment:
                    self._draw_stop_line(curve.line_segment, ax, "tomato")

    def draw_crosswalks(self, ax):
        for crosswalk in self.map_pb.crosswalk:
            # self._draw_polygon_boundary(crosswalk.polygon, ax, "red")
            self._draw_polygon(crosswalk.polygon, ax, 'c')

    def draw_stop_signs(self, ax):
        for stop_sign in self.map_pb.stop_sign:
            for stop_line in stop_sign.stop_line:
                for curve in stop_line.segment:
                    self._draw_stop_line(curve.line_segment, ax, "tomato")

    def draw_yields(self, ax):
        pass
        # for yield_sign in self.map_pb.yield:
        #   for stop_line in yield_sign.stop_line:
        #     for curve in stop_line.segment:
        #       self._draw_stop_line(curve.line_segment, ax, "yellow")

    def draw_clear_areas(self, ax):
        pass

    def draw_overlaps(self, ax):
        pass

    def draw_speed_bumps(self, ax):
        pass

    def draw_parking_spaces(self, ax):
        pass

    def draw_pnc_junctions(self, ax):
        pass

    @staticmethod
    def _draw_lane_boundary(lane, ax, color_val):
        """draw boundary"""
        for curve in lane.left_boundary.curve.segment:
            if curve.HasField('line_segment'):
                px = []
                py = []
                for p in curve.line_segment.point:
                    px.append(float(p.x))
                    py.append(float(p.y))
                ax.plot(px, py, ls='-', c=color_val, alpha=0.5, picker=True)
        for curve in lane.right_boundary.curve.segment:
            if curve.HasField('line_segment'):
                px = []
                py = []
                for p in curve.line_segment.point:
                    px.append(float(p.x))
                    py.append(float(p.y))
                ax.plot(px, py, ls='-', c=color_val, alpha=0.5, picker=True)

    @staticmethod
    def _draw_lane_central(lane, ax, color_val, alpha_val=0.5):
        for curve in lane.central_curve.segment:
            if curve.HasField('line_segment'):
                px = []
                py = []
                for p in curve.line_segment.point:
                    px.append(float(p.x))
                    py.append(float(p.y))
                line2d, = ax.plot(px, py, ls='-', linewidth=5,
                                  c=color_val, alpha=alpha_val, picker=True)

                # add data to global_var
                global_var.set_artist_value(line2d, lane)
                global_var.set_element_vaule(lane.id.id, line2d)

    @staticmethod
    def _draw_polygon_boundary(polygon, ax, color_val):
        px = []
        py = []
        for point in polygon.point:
            px.append(point.x)
            py.append(point.y)

        if px:
            px.append(px[0])
            py.append(py[0])

        ax.plot(px, py, ls='-', linewidth=2,
                c=color_val, alpha=0.5, picker=True)

    @staticmethod
    def _draw_polygon(polygon, ax, color_val):
        pxy = []
        for point in polygon.point:
            pxy.append([point.x, point.y])
        patch = Polygon(pxy, closed=True, edgecolor=color_val)
        ax.add_patch(patch)

    @staticmethod
    def _draw_stop_line(line_segment, ax, color_val):
        px = []
        py = []
        for p in line_segment.point:
            px.append(float(p.x))
            py.append(float(p.y))
        ax.plot(px, py, 'o-', linewidth=1, c=color_val, picker=True)


if __name__ == '__main__':
    pass
