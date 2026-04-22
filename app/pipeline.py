"""Pipeline: UI payload -> sized modules -> layout algorithm -> positioned CAD.

Coordinate conventions:
- Algorithm grid uses (x=row, y=col); w=column-extent, h=row-extent.
- CAD uses (x=horizontal, y=vertical). A cell is 10mm.
- Mapping: cad_x = placement.y * 10, cad_y = placement.x * 10.
"""

import math
import cadquery as cq

from app.algorithm_generate import GRID_SIZE, generate_layout
from app.cad.pen_holder_cadquery import make_pen_holder
from app.cad.sd_holder_cadquery import make_sd_holder
from app.cad.storage_tray import storage_tray
from app.cad.tray_lid import LID_THICKNESS, make_tray_lid

CELL_MM = 10
TRAY_HEIGHT_MM = {"short": 30, "high": 80}
LEVEL_STEP_MM = 33


def pen_rows(num_pens: int) -> int:
    if num_pens <= 1:
        return 1
    if num_pens <= 4:
        return 2
    return 3


def _bbox_cells(workplane: cq.Workplane) -> tuple[int, int]:
    bb = workplane.val().BoundingBox()
    return math.ceil(bb.xlen / CELL_MM), math.ceil(bb.ylen / CELL_MM)


def _to_positive_octant(cad: cq.Workplane) -> cq.Workplane:
    """Shift a shape so its bounding box starts at (0, 0, 0)."""
    bb = cad.val().BoundingBox()
    return cad.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def build_space(available_space: list[list[int]], grid_size: int = GRID_SIZE) -> list[list[int]]:
    grid = [[0] * grid_size for _ in range(grid_size)]
    for cell in available_space:
        r, c = cell[0], cell[1]
        if 0 <= r < grid_size and 0 <= c < grid_size:
            grid[r][c] = 1
    return grid


def build_modules(items, trays) -> list[dict]:
    """Build each module's CAD and compute its grid footprint.

    Returns a list of dicts with keys: id, type, w, h, cad.
    The CAD is pre-shifted so its bbox starts at (0, 0, 0), ready to translate.
    """
    modules: list[dict] = []
    next_id = 1

    if items.pens > 0:
        rows = pen_rows(items.pens)
        cad = make_pen_holder(num_pens=items.pens, num_rows=rows)
        cad = _to_positive_octant(cad)
        w, h = _bbox_cells(cad)
        modules.append({"id": next_id, "type": "pen", "w": w, "h": h, "cad": cad})
        next_id += 1

    if items.standardSD + items.microSD > 0:
        cad = make_sd_holder(
            num_small_slots=items.microSD,
            num_large_slots=items.standardSD,
        )
        cad = _to_positive_octant(cad)
        w, h = _bbox_cells(cad)
        modules.append({"id": next_id, "type": "sd", "w": w, "h": h, "cad": cad})
        next_id += 1

    for tray in trays:
        height_mm = TRAY_HEIGHT_MM.get(tray.height, 30)
        units_z = max(3, int(height_mm / 10))
        cad, _ = storage_tray(
            unitsX=tray.length, unitsY=tray.width, unitsZ=units_z,
            div_x=tray.divX, div_y=tray.divY,
        )
        cad = _to_positive_octant(cad)
        w, h = _bbox_cells(cad)
        modules.append({
            "id": next_id, "type": "tray", "w": w, "h": h, "cad": cad,
            "tray_height": tray.height,
        })
        next_id += 1

    return modules


def _rotate_90(cad: cq.Workplane) -> cq.Workplane:
    rotated = cad.rotate((0, 0, 0), (0, 0, 1), 90)
    return _to_positive_octant(rotated)


def position_modules(modules: list[dict], placements: list[dict]) -> list[dict]:
    """Translate each module's CAD to its placed grid position.

    Returns a list of dicts: {id, type, placement, cad}.
    """
    by_id = {m["id"]: m for m in modules}
    positioned: list[dict] = []

    for p in placements:
        m = by_id[p["id"]]
        cad = m["cad"]

        # If algorithm rotated the module, rotate the CAD 90° around Z.
        if (p["w"], p["h"]) != (m["w"], m["h"]):
            cad = _rotate_90(cad)

        # Algorithm (x=row, y=col) -> CAD (cad_x=col*10, cad_y=row*10).
        cad_x = p["y"] * CELL_MM
        cad_y = p["x"] * CELL_MM
        cad_z = p.get("level", 0) * LEVEL_STEP_MM
        cad = cad.translate((cad_x, cad_y, cad_z))

        positioned.append({
            "id": m["id"],
            "type": m["type"],
            "placement": p,
            "cad": cad,
        })

    return positioned


