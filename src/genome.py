import math
import random

from . import graph

class PivotGene(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

class GearGene(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

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
        "command_add": ["gear", "pivot", "pivot_on_gear"],
        "command_link": ["gear", "pivot"],
        "command_link_gear": ["to_gear"],
        "command_link_pivot": ["to_pivot"],
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
        self.pivots = []
        self.graph = graph.BidirectedGraph()

    ####
    ## Genome Parsers
    def command_add_gear(self, genome):
        teeth = self.modulo(genome, self.rules["min_gear_teeth"], self.rules["max_gear_teeth"])
        self.add_gear(number_of_teeth=teeth)

    def command_add_pivot(self, genome):
        x_position = self.scale(genome)
        y_position = self.scale(genome)
        position = (x_position, y_position)
        self.add_pivot(position=position)

    def command_add_pivot_on_gear(self, genome):
        gear = self.select(genome, self.gears)
        angle = self.scale(genome, math.pi * 2)
        radius = self.scale(genome)
        self.add_gear_pivot(gear=gear, angle=angle, radius=radius)

    def command_link_gear_to_gear(self, genome):
        gear_a = self.select(genome, self.gears)
        gear_b = self.select(genome, self.gears)
        angle = self.scale(genome, math.pi * 2)
        self.link_gear_to_gear(gear_a=gear_a, gear_b=gear_b, angle=angle)

    def command_link_pivot_to_pivot(self, genome):
        pivot_a = self.select(genome, self.pivots)
        pivot_b = self.select(genome, self.pivots)
        self.link_pivot_to_pivot(pivot_a=pivot_a, pivot_b=pivot_b)

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

    def add_pivot(self, **kw):
        name = "pivot-%d" % len(self.pivots)
        kw["name"] = name
        pivot = PivotGene(**kw)
        self.pivots.append(pivot)
        self.graph.add_node(pivot)

    def add_gear_pivot(self, gear=None, **kw):
        name = "pivot-%d" % len(self.pivots)
        kw["name"] = name
        pivot = PivotGene(**kw)
        self.pivots.append(pivot)
        self.graph.add_node(pivot)
        self.graph.connect(gear, pivot, kw)

    def link_gear_to_gear(self, gear_a=None, gear_b=None, **kw):
        self.graph.connect(gear_a, gear_b, kw)

    def link_pivot_to_pivot(self, pivot_a=None, pivot_b=None, **kw):
        self.graph.connect(pivot_a, pivot_b, kw)

class GearPivotGenome(Genome):
    SpecieClass = GearPivotSpecie

    @classmethod
    def random_genome(cls, length=100):
        max_val = cls.SpecieClass.DefaultRules["max_value"]
        genome = [random.randint(0, max_val) for x in range(length)]
        return cls(genome)

