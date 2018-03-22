from itertools import product

TAGS = ['origin_x', 'origin_y', 'distance_x', 'distance_y', 'nudges',
        'bottom_left_colour', 'other_colour']

TYPES = [int, int, int, int, int, str, str]

EXTEND = [False, False, True, True, True, True, True]

OPTIONS = 'x = 12pt, y = 12pt, '\
            'gridline/.style = {black, line width = 2pt, line join = round, line cap = round}'

SHIFTS = {'bottom' : (0, 0), 'right' : (2, 0),
            'top' : (2, 2), 'left' : (0, 2)}

ARC_TYPES = {'bottom' : '(180:360:1)', 'right' : '(-90:90:1)',
            'top' : '(0:180:1)' , 'left' : '(90:270:1)'}

def sym_coords(nx, ny):
    """
    Convenience function for square lattice definition, returns all
    pairs of co-ordinates on an n-by-n lattice which are both even or
    both odd. Note that it iterates over all of the points in the 2D
    grid which is nx-by-ny large, this is so the list of returned
    coordinates is sorted.
    """
    symmetric_coordinates = []
    for x in range(nx):
        if x % 2 == 0:
            for y in range(ny):
                if y % 2 == 0:
                    symmetric_coordinates.append((x, y))
        else:
            for y in range(ny):
                if y % 2 == 1:
                    symmetric_coordinates.append((x, y))
    return symmetric_coordinates


def skew_coords(nx, ny):
    """
    Convenience function for square lattice definition, returns all
    pairs of co-ordinates on an n-by-n lattice which are "even-odd" or
    "odd-even".Note that it iterates over all of the points in the 2D
    grid which is nx-by-ny large, this is so the list of returned
    coordinates is sorted.
    """
    skewed_coordinates = []
    for x in range(nx):
        if x % 2 == 0:
            for y in range(ny):
                if y % 2 == 1:
                    skewed_coordinates.append((x, y))
        else:
            for y in range(ny):
                if y % 2 == 0:
                    skewed_coordinates.append((x, y))
    return skewed_coordinates

# draw_tfm = lambda crd, o_x, o_y: (2 * crd[0] + o_x + 1, 2 * crd[1] + o_y + 1)
draw_tfm = lambda crd: (2 * crd[0] + 1, 2 * crd[1] + 1)
draw_tfm.__doc__ = "Takes regular cartesian coords to drawn coords"

tikz_crds = lambda crds: ', '.join(['{}/{}'.format(*c) for c in crds])

def file_to_args(flnm):
    """
    Takes a file whose lines are of the form:
        var_name bunch of values
    and returns a list of lists whose elements are suitable for input
    into sc_tikz using sc_tikz(*lst).  
    """
    with open(flnm, 'rb') as phil:
        lns = phil.readlines()
        if type(lns[0]) == bytes:
            lns = [ln.decode("utf-8") for ln in lns]

    arg_d = {}
    
    for ln in lns:
        lst = ln.split()
        arg_d[lst[0]] = lst[1:]

    n_tls = max(len(v) for v in arg_d.values())

    for tag, typ, ext in zip(TAGS, TYPES, EXTEND):
        arg_d[tag] = list(map(typ, arg_d[tag]))
        if ext and (len(arg_d[tag]) == 1):
            arg_d[tag] = [arg_d[tag][0] for idx in range(n_tls)]

    return [ [ arg_d[tag][dx] for tag in TAGS ] for dx in range(n_tls)]

