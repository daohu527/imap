#!/usr/bin/env python

import argparse
import matplotlib.pyplot as plt

from map import Map
from editor import Editor

def draw(hdmap):
    lane_ids = []
    junction_ids = []
    hdmap.draw_lanes(ax, lane_ids)
    hdmap.draw_junctions(ax, junction_ids)
    hdmap.draw_crosswalks(ax)
    hdmap.draw_stop_signs(ax)
    hdmap.draw_yields(ax)

def show_map():
    hdmap = Map()
    hdmap.load(args.map)
    draw(hdmap)
    plt.axis('equal')
    plt.show()

def save_map():
    pass

def load_base_map():
    pass

def add_editor():
    editor = Editor()
    fig.canvas.mpl_connect('button_press_event', editor.on_click)
    fig.canvas.mpl_connect('button_press_event', editor.on_press)
    fig.canvas.mpl_connect('button_release_event', editor.on_release)
    fig.canvas.mpl_connect('pick_event', editor.on_pick)
    fig.canvas.mpl_connect('motion_notify_event', editor.on_motion)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mapshow is a tool to display hdmap info on a map.",
        prog="mapshow.py")
    
    parser.add_argument(
        "-m", "--map", action="store", type=str, required=True,
        help="Specify the map file in txt or binary format")    

    args = parser.parse_args()

    fig, ax = plt.subplots()
    show_map()
    add_editor()
