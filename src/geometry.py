from functools import reduce
from itertools import combinations, product
from math import atan2

def calc_line_points(rects):
    points = set()
    line = []
    for r in rects:
        r = get_points(r)
        
        for (x,y) in product([r['x1'],r['x2']],[r['y1'],r['y2']]):
            not_inside = True
            for rr in rects:
                if rr == r: continue
                rr = get_points(rr)
                if rr['x1'] < x < rr['x2'] and rr['y1'] < y < rr['y2']:
                    not_inside = False
                    break
            if not_inside:
                points.add((x,y))

    for ra,rb in combinations(rects, 2):
        ra = get_points(ra)
        rb = get_points(rb)

        x1 = max(ra['x1'], rb['x1'])
        x2 = min(ra['x2'], rb['x2'])
        y1 = max(ra['y1'], rb['y1'])
        y2 = min(ra['y2'], rb['y2'])

        if x2 > x1 and y2 > y1:
            for (x,y) in product([x1,x2],[y1,y2]):
                not_inside = True
                for rr in rects:
                    rr = get_points(rr)
                    if rr['x1'] < x < rr['x2'] and rr['y1'] < y < rr['y2']:
                        not_inside = False
                        break
                if not_inside:
                    points.add((x,y))

    initial_point = point = min(points)
    line.append(point)
    points.remove(point)
    horizontal = True
    while len(points) > 0:
        if horizontal:
            next_point = sorted(((x,y) for (x,y) in points if x == point[0]), key=lambda p : abs(p[1] - point[1]))[0]
        else:
            next_point = sorted(((x,y) for (x,y) in points if y == point[1]), key=lambda p : abs(p[0] - point[0]))[0]
        line.append(next_point)
        points.remove(next_point)
        point = next_point
        horizontal = not horizontal

    line.append(initial_point)

    return reduce(lambda acc, x: acc + [*x], line, [])

    

def get_points(rect):
    if isinstance(rect, dict):
        rect = rect['rect']

    x1 = rect.pos[0]
    x2 = x1 + rect.size[0]
    y1 = rect.pos[1]
    y2 = y1 + rect.size[1]

    if x1 > x2:
        (x1,x2) = (x2,x1)
    if y1 > y2:
        (y1,y2) = (y2,y1)

    return {
        'x1': x1,
        'x2': x2,
        'y1': y1,
        'y2': y2
    }

def get_rect(rect):
    x1 = rect['original_x']
    x2 = x1 + rect['original_width']
    y1 = rect['original_y']
    y2 = y1 + rect['original_height']

    if x1 > x2:
        (x1,x2) = (x2,x1)
    if y1 > y2:
        (y1,y2) = (y2,y1)

    return [(x1, y1),
            (x2, y2)]

def point_in_rects(point, rects):
    (x,y) = point
    for r in map(get_points, rects):
        if r['x1'] <= x <= r['x2'] and r['y1'] <= y <= r['y2']:
            return True
    return False