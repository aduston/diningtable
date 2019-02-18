import sys
import re
import os.path
import json

from collections import namedtuple
from OCC import gp, TopLoc
from OCC.Visualization import Tesselator
from OCC.Display.SimpleGui import init_display
from OCC.Display.WebGl import threejs_renderer
from OCC.TopoDS import TopoDS_Builder, TopoDS_Compound
from OCC.BRepPrimAPI import BRepPrimAPI_MakeBox

from OCC.STEPControl import STEPControl_Writer, STEPControl_AsIs 

THICKNESS = 1.5
HEIGHT = 29.5
BENCH_HEIGHT = 18
SPANNER_HEIGHT = 6.

def Specs(**kwargs):
    return namedtuple('Specs', ' '.join(kwargs.keys()))(**kwargs)

SPECS = Specs(
    width=40.,
    length=95.,
    leg_width_inset=10., # distance from long edge to edge of leg
    leg_length_inset=24., # distance from short edge to center of leg
    leg_base_width_over=4.5,
    leg_base_length_over=1.5,
    split_top=False,
    double_spanner=True,
    spanner_sep = 5.5, # distance between centers of two
                       # spanners (if double_spanner is True)
    bench_width=15.,
    bench_leg_inset=12.
)

def _move(shape, x, y, z):
    tr = gp.gp_Trsf()
    tr.SetTranslation(gp.gp_Vec(x, y, z))
    loc = TopLoc.TopLoc_Location(tr)
    shape.Move(loc)
    return shape

_box = lambda *args: BRepPrimAPI_MakeBox(*args).Shape()

def _combine(*components):
    builder = TopoDS_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for c in components:
        builder.Add(compound, c)
    return compound

def _make_table_leg():
    leg_base = _box(
        THICKNESS + SPECS.leg_base_length_over * 2,
        SPECS.width - SPECS.leg_width_inset * 2 + \
            SPECS.leg_base_width_over * 2,
        THICKNESS)
    leg = _box(
        THICKNESS,
        SPECS.width - SPECS.leg_width_inset * 2,
        HEIGHT - THICKNESS * 2)
    _move(leg,
          SPECS.leg_base_length_over,
          SPECS.leg_base_width_over,
          0)
    _move(leg_base, 0, 0, HEIGHT - THICKNESS * 2)
    return _combine(leg_base, leg)

def _make_table_top():
    top = None
    if SPECS.split_top:
        SPLIT = 0.3
        side_0 = _box(SPECS.length, SPECS.width / 2 - SPLIT / 2, THICKNESS)
        side_1 = _box(SPECS.length, SPECS.width / 2 - SPLIT / 2, THICKNESS)
        _move(side_1, 0, SPECS.width / 2 + SPLIT / 2, 0)
        top = _combine(side_0, side_1)
    else:
        top = _box(SPECS.length, SPECS.width, THICKNESS)
    return _move(top, 0, 0, HEIGHT - THICKNESS)

def _make_spanners():
    num_spanners = 2 if SPECS.double_spanner else 1
    spanners = [
        _box(
            SPECS.length - SPECS.leg_length_inset * 2 - THICKNESS,
            THICKNESS,
            SPANNER_HEIGHT)
        for i in range(num_spanners)]
    if num_spanners == 1:
        _move(spanners[0],
              SPECS.leg_length_inset + THICKNESS / 2,
              SPECS.width / 2 - THICKNESS / 2,
              HEIGHT - THICKNESS * 2 - SPANNER_HEIGHT)
    else:
        _move(spanners[0],
              SPECS.leg_length_inset + THICKNESS / 2,
              SPECS.width / 2 - THICKNESS / 2 - SPECS.spanner_sep / 2,
              HEIGHT - THICKNESS * 2 - SPANNER_HEIGHT)
        _move(spanners[1],
              SPECS.leg_length_inset + THICKNESS / 2,
              SPECS.width / 2 - THICKNESS / 2 + SPECS.spanner_sep / 2,
              HEIGHT - THICKNESS * 2 - SPANNER_HEIGHT)
    return spanners

