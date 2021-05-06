#!/usr/bin/env python

import argparse
import matplotlib.pyplot as plt

import editor
import global_var
from map import Map

def draw(hdmap):
    lane_ids = []
    junction_ids = []
    hdmap.draw_lanes(ax, lane_ids)
    hdmap.draw_junctions(ax, junction_ids)
    hdmap.draw_crosswalks(ax)
    hdmap.draw_stop_signs(ax)
    hdmap.draw_yields(ax)

def show_map():
    hdmap=Map()
    hdmap.load(args.map)
    draw(hdmap)
    # max windows
    manager=plt.get_current_fig_manager()
    manager.window.showMaximized()
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mapshow is a tool to display hdmap info on a map.",
        prog="mapshow.py")
    
    parser.add_argument(
        "-m", "--map", action="store", type=str, required=True,
        help="Specify the map file in txt or binary format")    

    args = parser.parse_args()

    # Init global var
    global_var._init()

    fig, ax = plt.subplots()

    # 1. add select
    add_editor()

    # 2. show map
    show_map()
