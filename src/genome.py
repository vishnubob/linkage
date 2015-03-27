import math
import random

from . import graph

class Gene(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.world = None
        self.graph = None

    def bind(self, parent, world, graph, visited=None):
        if visited == None:
            visited = set()
        visited.add(self)
        self.parent = parent
        self.world = world
        self.graph = graph
        for child in self.children(visited):
            child.bind(self, self.world, self.graph, visited)

    def express(self):
        pass

    def children(self, visited):
        nodes = set(self.graph[self])
        to_visit = nodes - visited
        visited.add(to_visit)
        return iter(to_visit)

class PivotGene(Gene):
    pass

class PivotGearGene(PivotGene):
    def express(self, graph, world):
        pass

class PivotLinkageGene(PivotGene):
    def express(self, graph, world):
        pass

class GearGene(Gene):
    def embed_body(self, world):
        self.body = pymunk.Body(1, 1)
        self.body.position = self.position
        self.circle = pymunk.Circle(self.body, self._gear.pitch_radius)
        self.circle.layer = self.PymunkLayer
        self.circle.group = self.PymunkGroup
        self.static_body = pymunk.Body()
        self.static_body.position = self.position
        joint = pymunk.constraint.PivotJoint(self.body, self.static_body, self.position)
        self.world.add(self.body, self.circle, joint)

class MotorGene(GearGene):
    def express(self, visited=None):
        if visited == None:
            visited = set()
        visited.add(self)
        self.embed_body()
        for child in self.children:
            child.express(visited)

    def get_position(self):
        return self.world.gear_box * (.5, .5)
    position = property(get_position)

    def embed_body(self, world):
        super(Motor, self).embed_body(world)
        motor_joint = pymunk.constraint.SimpleMotor(self.static_body, self.body, 10)
        world.add([motor_joint])

class LinkageGene(Gene):
    def express(self, graph, world):
        pass

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



class Specie(object):
    DefaultRules = {}

    def __init__(self, rules=None):
        if rules == None:
            rules = {}
        self.rules = self.DefaultRules.copy()
        self.rules.update(rules)

    def scale(self, genome, max_val=1, min_val=0):
        return (genome.next() / float(self.rules["max_value"])) * (max_val - min_val) + min_val

    def modulo(self, genome, max_val=1, min_val=0):
        val = genome.next() % (max_val - min_val) + min_val
        return val

    def select(self, genome, choices):
        idx = self.modulo(genome, len(choices))
        return choices[idx]

    def execute(self, domain, genome):
        while domain in self.Grammar:
            choices = self.Grammar[domain]
            choice = self.select(genome, choices)
            domain = "%s_%s" % (domain, choice)
        func = getattr(self, domain)
        func(genome)

    def parse(self, genome):
        genome = iter(genome)
        try:
            while genome:
                try:
                    self.execute("command", genome)
                except ZeroDivisionError:
                    pass
        except StopIteration:
            pass

class Genome(list):
    pass

class GearPivotSpecie(Specie):
    Grammar = {
        "command": ["add", "link"],
        "command_add": ["gear", "gear_pivot", "linkage_pivot"],
        "command_link": ["gear_to_gear", "gear_pivot_to_linkage_pivot", "linkage_pivot_to_linkage_pivot"],
    }

    DefaultRules = {
        "max_gear_teeth": 60,
        "min_gear_teeth": 10,
        "max_linkage_length": 10,
        "min_linkage_length": 5,
        "max_value": 0xffffffff,
        "gear_module": 2,
    }

    def __init__(self, **kw):
        super(GearPivotSpecie, self).__init__(**kw)
        self.gears = []
        self.linkages = []
        self.linkage_pivots = []
        self.gear_pivots = []
        self.graph = graph.BidirectedGraph()

    ####
    ## Genome Parsers
    def command_add_gear(self, genome):
        teeth = self.modulo(genome, self.rules["min_gear_teeth"], self.rules["max_gear_teeth"])
        self.add_gear(number_of_teeth=teeth)

    def command_add_linkage_pivot(self, genome):
        x_position = self.scale(genome)
        y_position = self.scale(genome)
        position = (x_position, y_position)
        self.add_linkage_pivot(position=position)

    def command_add_gear_pivot(self, genome):
        gear = self.select(genome, self.gears)
        angle = self.scale(genome, math.pi * 2)
        radius = self.scale(genome)
        self.add_gear_pivot(gear=gear, angle=angle, radius=radius)

    def command_link_gear_to_gear(self, genome):
        gear_a = self.select(genome, self.gears)
        gear_b = self.select(genome, self.gears)
        angle = self.scale(genome, math.pi * 2)
        self.link_gear_to_gear(gear_a=gear_a, gear_b=gear_b, angle=angle)

    def command_link_gear_pivot_to_linkage_pivot(self, genome):
        pivot_a = self.select(genome, self.linkage_pivots)
        pivot_b = self.select(genome, self.gear_pivots)
        self.link_gear_pivot_to_linkage_pivot(pivot_a=pivot_a, pivot_b=pivot_b)

    def command_link_linkage_pivot_to_linkage_pivot(self, genome):
        pivot_a = self.select(genome, self.linkage_pivots)
        pivot_b = self.select(genome, self.linkage_pivots)
        self.link_linkage_pivot_to_linkage_pivot(pivot_a=pivot_a, pivot_b=pivot_b)

    ####
    ## Genome Expression
    def add_gear(self, **kw):
        module = self.rules["gear_module"]
        name = "gear-%d" % len(self.gears)
        kw["module"] = module
        kw["name"] = name
        gear = GearGene(**kw)
        self.gears.append(gear)
        self.graph.add_node(gear)

    def add_linkage(self, **kw):
        name = "linkage-%d" % len(self.linkages)
        kw["name"] = name
        linkage = LinkageGene(**kw)
        self.linkages.append(linkage)
        self.graph.add_node(linkage)
        return linkage

    def add_linkage_pivot(self, **kw):
        name = "linkage_pivot-%d" % len(self.linkage_pivots)
        kw["name"] = name
        pivot = PivotGene(**kw)
        self.linkage_pivots.append(pivot)
        self.graph.add_node(pivot)

    def add_gear_pivot(self, gear=None, **kw):
        name = "gear_pivot-%d" % len(self.gear_pivots)
        kw["name"] = name
        pivot = PivotGene(**kw)
        self.gear_pivots.append(pivot)
        self.graph.add_node(pivot)
        self.graph.connect(gear, pivot)

    def link_gear_to_gear(self, gear_a=None, gear_b=None, **kw):
        if gear_a == gear_b:
            return
        self.graph.connect(gear_a, gear_b)

    def link_gear_pivot_to_linkage_pivot(self, pivot_a=None, pivot_b=None, **kw):
        if pivot_a == pivot_b:
            return
        linkage = self.add_linkage(pivot_a=pivot_a, pivot_b=pivot_b)
        self.graph.connect(pivot_a, linkage)
        self.graph.connect(linkage, pivot_b)

    def link_linkage_pivot_to_linkage_pivot(self, pivot_a=None, pivot_b=None, **kw):
        if pivot_a == pivot_b:
            return
        linkage = self.add_linkage(pivot_a=pivot_a, pivot_b=pivot_b)
        self.graph.connect(pivot_a, linkage)
        self.graph.connect(linkage, pivot_b)

    def normalize_graph(self):
        motor = self.gears[0]
        connected_gears = self.bfs_walk(motor, kind=GearGene)
        all_gears = set(self.gears)
        disjoint_gears = all_gears - connected_gears
        for node in disjoint_gears:
            self.graph.remove_node(node)
        #
        connected_nodes = self.bfs_walk(motor)
        all_nodes = set(self.graph.keys())
        disjoint_nodes = all_nodes - connected_nodes
        for node in disjoint_nodes:
            self.graph.remove_node(node)

    def bfs_walk(self, node, kind=None, visited=None):
        if visited == None:
            visited = set()
        visited.add(node)
        for node in self.graph[node]:
            if kind != None and not isinstance(node, kind):
                continue
            if node in visited:
                continue
            visited = self.bfs_walk(node, visited=visited)
        return visited

class GearPivotGenome(Genome):
    SpecieClass = GearPivotSpecie

    @classmethod
    def random_genome(cls, length=100):
        max_val = cls.SpecieClass.DefaultRules["max_value"]
        genome = [random.randint(0, max_val) for x in range(length)]
        return cls(genome)

