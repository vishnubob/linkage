__all__ = ["draw", "GraphViz"]

import math
import pyglet
import pymunk
from pymunk.vec2d import Vec2d
import graphviz
from graph import *

def draw(*objs, **kwargs):
    new_batch = False
    
    if "batch" not in kwargs:
        new_batch = True
        batch = pyglet.graphics.Batch()
    else:
        batch = kwargs["batch"]
        
    for o in objs:
        if isinstance(o, pymunk.Space):
            _draw_space(o, batch)
        elif isinstance(o, pymunk.Shape):
            _draw_shape(o, batch)
        elif isinstance(o, pymunk.Constraint):
            _draw_constraint(o, batch)
        elif hasattr(o, '__iter__'):
            for oo in o:
                draw(oo, **kwargs)
    
    if new_batch:
        batch.draw()

def _draw_space(space, batch = None):
    for s in space.shapes:
        if not (hasattr(s, "ignore_draw") and s.ignore_draw):
            _draw_shape(s, batch)
    for c in space.constraints:
        if not (hasattr(c, "ignore_draw") and c.ignore_draw):
            _draw_constraint(c, batch)
            
def _draw_shape(shape, batch = None):
    if isinstance(shape, pymunk.Circle):
        _draw_circle(shape, batch)
    elif isinstance(shape, pymunk.Segment):
        _draw_segment(shape, batch)
    elif isinstance(shape, pymunk.Poly):
        _draw_poly(shape, batch)
    
def _draw_circle(circle, batch = None):
    circle_center = circle.body.position + circle.offset.rotated(circle.body.angle)
    
    r = 0
    if hasattr(circle, "color"):
        color = circle.color  
    elif circle.body.is_static:
        color = (200, 200, 200)
        r = 1
    else:
        color = (255, 0, 0)
        
    #http://slabode.exofire.net/circle_draw.shtml
    num_segments = int(4 * math.sqrt(circle.radius))
    theta = 2 * math.pi / num_segments
    c = math.cos(theta)
    s = math.sin(theta)
    
    x = circle.radius # we start at angle 0
    y = 0
    
    ps = []
    
    for i in range(num_segments):
        ps += [Vec2d(circle_center.x + x, circle_center.y + y)]
        t = x
        x = c * x - s * y
        y = s * t + c * y
               
    
    if circle.body.is_static:
        mode = pyglet.gl.GL_LINES
        ps = [p for p in ps+ps[:1] for _ in (0, 1)]
    else:
        mode = pyglet.gl.GL_TRIANGLE_STRIP
        ps2 = [ps[0]]
        for i in range(1, int(len(ps)+1/2)):
            ps2.append(ps[i])
            ps2.append(ps[-i])
        ps = ps2
    vs = []
    for p in [ps[0]] + ps + [ps[-1]]:
            vs += [p.x, p.y]
        
    c = circle_center + Vec2d(circle.radius, 0).rotated(circle.body.angle)
    cvs = [circle_center.x, circle_center.y, c.x, c.y]
        
    bg = pyglet.graphics.OrderedGroup(0)
    fg = pyglet.graphics.OrderedGroup(1)
        
    l = len(vs)//2
    if batch == None:
        pyglet.graphics.draw(l, mode,
                            ('v2f', vs),
                            ('c3B', color*l))
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                            ('v2f', cvs),
                            ('c3B', (0,0,255)*2))
    else:
        batch.add(len(vs)//2, mode, bg,
                 ('v2f', vs),
                 ('c3B', color*l))
        batch.add(2, pyglet.gl.GL_LINES, fg,
                 ('v2f', cvs),
                 ('c3B', (0,0,255)*2))
    return

