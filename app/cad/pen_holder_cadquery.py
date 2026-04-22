import math
import cadquery as cq

# Geometry defaults
CELL_SIZE = 20.0        # Base unit footprint per pen (X and Y)
HOLDER_HEIGHT = 70.0    # Total height
SLOT_DIAMETER = 15.0    # Pen slot diameter (per spec)
FLOOR_THICKNESS = 5.0   # Material left under slots so pens don't touch desk


def make_pen_holder(
    num_pens: int,
    num_rows: int,
    cell_size: float = CELL_SIZE,
    holder_height: float = HOLDER_HEIGHT,
    slot_diameter: float = SLOT_DIAMETER,
    floor_thickness: float = FLOOR_THICKNESS,
    export_path: str | None = None,
) -> cq.Workplane:
    """Build a rectangular pen holder with circular slots.

    num_pens does not need to divide evenly into num_rows; extra cells are
    left solid (no hole) in row-major order.
    """
    if num_pens < 1 or num_rows < 1:
        raise ValueError("num_pens and num_rows must be >= 1")

    cols = math.ceil(num_pens / num_rows)
    outer_x = cols * cell_size
    outer_y = num_rows * cell_size
    slot_depth = holder_height - floor_thickness

    result = cq.Workplane("XY").box(
        outer_x, outer_y, holder_height, centered=(False, False, False)
    )

    slot_points = []
    for i in range(num_pens):
        row, col = i // cols, i % cols
        slot_points.append(
            (col * cell_size + cell_size / 2, row * cell_size + cell_size / 2)
        )

    result = (
        result.faces(">Z").workplane()
        .pushPoints(slot_points)
        .circle(slot_diameter / 2)
        .cutBlind(-slot_depth)
    )

    # ADD MAGNET HOLES
    mag_dia = 3.4
    mag_r = mag_dia / 2.0
    mag_depth = 1.2
    z_level = 11.0

    num_holes_y = int(outer_y / 10.0) - 1
    num_holes_x = int(outer_x / 10.0) - 1

    y_centers = [10.0 + i * 10.0 for i in range(num_holes_y)]
    x_centers = [10.0 + i * 10.0 for i in range(num_holes_x)]

    if y_centers:
        pts = [(y, z_level) for y in y_centers]
        right_holes = cq.Workplane("YZ").workplane(offset=outer_x).pushPoints(pts).circle(mag_r).extrude(-mag_depth)
        result = result.cut(right_holes)
        left_holes = cq.Workplane("YZ").workplane(offset=0).pushPoints(pts).circle(mag_r).extrude(mag_depth)
        result = result.cut(left_holes)

    if x_centers:
        pts = [(x, z_level) for x in x_centers]
        front_holes = cq.Workplane("XZ").workplane(offset=-outer_y).pushPoints(pts).circle(mag_r).extrude(mag_depth)
        result = result.cut(front_holes)
        back_holes = cq.Workplane("XZ").workplane(offset=0).pushPoints(pts).circle(mag_r).extrude(-mag_depth)
        result = result.cut(back_holes)

    if export_path:
        cq.exporters.export(result, export_path)

    return result


if __name__ == "__main__":
    make_pen_holder(num_pens=10, num_rows=2, export_path="pen_holder.stl")
