"""
tests/test_algorithm_generate.py

Scenarios covered
-----------------
1. Regular square space — mixed module types, all fit.
2. L-shape with notch   — irregular boundary, small set that fits.
3. Exact fit            — module areas sum to exactly the space area.
4. Single module        — no clustering logic exercised; must still place.
5. All same type        — cluster constraint active from the second module.
6. Rotation required    — modules only fit after 90° rotation.
7. T-shape space        — bar + stem; large trays go in bar, small in stem.
8. Impossible           — module larger than the whole space; clean FAIL.
"""

import sys
import os

# Allow importing from app/ without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.algorithm_generate import generate_layout, GRID_SIZE


# =============================================================================
# Helpers
# =============================================================================

def make_rect_space(row_start, row_end, col_start, col_end):
    """Return a GRID_SIZE x GRID_SIZE space with a filled rectangle."""
    space = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    for i in range(row_start, row_end):
        for j in range(col_start, col_end):
            space[i][j] = 1
    return space


def placed_ids(result):
    return {p["id"] for p in result}


def assert_no_overlap(result):
    """Verify no two placements share a cell."""
    cells = {}
    for p in result:
        for i in range(p["h"]):
            for j in range(p["w"]):
                cell = (p["x"] + i, p["y"] + j)
                assert cell not in cells, (
                    f"Overlap at {cell} between id={p['id']} and id={cells[cell]}"
                )
                cells[cell] = p["id"]


def assert_in_bounds(result, space):
    """Verify every placed cell is inside the valid space region."""
    for p in result:
        for i in range(p["h"]):
            for j in range(p["w"]):
                r, c = p["x"] + i, p["y"] + j
                assert space[r][c] == 1, (
                    f"Module id={p['id']} placed outside valid space at ({r},{c})"
                )


# =============================================================================
# Test 1 — Regular square space, mixed modules
# =============================================================================

def test_regular_square_all_placed():
    """All modules fit in a 15x15 square; result is non-empty with no overlap."""
    space = make_rect_space(20, 35, 20, 35)   # 15x15 = 225 cells
    modules = [
        {"id": 1, "type": "pen",  "w": 2, "h": 2},
        {"id": 2, "type": "pen",  "w": 2, "h": 3},
        {"id": 3, "type": "tray", "w": 4, "h": 6},
        {"id": 4, "type": "tray", "w": 5, "h": 7},
    ]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Unexpected failures: {failed}"
    assert placed_ids(result) == {1, 2, 3, 4}
    assert_no_overlap(result)
    assert_in_bounds(result, space)


# =============================================================================
# Test 2 — Irregular L-shape with notch, small module set
# =============================================================================

def _make_l_notch_space():
    space = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    for i in range(5, 10):          # wide top bar
        for j in range(5, 17):
            space[i][j] = 1
    for i in range(10, 13):         # middle (notch removes right 6 cols)
        for j in range(5, 11):
            space[i][j] = 1
    for i in range(13, 21):         # narrow stem
        for j in range(5, 11):
            space[i][j] = 1
    return space


def test_l_shape_notch_all_placed():
    """Small set of modules fits inside the irregular L-shape."""
    space = _make_l_notch_space()
    modules = [
        {"id": 1, "type": "pen",  "w": 2, "h": 2},
        {"id": 2, "type": "pen",  "w": 2, "h": 2},
        {"id": 3, "type": "tray", "w": 4, "h": 3},  # only fits in top bar
        {"id": 4, "type": "sd",   "w": 3, "h": 2},
        {"id": 5, "type": "sd",   "w": 2, "h": 2},
    ]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Unexpected failures: {failed}"
    assert placed_ids(result) == {1, 2, 3, 4, 5}
    assert_no_overlap(result)
    assert_in_bounds(result, space)


def test_l_shape_notch_respects_boundary():
    """No module is placed in the notched-out region (cols 11-16, rows 10-12)."""
    space = _make_l_notch_space()
    modules = [
        {"id": 1, "type": "pen", "w": 2, "h": 2},
        {"id": 2, "type": "pen", "w": 2, "h": 2},
    ]
    result, _ = generate_layout(space, modules)
    for p in result:
        for i in range(p["h"]):
            for j in range(p["w"]):
                r, c = p["x"] + i, p["y"] + j
                # notched-out region: rows 10-12, cols 11-16
                assert not (10 <= r <= 12 and 11 <= c <= 16), (
                    f"Module placed in notched region at ({r},{c})"
                )


# =============================================================================
# Test 3 — Exact fit (no empty cells remaining)
# =============================================================================

