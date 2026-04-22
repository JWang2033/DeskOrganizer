import cadquery as cq

LID_THICKNESS = 2.0
LIP_DEPTH = 1.5
WALL_THICKNESS = 1.5
TOLERANCE = 0.3


def make_tray_lid(
    units_x: int,
    units_y: int,
    lid_thickness: float = LID_THICKNESS,
    lip_depth: float = LIP_DEPTH,
    wall_thickness: float = WALL_THICKNESS,
    tolerance: float = TOLERANCE,
    export_path: str | None = None,
) -> cq.Workplane:
    """Build a tray lid: flat top plate matching the tray footprint plus an
    inner lip that drops into the tray opening for a friction fit.
    """
    L = units_x * 10.0
    W = units_y * 10.0

    plate = cq.Workplane("XY").box(L, W, lid_thickness, centered=(True, True, False))

    lip_l = L - 2 * wall_thickness - 2 * tolerance
    lip_w = W - 2 * wall_thickness - 2 * tolerance
    lip = (
        cq.Workplane("XY")
        .box(lip_l, lip_w, lip_depth, centered=(True, True, False))
        .translate((0, 0, -lip_depth))
    )

    result = plate.union(lip)

    if export_path:
        cq.exporters.export(result, export_path)

    return result


if __name__ == "__main__":
    make_tray_lid(units_x=4, units_y=4, export_path="tray_lid.stl")
