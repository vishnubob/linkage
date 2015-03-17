import math
import pyglet
import pymunk
import random
from pymunk.vec2d import Vec2d
from visualization import draw
from scad.gear import *

GEAR_LAYER = 0
LINKAGE_LAYER = 1

def center(pos):
    return (pos[0] / 2.0, pos[1] / 2.0)

def square(size):
    return math.sqrt(size[0] * size[1])

def euclidean_distance(pos1, pos2):
    (x1, y1) = pos1
    (x2, y2) = pos2
    distance = (x2 - x1) ** 2 + (y1 - y2) ** 2
    return math.sqrt(distance)

def rect(body, size, offset=(0, 0), radius=0, segments=False):
    (width, height) = size
    verticies = [(0, 0), (width, 0), (width, height), (0, height)]
    if segments:
        ret = []
        for (idx, vertex_a) in enumerate(verticies):
            vertex_b = verticies[(idx + 1) % len(verticies)]
            seg = pymunk.Segment(body, vertex_a, vertex_b, radius)
            ret.append(seg)
    else:
        ret = pymunk.Poly(body, verticies, offset, radius)
    return ret

class Linkage(object):
    def __init__(self, **kw):
        self.name = kw.get("name", '')
        self.angle = kw.get("angle", 0)
        self.length = kw.get("length", 1)
        self.linked_linkages = {}
        self.linkage_layer = 0
        self.linkage_group = (1 << GEAR_LAYER)
        self.position_a = None
        self.position_b = None
        self.angle = None
        self.pivot_points = {}
        self.embedded = False

    def get_center(self):
        assert self.position_a != None and self.position_b != None
        x = (self.position_a[0] + self.position_b[0]) / 2.0
        y = (self.position_a[1] + self.position_b[1]) / 2.0
        return (x, y)
    center = property(get_center)

    def solve_position_b(self, point):
        dx = point[0] - self.position_a[0]
        dy = point[1] - self.position_a[1]
        self.angle = math.atan2(dy, dx)
        bx = self.length * math.cos(self.angle) + self.position_a[0]
        by = self.length * math.sin(self.angle) + self.position_a[1]
        self.position_b = (bx, by)

    def prepare_embed(self, visited=None):
        if visited == None:
            visited = set()
        for linkage in self.linked_linkages:
            if linkage in visited:
                continue
            self.calculate_position(linkage)

    def embed(self, world, visited=None):
        if self.embedded:
            return
        self.embedded = True
        if visited == None:
            visited = set()
        self.embed_body(world)
        for linkage in self.linked_linkages:
            linkage.embed(world)
            self.embed_pivot(world, linkage)

    def calculate_position(self, linkage):
        (pivot_a, pivot_b) = self.linked_linkages[linkage]
        circle_a = Circle(self.position_a, pivot_a)
        circle_b = Circle(linkage.position_a, pivot_b)
        (p1, p2) = circle_a.intersect(circle_b)
        if p1[1] > p2[1]:
            intersection = p1
        else:
            intersection = p2
        self.pivot_points[linkage] = intersection
        self.solve_position_b(intersection)
        linkage.solve_position_b(intersection)

    def link_linkage(self, pivot_a, linkage_b, pivot_b):
        self.linked_linkages[linkage_b] = (pivot_a, pivot_b)

    def embed_body(self, world):
        self.body = pymunk.Body(1, 1)
        self.body.position = self.center
        self.body.angle = self.angle
        a = (self.length / -2.0, 0)
        b = (self.length / 2.0, 0)
        self.segment = pymunk.Segment(self.body, a, b, 2)
        self.segment.layer = self.linkage_layer
        self.segment.group = self.linkage_group
        world.add(self.body, self.segment)

    def embed_pivot(self, world, linkage):
        print "linking %s to %s." % (self.name, linkage.name)
        print self.pivot_points[linkage]
        joint = pymunk.constraint.PivotJoint(self.body, linkage.body, self.pivot_points[linkage])
        world.add(joint)

