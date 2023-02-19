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


import imap.editor as editor
import matplotlib.pyplot as plt

from imap.map import Map

fig, ax = plt.subplots(figsize=(20, 20))
# plt.gca().set_aspect('equal', adjustable='box')


def draw(hdmap, lane_id):
    lane_ids = []
    junction_ids = []
    hdmap.draw_lanes(ax, lane_id)
    hdmap.draw_junctions(ax, junction_ids)
    hdmap.draw_signals(ax)
    hdmap.draw_crosswalks(ax)
    hdmap.draw_stop_signs(ax)
    hdmap.draw_yields(ax)

def show_map(map_path, lane_id):
    hdmap=Map()
    hdmap.load(map_path)
    draw(hdmap, lane_id)
    # max windows
    # manager=plt.get_current_fig_manager()
    # manager.window.showMaximized()
    # tight layout
    # todo(zero): why tight layout not work?
    plt.tight_layout()
    plt.axis('equal')
    plt.show()

def add_editor():
  fig.canvas.mpl_connect('button_press_event', editor.on_click)
  fig.canvas.mpl_connect('button_press_event', editor.on_press)
  fig.canvas.mpl_connect('button_release_event', editor.on_release)
  fig.canvas.mpl_connect('pick_event', editor.on_pick)
  fig.canvas.mpl_connect('motion_notify_event', editor.on_motion)


def draw_line(line, color=None, reference_line=False, label=""):
  x = [point.x for point in line]
  y = [point.y for point in line]

  if reference_line:
    ax.plot(x, y, linestyle="dashed", linewidth=10, alpha=0.5, label=label)
  else:
    if color:
      ax.plot(x, y, color, label = label)
    else:
      ax.plot(x, y, label = label)


def show(need_save=False, path=None):
  # show map
  ax.legend()
  ax.axis('equal')
  if need_save:
    plt.savefig(path)
    print(path, "saved")
  plt.show()