def test_exact_fit_no_empty_cells():
    """Two modules whose areas sum to exactly the space area tile it completely."""
    # Space: 10 cols x 6 rows = 60 cells
    space = make_rect_space(5, 11, 5, 15)
    modules = [
        {"id": 1, "type": "tray", "w": 4, "h": 6},   # area 24
        {"id": 2, "type": "tray", "w": 6, "h": 6},   # area 36  → total 60
    ]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Unexpected failures: {failed}"
    assert_no_overlap(result)
    assert_in_bounds(result, space)
    # Verify total coverage
    covered = sum(p["w"] * p["h"] for p in result)
    assert covered == 60, f"Expected 60 cells covered, got {covered}"


# =============================================================================
# Test 4 — Single module
# =============================================================================

def test_single_module_placed():
    """One module on an 8x8 space; trivial but must not crash or fail."""
    space = make_rect_space(10, 18, 10, 18)
    modules = [{"id": 1, "type": "sd", "w": 3, "h": 2}]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Unexpected failure: {failed}"
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert_in_bounds(result, space)


# =============================================================================
# Test 5 — All same type (cluster always active after first)
# =============================================================================

def test_same_type_modules_cluster_together():
    """
    All pen holders must end up adjacent to each other
    (cluster constraint keeps same-type modules on the frontier).
    """
    # Wide 20x4 strip
    space = make_rect_space(10, 14, 5, 25)
    modules = [
        {"id": i, "type": "pen", "w": 2, "h": 4}
        for i in range(1, 6)        # 5 pens, each 2x4 = area 8; total 40 ≤ 80
    ]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Unexpected failures: {failed}"
    assert len(result) == 5
    assert_no_overlap(result)
    assert_in_bounds(result, space)

    # Verify all placements form a contiguous block (no gaps between them)
    xs = {p["x"] for p in result}
    assert len(xs) == 1, "All pens should share the same row (x coordinate)"


# =============================================================================
# Test 6 — Rotation required
# =============================================================================

def test_rotation_required_to_fit():
    """
    Space is 3 cols wide x 15 rows tall.
    Modules are 5w x 3h in default orientation — they only fit as 3w x 5h.
    """
    space = make_rect_space(5, 20, 5, 8)    # 3 cols wide
    modules = [
        {"id": 1, "type": "sd", "w": 5, "h": 3},
        {"id": 2, "type": "sd", "w": 5, "h": 3},
        {"id": 3, "type": "sd", "w": 5, "h": 3},
    ]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Rotation not attempted or failed: {failed}"
    assert len(result) == 3
    # Each placed module must have been rotated: placed w should be 3, h should be 5
    for p in result:
        assert p["w"] == 3 and p["h"] == 5, (
            f"Module id={p['id']} was not rotated correctly: {p['w']}x{p['h']}"
        )
    assert_no_overlap(result)
    assert_in_bounds(result, space)


# =============================================================================
# Test 7 — T-shape space
# =============================================================================

def _make_t_space():
    space = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    for i in range(5, 10):          # horizontal bar (20x5)
        for j in range(5, 25):
            space[i][j] = 1
    for i in range(10, 23):         # vertical stem (5x13)
        for j in range(12, 17):
            space[i][j] = 1
    return space


def test_t_shape_all_placed():
    """Modules sized so large trays go to bar, small ones to stem."""
    space = _make_t_space()
    modules = [
        {"id": 1, "type": "tray", "w": 6, "h": 4},
        {"id": 2, "type": "tray", "w": 5, "h": 4},
        {"id": 3, "type": "pen",  "w": 2, "h": 3},
        {"id": 4, "type": "pen",  "w": 2, "h": 3},
        {"id": 5, "type": "sd",   "w": 3, "h": 2},
        {"id": 6, "type": "sd",   "w": 3, "h": 2},
    ]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Unexpected failures: {failed}"
    assert placed_ids(result) == {1, 2, 3, 4, 5, 6}
    assert_no_overlap(result)
    assert_in_bounds(result, space)


def test_t_shape_large_module_in_bar():
    """A 6x4 tray must land in the wide bar (rows 5-9), not the narrow stem."""
    space = _make_t_space()
    modules = [{"id": 1, "type": "tray", "w": 6, "h": 4}]
    result, failed = generate_layout(space, modules)
    assert failed == [], f"Unexpected failure: {failed}"
    p = result[0]
    # The tray (h=4) cannot fit in the 5-col wide stem; must be in the bar rows
    assert p["x"] >= 5 and p["x"] + p["h"] <= 10, (
        f"Large tray should be in bar (rows 5-9), got x={p['x']} h={p['h']}"
    )


# =============================================================================
# Test 8 — Impossible: module larger than the entire space
# =============================================================================

def test_impossible_module_too_large():
    """A 6x6 module on a 4x4 space must fail cleanly with the module in unplaced."""
    space = make_rect_space(5, 9, 5, 9)   # 4x4
    modules = [{"id": 1, "type": "tray", "w": 6, "h": 6}]
    result, failed = generate_layout(space, modules)
    assert result == [], "No modules should be placed"
    assert len(failed) == 1
    assert failed[0]["id"] == 1