def _make_table():
    top = _make_table_top()
    leg_0 = _make_table_leg()
    leg_1 = _make_table_leg()
    spanners = _make_spanners()
    leg_base_inset = SPECS.leg_length_inset - THICKNESS / 2 - \
        SPECS.leg_base_length_over
    _move(leg_0,
          leg_base_inset,
          SPECS.leg_width_inset - SPECS.leg_base_width_over,
          0)
    _move(leg_1,
          SPECS.length - leg_base_inset - THICKNESS -
          SPECS.leg_base_length_over * 2,
          SPECS.leg_width_inset - SPECS.leg_base_width_over,
          0)
    return _combine(*([top, leg_0, leg_1] + spanners))

def _make_bench():
    top = _box(SPECS.length, SPECS.bench_width, THICKNESS)
    leg_0 = _box(THICKNESS, SPECS.bench_width, BENCH_HEIGHT - THICKNESS)
    leg_1 = _box(THICKNESS, SPECS.bench_width, BENCH_HEIGHT - THICKNESS)
    spanner = _box(
        SPECS.length - SPECS.bench_leg_inset * 2 - THICKNESS * 2,
        THICKNESS, SPANNER_HEIGHT)
    _move(spanner,
          SPECS.bench_leg_inset + THICKNESS,
          SPECS.bench_width / 2 - THICKNESS / 2,
          BENCH_HEIGHT - THICKNESS - SPANNER_HEIGHT)
    _move(leg_0, SPECS.bench_leg_inset, 0, 0)
    _move(leg_1, SPECS.length - SPECS.bench_leg_inset - THICKNESS, 0, 0)
    _move(top, 0, 0, BENCH_HEIGHT - THICKNESS)
    return _combine(top, leg_0, leg_1, spanner)

def _write_threejs_json(html_dir, shape):
    tess = Tesselator(shape)
    tess.Compute(compute_edges=False, mesh_quality=1.)
    with open(os.path.join(html_dir, "table.json"), 'w') as f:
        f.write(tess.ExportShapeToThreejsJSONString('table'))

def _write_pieces_json(html_dir):
    bench_pieces = {
        'top': [SPECS.length, SPECS.bench_width],
        'spanner': [
            SPECS.length - (SPECS.bench_leg_inset + THICKNESS) * 2,
            SPANNER_HEIGHT],
        'legs (2)': [BENCH_HEIGHT - THICKNESS, SPECS.bench_width]
    }
    spanner_label = 'spanners (2)' if SPECS.double_spanner else 'spanner'
    table_pieces = {
        'top': [SPECS.length, SPECS.width],
        'legs (2)': [
            HEIGHT - THICKNESS * 2,
            SPECS.width - SPECS.leg_width_inset * 2],
        'leg bases (2)': [
            SPECS.width - SPECS.leg_width_inset * 2 +
            SPECS.leg_base_width_over * 2,
            THICKNESS + SPECS.leg_base_length_over * 2
        ],
        spanner_label: [
            SPECS.length - SPECS.leg_length_inset * 2 - THICKNESS,
            SPANNER_HEIGHT]
    }
    json_string = json.dumps({
        'table': table_pieces,
        'bench': bench_pieces
    })
    index_js_fn = os.path.join(html_dir, 'index.js')
    with open(index_js_fn, 'r') as f:
        index_js = f.read()
    index_js = re.sub(
        r'var PIECES = [^;]+;',
        "var PIECES = {};".format(json_string),
        index_js,
        count=1)
    with open(index_js_fn, 'w') as f:
        f.write(index_js)

table = _make_table()
bench = _make_bench()
_move(bench, 0, SPECS.width - 2, 0)
# whole_thing = _combine(table, bench)
whole_thing = table

if len(sys.argv) > 1 and sys.argv[1] == 'json':
    html_dir = os.path.join(os.path.dirname(__file__), 'html')
    _write_threejs_json(html_dir, whole_thing)
    _write_pieces_json(html_dir)
else:
    display, start_display, _, _ = init_display()
    display.DisplayShape(whole_thing, update=True)
    start_display()