def combine(positioned: list[dict]) -> cq.Workplane | None:
    combined = None
    for entry in positioned:
        combined = entry["cad"] if combined is None else combined.union(entry["cad"])
    return combined


def _space_from_placements(placements: list[dict], stackable_ids: set, grid_size: int = GRID_SIZE) -> list[list[int]]:
    """Build an available_space grid from the footprints of given placed modules."""
    grid = [[0] * grid_size for _ in range(grid_size)]
    for p in placements:
        if p["id"] not in stackable_ids:
            continue
        for i in range(p["h"]):
            for j in range(p["w"]):
                r, c = p["x"] + i, p["y"] + j
                if 0 <= r < grid_size and 0 <= c < grid_size:
                    grid[r][c] = 1
    return grid


def _footprint_overlaps(a: dict, b: dict) -> bool:
    return not (
        a["x"] + a["h"] <= b["x"] or b["x"] + b["h"] <= a["x"]
        or a["y"] + a["w"] <= b["y"] or b["y"] + b["w"] <= a["y"]
    )


def build_tray_lids(placements: list[dict], short_tray_ids: set) -> list[dict]:
    """Generate a positioned lid for every short tray that has a module stacked on top."""
    by_level: dict[int, list[dict]] = {}
    for p in placements:
        by_level.setdefault(p.get("level", 0), []).append(p)

    lids: list[dict] = []
    for p in placements:
        if p["id"] not in short_tray_ids:
            continue
        level = p.get("level", 0)
        upper = by_level.get(level + 1, [])
        if not any(_footprint_overlaps(p, u) for u in upper):
            continue

        lid_cad = make_tray_lid(units_x=p["w"], units_y=p["h"])
        cx = p["y"] * CELL_MM + p["w"] * CELL_MM / 2
        cy = p["x"] * CELL_MM + p["h"] * CELL_MM / 2
        cz = level * LEVEL_STEP_MM + (LEVEL_STEP_MM - LID_THICKNESS)
        lid_cad = lid_cad.translate((cx, cy, cz))

        lids.append({
            "id": p["id"],
            "type": "lid",
            "placement": p,
            "cad": lid_cad,
        })

    return lids


def _pack_one_level(space: list[list[int]], module_list: list[dict], short_tray_ids: set) -> tuple[list[dict], list[dict]]:
    """Pack modules onto one level, with a short-trays-first fallback."""
    placed, unplaced = generate_layout(space, module_list)
    if not unplaced:
        return placed, unplaced

    short_trays = [m for m in module_list if m["id"] in short_tray_ids]
    if not short_trays:
        return placed, unplaced

    rest = [m for m in module_list if m["id"] not in short_tray_ids]
    trays_placed, trays_unplaced = generate_layout(space, short_trays)
    rest_placed, rest_unplaced = generate_layout(
        space, rest + trays_unplaced, preplaced=trays_placed
    )
    return trays_placed + rest_placed, rest_unplaced


def run_pipeline(items, trays, available_space) -> dict:
    modules = build_modules(items, trays)
    short_tray_ids = {m["id"] for m in modules if m["type"] == "tray" and m.get("tray_height") == "short"}

    pending = [
        {"id": m["id"], "type": m["type"], "w": m["w"], "h": m["h"]}
        for m in modules
    ]
    space = build_space(available_space)

    all_placements: list[dict] = []
    level = 0
    while pending:
        placed, pending = _pack_one_level(space, pending, short_tray_ids)
        for p in placed:
            p["level"] = level
        all_placements.extend(placed)

        if not pending or not any(p["id"] in short_tray_ids for p in placed):
            break
        space = _space_from_placements(placed, short_tray_ids)
        level += 1

    positioned = position_modules(modules, all_placements)
    positioned.extend(build_tray_lids(all_placements, short_tray_ids))
    combined = combine(positioned)

    return {
        "placements": all_placements,
        "modules": positioned,
        "combined": combined,
        "unplaced": pending,
    }