class Gear(object):
    def __init__(self, **kw):
        self.name = kw.get("name", '')
        self._gear = BaseGear(**kw)
        self.position = kw.get("position", [0, 0])
        self.linked_gears = {}
        self.linked_linkage = None
        self.gear_layer = 0
        self.gear_group = (1 << GEAR_LAYER)

    def link_gear(self, gear, angle):
        self.linked_gears[gear] = angle

    def link_linkage(self, angle, radius, linkage):
        self.linked_linkage = (angle, radius, linkage)

    def normalize(self, visited=None):
        if visited == None:
            visited = set()
        visited.add(self)
        _linked_gears = {}
        for gear in self.linked_gears:
            if gear in visited:
                continue
            _linked_gears[gear] = self.linked_gears[gear]
            gear.normalize(visited)
        self.linked_gears = _linked_gears

    def set_position(self, position):
        print "setting gear position", self.name, self.linked_linkage
        self.position = position
        for gear in self.linked_gears:
            angle = self.linked_gears[gear]
            radius = self._gear.pitch_radius + gear._gear.pitch_radius
            x = radius * math.cos(angle) + self.position[0]
            y = radius * math.sin(angle) + self.position[1]
            gear.set_position((x, y))
        if self.linked_linkage:
            (angle, radius, linkage) = self.linked_linkage
            x = radius * math.cos(angle) + self.position[0]
            y = radius * math.sin(angle) + self.position[1]
            print "setting position a", linkage.name
            linkage.position_a = (x, y)

    def embed(self, world):
        self.embed_body(world)
        for gear in self.linked_gears:
            gear.embed(world)
            self.embed_gear_joint(world, gear)
        if self.linked_linkage:
            (angle, radius, linkage) = self.linked_linkage
            print "embedding linkage", linkage.name
            linkage.embed(world)
            self.embed_link_joint(world, linkage)

    def embed_body(self, world):
        self.body = pymunk.Body(1, 1)
        self.body.position = self.position
        self.circle = pymunk.Circle(self.body, self._gear.pitch_radius)
        self.circle.layer = self.gear_layer
        self.circle.group = self.gear_group
        self.static_body = pymunk.Body()
        self.static_body.position = self.position
        joint = pymunk.constraint.PivotJoint(self.body, self.static_body, self.position)
        world.add(self.body, self.circle, joint)

    def embed_gear_joint(self, world, other):
        print "linking %s to %s." % (self.name, other.name)
        ratio = other._gear.number_of_teeth / float(self._gear.number_of_teeth)
        ratio = -ratio
        joint = pymunk.constraint.GearJoint(self.body, other.body, 0, ratio)
        world.add(joint)

    def embed_link_joint(self, world, linkage):
        print "linking %s to %s." % (self.name, linkage.name)
        joint = pymunk.constraint.PivotJoint(self.body, linkage.body, linkage.position_a)
        world.add(joint)

class Motor(Gear):
    def embed_body(self, world):
        super(Motor, self).embed_body(world)
        motor_joint = pymunk.constraint.SimpleMotor(self.static_body, self.body, 10)
        world.add([motor_joint])

class WorldBuild(object):
    Grammar = {
        "command": ["add", "constrain"],
        "command_add": ["gear", "linkage"],
        "command_constrain": ["gear", "linkage"],
        "command_constrain_gear": ["gear", "linkage"],
        "command_constrain_linkage": ["linkage", "pen"],
    }

    DefaultRules = {
        "max_gear_teeth": 60,
        "min_gear_teeth": 10,
        "max_linkage_length": 10,
        "min_linkage_length": 5,
        "max_value": 0xffffffff,
        "gear_module": 2,
    }

    def __init__(self, world, rules=None):
        if rules == None:
            rules = {}
        self.world = world
        self.rules = self.DefaultRules.copy()
        self.rules.update(rules)
        self.gears = []
        self.linkages = []

    def embed(self):
        (width, height) = self.world.size
        center_width = width / 2
        center_height = height / 2
        position = (center_width, center_height)
        self.gears[0].normalize()
        self.gears[0].set_position(position)
        for link in self.linkages:
            link.prepare_embed()
        self.gears[0].embed(self.world)

    def scale(self, script, *args):
        if len(args) == 1:
            min_val = 0
            max_val = args[0]
        elif len(args) == 2:
            min_val = args[0]
            max_val = args[1]
        else:
            raise RuntimeError, "must provide one or two values"
        val = (script.next() / float(self.rules["max_value"])) * (max_val - min_val) + min_val
        return val

    def modulo(self, script, *args):
        if len(args) == 1:
            min_val = 0
            max_val = args[0]
        elif len(args) == 2:
            min_val = args[0]
            max_val = args[1]
        else:
            raise RuntimeError, "must provide one or two values"
        val = script.next() % (max_val - min_val) + min_val
        return val

    def select(self, script, choices):
        value = script.next()
        return choices[value % len(choices)]

    def execute(self, domain, script):
        while domain in self.Grammar:
            choices = self.Grammar[domain]
            choice = self.select(script, choices)
            domain = "%s_%s" % (domain, choice)
        func = getattr(self, domain)
        func(script)

    def parse(self, script):
        script = iter(script)
        try:
            while script:
                try:
                    self.execute("command", script)
                except ZeroDivisionError:
                    pass
        except StopIteration:
            pass

    def command_add_gear(self, script):
        teeth = self.modulo(script, self.rules["min_gear_teeth"], self.rules["max_gear_teeth"])
        self.add_gear(number_of_teeth=teeth)

    def add_gear(self, **kw):
        module = self.rules["gear_module"]
        name = "gear-%d" % len(self.gears)
        kw["module"] = module
        kw["name"] = name
        if self.gears:
            gear = Gear(**kw)
        else:
            gear = Motor(**kw)
        self.gears.append(gear)

    def command_add_linkage(self, script):
        length = self.modulo(script, self.rules["min_linkage_length"], self.rules["max_linkage_length"])
        self.add_linkage(length=length)

    def add_linkage(self, **kw):
        name = "linkage-%d" % len(self.linkages)
        kw["name"] = name
        linkage = Linkage(**kw)
        self.linkages.append(linkage)

    def command_constrain_gear_gear(self, script):
        gear_a = self.select(script, self.gears)
        gear_b = self.select(script, self.gears)
        angle = self.scale(script, math.pi * 2)
        self.constrain_gear_gear(gear_a, gear_b, angle)

    def constrain_gear_gear(self, gear_a, gear_b, angle):
        gear_a.link_gear(gear_b, angle)

    def command_constrain_gear_linkage(self, script):
        gear = self.select(script, self.gears)
        linkage = self.select(script, self.linkages)
        gear_phase = self.scale(script, math.pi * 2)
        gear_radius = self.scale(script, gear, gear._gear.pitch_radius)
        self.constrain_gear_linkage(gear, gear_phase, gear_radius, linkage)

    def constrain_gear_linkage(self, gear, angle, radius, linkage):
        gear.link_linkage(angle, radius, linkage)

    def command_constrain_linkage_linkage(self, script):
        linkage_a = self.select(script, self.linkages)
        linkage_b = self.select(script, self.linkages)
        if linkage_a == linkage_b:
            return
        pivot_a = self.scale(script, linkage_a.length)
        pivot_b = self.scale(script, linkage_b.length)
        linkage_a.link_linkage(pivot_a, linkage_b, pivot_b)

    def constrain_linkage_linkage(self, linkage_a, linkage_b, pivot_a, pivot_b):
        linkage_a.link_linkage(pivot_a, linkage_b, pivot_b)

    def command_constrain_linkage_pen(self, script):
        pass

