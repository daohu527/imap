
class Vector3d:
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z

  def __add__(self, other):
    self.x += other.x
    self.y += other.y
    self.z += other.z
    return self

  def __str__(self):
    return "Vector3d x: {}, y: {}, z: {}".format(self.x, self.y, self.z)

class Point3d:
  def __init__(self, x, y, z, s, heading):
    self.x = x
    self.y = y
    self.z = z
    self.s = s
    self.heading = heading

  def __init__(self, vector3d, s, heading):
    self.x = vector3d.x
    self.y = vector3d.y
    self.z = vector3d.z
    self.s = s
    self.heading = heading

  def __str__(self):
    return "Point3d x: {}, y: {}, z: {}, s: {}, heading: {}".format(self.x, \
        self.y, self.z, self.s, self.heading)