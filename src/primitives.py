from graph import *
from visualization import *

class Point(list):
    def __init__(self, *args, **kw):
        vals = [0, 0]
        vals[0] = kw.get('x', 0)
        vals[1] = kw.get('y', 0)
        if len(args) > 0:
            vals[0] = args[0]
        if len(args) > 1:
            vals[1] = args[1]
        super(Point, self).__init__(vals)

    def norm(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def get_x(self):
        return self[0]
    def set_x(self, x):
        self[0] = x
    x = property(get_x, set_x)

    def get_y(self):
        return self[1]
    def set_y(self, y):
        self[1] = y
    y = property(get_y, set_y)

class Circle(object):
    def __init__(self, center, radius):
        self._center = Point(*center)
        self.radius = radius

    def intersect(self, other):
        distance = (self.center - other.center).norm()
        if distance > (self.radius + other.radius):
            raise ValueError
        alpha = (self.radius ** 2 - other.radius ** 2 + distance ** 2) / (2.0 * distance)
        beta = math.sqrt(self.radius ** 2 - alpha ** 2)
        delta = other.center - self.center
        _x = self.center.x + (alpha * delta.x) / distance
        _y = self.center.y + (alpha * delta.y) / distance
        #
        _x1 = _x + (beta * delta.y / distance)
        _y1 = _y - (beta * delta.x / distance)
        p1 = Point(_x1, _y1)
        #
        _x2 = _x - (beta * delta.y / distance)
        _y2 = _y + (beta * delta.x / distance)
        p2 = Point(_x2, _y2)
        #
        return (p1, p2)

    def set_center(self, center):
        self._center = center
    def get_center(self):
        return self._center
    center = property(get_center, set_center)

class Edge(object):
    def __init__(self, length=1, name=''):
        self.length = length
        self.name = name

class Pivot(object):
    def __init__(self, position=None, name=''):
        self.name = name
        if position == None:
            position = (0, 0)
        position = Point(*position)
        self.position = position