class World(object):
    def __init__(self, size):
        self.size = size
        self.init_world()

    def init_world(self):
        self.world = pymunk.Space()
        self.world.gravity = (0, 0)
        self.world.damping = 1

    def add(self, *args, **kw):
        self.world.add(*args, **kw)

    def step(self, val):
        self.world.step(val)
    
class RenderSimulation(object):
    def __init__(self, simulation, pen=None):
        self.simulation = simulation
        self.pen = pen
        self.pen_points = []
        self.init_pyglet()

    def init_pyglet(self):
        (width, height) = self.simulation.size
        config = pyglet.gl.Config(sample_buffers=1, samples=2, double_buffer=True)
        self.window = pyglet.window.Window(config=config, width=width, height=height, vsync=False)
        self.on_draw = self.window.event(self.on_draw)

    def update(self, dt):
        # Note that we dont use dt as input into step. That is because the 
        # simulation will behave much better if the step size doesnt change 
        # between frames.
        r = 10
        for x in range(r):
            self.simulation.step(1.0 / 30.0 / r)               

    def run(self):
        pyglet.clock.schedule_interval(self.update, 1 / 30.0)
        pyglet.app.run()

    def draw_pen(self):
        if not self.pen:
            return
        body = self.pen.body
        pv1 = body.position + self.pen.a.rotated(body.angle)
        pv2 = body.position + self.pen.b.rotated(body.angle)
        self.pen_points.extend(pv2)
        self.pen_points = self.pen_points[-20:]
        count = len(self.pen_points) / 2
        if count < 2:
            return
        color = (255, 0, 0)
        pyglet.graphics.draw(count, pyglet.gl.GL_LINE_STRIP, ('v2f', self.pen_points), ('c3B', color * count))

    def on_draw(self):
        pyglet.gl.glClearColor(240,240,240,255)
        self.window.clear()
        draw(self.simulation.world)
        self.draw_pen()

def use_case_one(world):
    builder = WorldBuild(world)
    builder.add_gear(number_of_teeth=20)
    builder.add_gear(number_of_teeth=30)
    builder.constrain_gear_gear(builder.gears[0], builder.gears[1], 0)
    builder.add_linkage(length=100)
    builder.constrain_gear_linkage(builder.gears[0], 0, 10, builder.linkages[0])
    builder.add_linkage(length=40)
    builder.constrain_gear_linkage(builder.gears[1], 0, 15, builder.linkages[1])
    builder.constrain_linkage_linkage(builder.linkages[0], builder.linkages[1], 50, 39)
    builder.embed()
    return builder.linkages[0]

def random_config(world):
    max_val = WorldBuild.DefaultRules["max_value"]
    script = [int(random.random() * max_val) for x in range(500)]
    builder = WorldBuild()
    builder.parse(script)
    builder.embed(world)

size = (500, 500)
world = World(size)
pen = use_case_one(world)
render = RenderSimulation(world, pen.segment)
render.run()
