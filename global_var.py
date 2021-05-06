#!/usr/bin/env python

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
