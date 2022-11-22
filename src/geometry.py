def calc_line_points(r):
    r = r['rects'][0]

    x1 = r.pos[0]
    x2 = x1 + r.size[0]
    y1 = r.pos[1]
    y2 = y1 + r.size[1]

    return [x1,y1,x2,y1,x2,y2,x1,y2]