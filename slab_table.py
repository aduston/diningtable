import sys
import os.path

from collections import namedtuple
from OCC import gp, TopLoc
from OCC.Visualization import Tesselator
from OCC.Display.SimpleGui import init_display
from OCC.Display.WebGl import threejs_renderer
from OCC.TopoDS import TopoDS_Builder, TopoDS_Compound
from OCC.BRepPrimAPI import BRepPrimAPI_MakeBox

from OCC.STEPControl import STEPControl_Writer, STEPControl_AsIs 

THICKNESS = 1.5
HEIGHT = 30
BENCH_HEIGHT = 18

def Specs(**kwargs):
    return namedtuple('Specs', ' '.join(kwargs.keys()))(**kwargs)

SPECS = Specs(
    width=42.,
    length=95.,
    leg_width_inset=10., # distance from long edge to edge of leg
    leg_length_inset=24., # distance from short edge to center of leg
    leg_base_width_over=3.,
    leg_base_length_over=1.5,
    split_top=False,
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
        SPLIT = 0.5
        side_0 = _box(SPECS.length, SPECS.width / 2 - SPLIT / 2, THICKNESS)
        side_1 = _box(SPECS.length, SPECS.width / 2 - SPLIT / 2, THICKNESS)
        _move(side_1, 0, SPECS.width / 2 + SPLIT / 2, 0)
        top = _combine(side_0, side_1)
    else:
        top = _box(SPECS.length, SPECS.width, THICKNESS)
    return _move(top, 0, 0, HEIGHT - THICKNESS)

def _make_table():
    top = _make_table_top()
    leg_0 = _make_table_leg()
    leg_1 = _make_table_leg()
    spanner = _box(
        SPECS.length - SPECS.leg_length_inset * 2 - THICKNESS,
        THICKNESS,
        6.)
    _move(spanner,
          SPECS.leg_length_inset + THICKNESS / 2,
          SPECS.width / 2 - THICKNESS / 2,
          HEIGHT - THICKNESS * 2 - 6.)
    leg_base_inset = SPECS.leg_length_inset - THICKNESS / 2 - \
        SPECS.leg_base_length_over
    _move(leg_0,
          leg_base_inset,
          SPECS.leg_width_inset - SPECS.leg_base_width_over,
          0)
    _move(leg_1,
          SPECS.length - leg_base_inset - THICKNESS - SPECS.leg_base_length_over * 2,
          SPECS.leg_width_inset - SPECS.leg_base_width_over,
          0)
    return _combine(top, leg_0, leg_1, spanner)

def _make_bench():
    top = _box(SPECS.length, SPECS.bench_width, THICKNESS)
    leg_0 = _box(THICKNESS, SPECS.bench_width, BENCH_HEIGHT - THICKNESS)
    leg_1 = _box(THICKNESS, SPECS.bench_width, BENCH_HEIGHT - THICKNESS)
    spanner = _box(
        SPECS.length - SPECS.bench_leg_inset * 2 - THICKNESS * 2,
        THICKNESS, 6.)
    _move(spanner,
          SPECS.bench_leg_inset + THICKNESS,
          SPECS.bench_width / 2 - THICKNESS / 2,
          BENCH_HEIGHT - THICKNESS - 6.)
    _move(leg_0, SPECS.bench_leg_inset, 0, 0)
    _move(leg_1, SPECS.length - SPECS.bench_leg_inset - THICKNESS, 0, 0)
    _move(top, 0, 0, BENCH_HEIGHT - THICKNESS)
    return _combine(top, leg_0, leg_1, spanner)


table = _make_table()
bench = _make_bench()
_move(bench, 0, SPECS.width - 2, 0)
whole_thing = _combine(table, bench)

if len(sys.argv) > 1 and sys.argv[1] == 'json':
    html_dir = os.path.join(os.path.dirname(__file__), 'html')
    tess = Tesselator(whole_thing)
    tess.Compute(compute_edges=False, mesh_quality=1.)
    with open(os.path.join(html_dir, "table.json"), 'w') as f:
        f.write(tess.ExportShapeToThreejsJSONString('table'))
else:
    display, start_display, _, _ = init_display()
    display.DisplayShape(whole_thing, update=True)
    start_display()
