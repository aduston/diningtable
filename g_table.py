from collections import namedtuple
from OCC import gp, TopLoc
from OCC.Display.SimpleGui import init_display
from OCC.TopoDS import TopoDS_Builder, TopoDS_Compound
from OCC.BRepPrimAPI import BRepPrimAPI_MakeBox

from OCC.STEPControl import STEPControl_Writer, STEPControl_AsIs 

TABLE_THICKNESS = 1.5
PEDESTAL_HEIGHT = 28.5

def Specs(**kwargs):
    return namedtuple('Specs', ' '.join(kwargs.keys()))(**kwargs)

SPECS = Specs(
    width=40.,
    length=99.,
    pedestal_inset=16.,
    pedestal_width=10.,
    pedestal_thickness=3.,
    pedestal_gap=1.0
)

def _move(shape, x, y, z):
    tr = gp.gp_Trsf()
    tr.SetTranslation(gp.gp_Vec(x, y, z))
    loc = TopLoc.TopLoc_Location(tr)
    shape.Move(loc)

_box = lambda *args: BRepPrimAPI_MakeBox(*args).Shape()

def _make_table():
    builder = TopoDS_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    table_top = _box(SPECS.length, SPECS.width, TABLE_THICKNESS)
    _move(table_top, 0, 0, PEDESTAL_HEIGHT)
    builder.Add(compound, table_top)
    for i in range(4):
        pedestal = _box(SPECS.pedestal_thickness, SPECS.pedestal_width, PEDESTAL_HEIGHT)
        if i < 2:
            x = SPECS.pedestal_inset
        else:
            x = SPECS.length - SPECS.pedestal_inset - SPECS.pedestal_thickness
        if i % 2 == 0:
            y = (SPECS.width + SPECS.pedestal_gap) / 2
        else:
            y = (SPECS.width - SPECS.pedestal_gap) / 2 - SPECS.pedestal_width
        _move(pedestal, x, y, 0.)
        builder.Add(compound, pedestal)
    return compound

def _write_step(table):
    step_writer = STEPControl_Writer()
    step_writer.Transfer(table, STEPControl_AsIs)
    status = step_writer.Write("table.stp")


table = _make_table()

# _write_step(table)

display, start_display, _, _ = init_display()
display.DisplayShape(table, update=True)
start_display()
