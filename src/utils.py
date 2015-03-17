def center(pos):
    return (pos[0] / 2.0, pos[1] / 2.0)

def square(size):
    return math.sqrt(size[0] * size[1])

def euclidean_distance(pos1, pos2):
    (x1, y1) = pos1
    (x2, y2) = pos2
    distance = (x2 - x1) ** 2 + (y1 - y2) ** 2
    return math.sqrt(distance)
