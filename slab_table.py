from collections import namedtuple
from OCC import gp, TopLoc
from OCC.Display.SimpleGui import init_display
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
    leg_width_inset=8., # distance from log edge to edge of leg
    leg_length_inset=24., # distance from short edge to center of leg
    leg_base_width_over=3.,
    leg_base_length_over=1.5,
    split_top=True
)

def _move(shape, x, y, z):
    tr = gp.gp_Trsf()
    tr.SetTranslation(gp.gp_Vec(x, y, z))
    loc = TopLoc.TopLoc_Location(tr)
    shape.Move(loc)

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
        HEIGHT - THICKNESS * 3)
    _move(leg,
          SPECS.leg_base_length_over,
          SPECS.leg_base_width_over,
          THICKNESS)
    return _combine(leg_base, leg)

def _make_table_top():
    if SPECS.split_top:
        SPLIT = 0.5
        side_0 = _box(SPECS.length, SPECS.width / 2 - SPLIT / 2, THICKNESS)
        side_1 = _box(SPECS.length, SPECS.width / 2 - SPLIT / 2, THICKNESS)
        _move(side_1, 0, SPECS.width / 2 + SPLIT / 2, 0)
        return _combine(side_0, side_1)
    else:
        return _box(SPECS.length, SPECS.width, THICKNESS)

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
          THICKNESS * 2)
    leg_base_inset = SPECS.leg_length_inset - THICKNESS / 2 - \
        SPECS.leg_base_length_over / 2
    _move(leg_0,
          leg_base_inset,
          SPECS.leg_width_inset - SPECS.leg_base_width_over,
          THICKNESS)
    _move(leg_1,
          SPECS.length - leg_base_inset - THICKNESS - SPECS.leg_base_length_over * 2,
          SPECS.leg_width_inset - SPECS.leg_base_width_over,
          THICKNESS)
    return _combine(top, leg_0, leg_1, spanner)

table = _make_table()

display, start_display, _, _ = init_display()
display.DisplayShape(table, update=True)
start_display()
