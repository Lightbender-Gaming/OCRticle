from functools import reduce
from itertools import combinations, product
from math import atan2

from kivy.graphics import Rectangle

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

def get_original_rect(rect):
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

def parse_rect(new_rect, rects, image):
    new_rect_points = get_points(new_rect)
    q = [new_rect_points]
    final_rects = []

    while len(q) > 0:
        rect = q.pop()
        fine = True
        for orig_rect in rects:
            bounds = get_points(orig_rect)

            if rect['x1'] < bounds['x1'] < rect['x2']:
                new1 = rect.copy()
                new1['x2'] = bounds['x1']
                q.append(new1)
                new2 = rect.copy()
                new2['x1'] = bounds['x1']
                q.append(new2)
                fine = False
                break
            elif rect['x1'] < bounds['x2'] < rect['x2']:
                new1 = rect.copy()
                new1['x2'] = bounds['x2']
                q.append(new1)
                new2 = rect.copy()
                new2['x1'] = bounds['x2']
                q.append(new2)
                fine = False
                break
            elif rect['x1'] < bounds['x2'] and rect['x2'] > bounds['x1']:
                if rect['y1'] < bounds['y1'] < rect['y2']:
                    new1 = rect.copy()
                    new1['y2'] = bounds['y1']
                    q.append(new1)
                    new2 = rect.copy()
                    new2['y1'] = bounds['y1']
                    q.append(new2)
                    fine = False
                    break
                elif rect['y1'] < bounds['y2'] < rect['y2']:
                    new1 = rect.copy()
                    new1['y2'] = bounds['y2']
                    q.append(new1)
                    new2 = rect.copy()
                    new2['y1'] = bounds['y2']
                    q.append(new2)
                    fine = False
                    break
                elif rect['y1'] < bounds['y2'] and rect['y2'] > bounds['y1']:
                    fine = False
        if fine:
            final_rects.append(rect)

    print(final_rects)
    return_rects = []
    for points in final_rects:
        width = points['x2'] - points['x1']
        height = points['y2'] - points['y1']
        rect = Rectangle(pos=(points['x1'], points['y1']), size=(width, height))
        return_rects.append({
            'rect': rect,
            'original_x': (points['x1'] - (image.center_x - image.norm_image_size[0] / 2)) * image.texture_size[0] / image.norm_image_size[0],
            'original_y': (points['y1'] - (image.center_y - image.norm_image_size[1] / 2)) * image.texture_size[1] / image.norm_image_size[1],
            'original_width': width * image.texture_size[0] / image.norm_image_size[0],
            'original_height': height * image.texture_size[1] / image.norm_image_size[1]
        })
    return return_rects