def sc_tikz(o_x, o_y, d_x, d_y, nudge, bl_col, oth_col):
    """
    produces a tikz block (the part that goes between the 
    \begin{tikzpicture} and \end{tikzpicture}) for a single surface 
    code patch.

    I try to produce legible TikZ at all times.

    This code returns a list of strings which you can join with \n.
    """
    sz = (d_x - 1, d_y - 1)

    output_strs = [r'% args: ' + repr(locals())]
    output_strs.append(r'% overall translation')
    scope_stmt = r'\begin{{scope}}[shift = {{{}}}]'
    output_strs.append(scope_stmt.format((o_x, o_y)))
    
    output_strs.append(r'% fill grid squares with background colours')
    bl_range = list(map(draw_tfm, sym_coords(*sz)))
    oth_range = list(map(draw_tfm, skew_coords(*sz)))
    bl_crds, oth_crds = tikz_crds(bl_range), tikz_crds(oth_range)
    for crds, col in zip([bl_crds, oth_crds], [bl_col, oth_col]):
        # output_strs.extend([''.join([r'\foreach \x/\y in {', crds, r'}{']),
        #                     ''.join([r'    \fill[', col, r'] (\x, \y) rectangle +(2,2);']),
        #                     r'}'])
        output_strs.extend([''.join([r'\foreach \x/\y in {', crds, r'}{']),
                            ''.join([r'    \filldraw[gridline, fill=', col, r'] (\x, \y) rectangle +(2,2);']),
                            r'}'])

    # output_strs.append(r'% draw grid')
    # corner_crds = [c + 1 for c in bl_range[0]] + [2 * d_x, 2 * d_y]
    # styl_str = r'\draw[gridline, step=2, shift = {(-1,-1)}]'
    # grid_str = ' ({}, {}) grid ({}, {});'.format(*corner_crds)
    # output_strs.append(styl_str + grid_str)
    
    output_strs.append(r'% draw/fill arcs')
    
    #calculate arc starting points by first finding neighbouring squares
    if nudge:
        arc_starts = {
            'bottom' : list(filter(lambda pt: pt[1] == 0, skew_coords(*sz))),
            'right' : list(filter(lambda pt: pt[0] == sz[0] - 1, sym_coords(*sz))),
            'top' : list(filter(lambda pt: pt[1] == sz[1] - 1, skew_coords(*sz))),
            'left' :  list(filter(lambda pt: pt[0] == 0, sym_coords(*sz)))
        }
    else:
        arc_starts = {
            'bottom' : list(filter(lambda pt: pt[1] == 0, sym_coords(*sz))),
            'right' : list(filter(lambda pt: pt[0] == sz[0] - 1, skew_coords(*sz))),
            'top' : list(filter(lambda pt: pt[1] == sz[1] - 1, sym_coords(*sz))),
            'left' :  list(filter(lambda pt: pt[0] == 0, skew_coords(*sz)))
        }
    #scale and shift
    for key in arc_starts.keys():
        new_pts = list(map(list, map(draw_tfm, arc_starts[key])))
        for tpl in new_pts:
            tpl[0] += SHIFTS[key][0]
            tpl[1] += SHIFTS[key][1]
        arc_starts[key] = tikz_crds(new_pts)
        # print(tikz_crds(new_pts))
        # print(arc_starts[key]) 
    
    if nudge:
        colours = {'top' : bl_col, 'bottom' : bl_col, 'left' : oth_col, 'right' : oth_col}
    else:
        colours = {'top' : oth_col, 'bottom' : oth_col, 'left' : bl_col, 'right' : bl_col}

    for key in arc_starts.keys():
        output_strs.extend([''.join([r'\foreach \x/\y in {', arc_starts[key] , r'}{']),
                                ''.join([r'    \filldraw[gridline, fill = ', colours[key], r'] (\x, \y) arc {} -- cycle;'.format(ARC_TYPES[key])]),
                                r'}'])
    
    output_strs.append(r'\end{scope}')
    return output_strs

def main(flnm):
    """
    Does the default thing. That is:
     + opens the file with name flnm
     + produces a gigantic string of output
     + saves it to a file whose name is the same as flnm, except it 
       now has a .tikz extension
    """
    out_nm = flnm.split('.')[0] + '.tikz'
    
    out_lines = [''.join([r'\begin{tikzpicture}[', OPTIONS, ']'])]
    
    for args in file_to_args(flnm):
        out_lines.extend(sc_tikz(*args))

    out_lines.append(r'\end{tikzpicture}')

    with open(out_nm, 'wb') as phil:
        phil.writelines(map(lambda st: bytes(st + '\n', "utf-8"), out_lines))

    pass

if __name__ == '__main__':
    from sys import argv
    flnm = argv[1]
    main(flnm)