def _draw_poly(poly, batch = None):
    ps = poly.get_vertices()
    
    if hasattr(poly, "color"):
        color = poly.color  
    elif poly.body.is_static:
        color = (200, 200, 200)
    else:
        color = (0, 255, 0)
        
    if poly.body.is_static:
        mode = pyglet.gl.GL_LINES
        ps = [p for p in ps+ps[:1] for _ in (0, 1)]
    else:
        mode = pyglet.gl.GL_TRIANGLE_STRIP
        ps = [ps[1],ps[2], ps[0]] + ps[3:]
        
    vs = []
    for p in [ps[0]] + ps + [ps[-1]]:
            vs += [p.x, p.y]
        
    l = len(vs)//2
    if batch == None:
        pyglet.graphics.draw(l, mode,
                            ('v2f', vs),
                            ('c3B', color*l))
    else:
        batch.add(l, mode, None,
                 ('v2f', vs),
                 ('c3B', color*l))

def _draw_segment(segment, batch = None):
    body = segment.body
    pv1 = body.position + segment.a.rotated(body.angle)
    pv2 = body.position + segment.b.rotated(body.angle)
    
    d = pv2 - pv1
    a = -math.atan2(d.x, d.y)
    dx = segment.radius * math.cos(a)
    dy = segment.radius * math.sin(a)
    
    p1 = pv1 + Vec2d(dx,dy)
    p2 = pv1 - Vec2d(dx,dy)
    p3 = pv2 + Vec2d(dx,dy)
    p4 = pv2 - Vec2d(dx,dy)
           
    vs = [i for xy in [p1,p2,p3]+[p2,p3,p4] for i in xy]
    
    if hasattr(segment, "color"):
        color = segment.color  
    elif segment.body.is_static:
        color = (200, 200, 200)
    else:
        color = (0, 0, 255)
        
    l = len(vs)//2
    if batch == None:
        pyglet.graphics.draw(l, pyglet.gl.GL_TRIANGLES,
                            ('v2f', vs),
                            ('c3B', color * l))
    else:
        batch.add(l,pyglet.gl.GL_TRIANGLES, None,
                 ('v2f', vs),
                 ('c3B', color * l))

def _draw_constraint(constraint, batch=None):
    darkgrey = (169, 169, 169)

    if isinstance(constraint, pymunk.GrooveJoint) and hasattr(constraint, "groove_a"):
        pv1 = constraint.a.position + constraint.groove_a.rotated(constraint.a.angle)
        pv2 = constraint.a.position + constraint.groove_b.rotated(constraint.a.angle)
        _draw_line(pv1, pv2, darkgrey, batch)
    elif isinstance(constraint, pymunk.PinJoint):
        pv1 = constraint.a.position + constraint.anchr1.rotated(constraint.a.angle)
        pv2 = constraint.b.position + constraint.anchr2.rotated(constraint.b.angle)
        _draw_line(pv1, pv2, darkgrey, batch)
    elif hasattr(constraint, "anchr1"):
        pv1 = constraint.a.position + constraint.anchr1.rotated(constraint.a.angle)
        pv2 = constraint.b.position + constraint.anchr2.rotated(constraint.b.angle)
        _draw_line(pv1, pv2, darkgrey, batch)
    else:
        pv1 = constraint.a.position
        pv2 = constraint.b.position
        _draw_line(pv1, pv2, darkgrey, batch)

def _draw_line(pv1, pv2, color, batch):
    line = (int(pv1.x), int(pv1.y), int(pv2.x), int(pv2.y))
    if batch == None:
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES,
                            ('v2f', line),
                            ('c3B', color * 2))
    else:
        batch.add(2, pyglet.gl.GL_LINES, None,
                  ('v2i', line),
                  ('c3B', color * 2))

class GraphViz(object):
    def render(self, graph, filename="graph_dot"):
        directed = isinstance(graph, DirectedGraph)
        dot = graphviz.Graph(format="png")
        visited = set()
        for node in graph:
            dot.node(str(id(node)), label=node.name)
        for node in graph:
            for n_node in graph[node]:
                if directed or (n_node, node) not in visited:
                    dot.edge(str(id(node)), str(id(n_node)), label=str(graph[node][n_node]))
                    visited.add((node, n_node))
        dot.render(filename)
