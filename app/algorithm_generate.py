# layout_engine.py

import copy

GRID_SIZE = 50


# =========================
# Mock Data
# =========================

def mock_space():
    space = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]

    # A test region
    for i in range(20, 35):
        for j in range(20, 35):
            space[i][j] = 1

    return space


def mock_modules():
    """
    Modules are already expanded, and each has a type.
    """
    return [
        {"id": 1, "type": "pen",  "w": 2, "h": 2},
        {"id": 2, "type": "pen",  "w": 2, "h": 3},
        {"id": 3, "type": "tray", "w": 4, "h": 6},
        {"id": 4, "type": "tray", "w": 5, "h": 7},
    ]


def mock_space_2():
    """
    Irregular space: an L-shape with a rectangular notch cut from the
    top-right corner — tests that the algorithm respects non-rectangular
    boundaries and still packs modules tightly.

    Shape (each cell = 1 grid unit, origin at top-left of the 50x50 grid):

        columns 5-16
        +------------+
        |  top bar   |  rows 5-9   (12 wide x 5 tall)
        |      +-----+
        | left |       rows 10-12  (notch: right 6 cols removed)
        +--+---+
        |  stem |      rows 13-20  (6 wide x 8 tall, cols 5-10)
        +--+----+
    """
    space = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    # Wide top bar: rows 5-9, cols 5-16
    for i in range(5, 10):
        for j in range(5, 17):
            space[i][j] = 1

    # Middle section with notch: rows 10-12, cols 5-10 only
    for i in range(10, 13):
        for j in range(5, 11):
            space[i][j] = 1

    # Narrow bottom stem: rows 13-20, cols 5-10
    for i in range(13, 21):
        for j in range(5, 11):
            space[i][j] = 1

    return space


def mock_modules_2():
    """
    A mix of modules sized to exercise the smaller irregular space:
    the wide tray fits only in the top bar; smaller pieces fill the stem.
    """
    return [
        {"id": 1, "type": "pen",  "w": 2, "h": 2},
        {"id": 2, "type": "pen",  "w": 2, "h": 2},
        {"id": 3, "type": "tray", "w": 4, "h": 3},  # fits only in wide top bar
        {"id": 4, "type": "sd",   "w": 3, "h": 2},
        {"id": 5, "type": "sd",   "w": 2, "h": 2},
        {"id": 6, "type": "pen",  "w": 2, "h": 2},
        {"id": 7, "type": "pen",  "w": 2, "h": 3},
        {"id": 8, "type": "tray", "w": 4, "h": 6},
        {"id": 9, "type": "tray", "w": 5, "h": 7},
        {"id": 10, "type": "sd",   "w": 3, "h": 2},
        {"id": 11, "type": "pen",  "w": 2, "h": 2},
        {"id": 12, "type": "pen",  "w": 2, "h": 3},
        {"id": 13, "type": "tray", "w": 4, "h": 6},
        {"id": 14, "type": "tray", "w": 5, "h": 7},
        {"id": 15, "type": "sd",   "w": 3, "h": 2},
        {"id": 16, "type": "pen",  "w": 2, "h": 2},
        {"id": 17, "type": "pen",  "w": 2, "h": 3},
        {"id": 18, "type": "tray", "w": 4, "h": 6},
        {"id": 19, "type": "tray", "w": 5, "h": 7},
        {"id": 20, "type": "sd",   "w": 3, "h": 2},
    ]


# =========================
# Core Algorithm  (greedy — no backtracking)
# =========================

def generate_layout(space, module_list, preplaced=None):
    """
    Greedy layout engine — maximises side contact.

    Strategy:
      1. Sort modules by type, then by descending area (largest first).
      2. For each module, score every valid (orientation, position) pair by the
         number of footprint-boundary edges that touch an already-occupied cell
         (contact score).  Higher score = more sides shared = better engagement.
      3. Cluster constraint: subsequent modules of the same type only consider
         cells on the frontier of that type, keeping same-type modules together.
      4. Pick the highest-scoring valid position.  Ties are broken by row-major
         order so output is deterministic — O(modules × cells).

    preplaced: placements whose cells are treated as occupied for scoring and
    collision, but not included in the returned placements.
    """

    grid     = [[0]    * GRID_SIZE for _ in range(GRID_SIZE)]
    type_map = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]

    module_list = sorted(
        module_list,
        key=lambda m: (m["type"], -(m["w"] * m["h"]))
    )

    placements   = []
    placed_types = {}                # type -> placed count
    type_frontier = {}               # type -> set of candidate (x, y) anchors
    unplaced     = []                # modules that could not be placed

    # Precompute valid cells once
    valid_cells = [
        (i, j)
        for i in range(GRID_SIZE)
        for j in range(GRID_SIZE)
        if space[i][j] == 1
    ]

    def can_place(rw, rh, x, y):
        if x + rh > GRID_SIZE or y + rw > GRID_SIZE:
            return False
        for i in range(rh):
            for j in range(rw):
                if space[x+i][y+j] == 0 or grid[x+i][y+j] == 1:
                    return False
        return True

    def contact_score(rw, rh, x, y) -> int:
        """
        Count how many outer-boundary edges of the footprint at (x, y)
        are directly adjacent to an already-occupied cell.
        More shared edges = tighter packing = higher score.
        """
        score = 0
        for i in range(rh):
            for j in range(rw):
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + i + dx, y + j + dy
                    # Only count neighbours outside the footprint itself
                    if 0 <= nx < x + rh and x <= nx and 0 <= ny < y + rw and y <= ny:
                        continue  # still inside the footprint — skip
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if grid[nx][ny] == 1:
                            score += 1
        return score

    def do_place(rw, rh, x, y, mtype):
        for i in range(rh):
            for j in range(rw):
                grid[x+i][y+j]     = 1
                type_map[x+i][y+j] = mtype
        # Expand frontier: neighbours of the newly placed footprint
        frontier = type_frontier.setdefault(mtype, set())
        for i in range(rh):
            for j in range(rw):
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x+i+dx, y+j+dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if grid[nx][ny] == 0 and space[nx][ny] == 1:
                            frontier.add((nx, ny))

    if preplaced:
        for p in preplaced:
            do_place(p["w"], p["h"], p["x"], p["y"], p["type"])
            placed_types[p["type"]] = placed_types.get(p["type"], 0) + 1

    # ---------- greedy placement ----------
    for module in module_list:
        mtype = module["type"]
        w, h  = module["w"], module["h"]
        placed_types.setdefault(mtype, 0)

        # Collect all valid (score, rw, rh, x, y) candidates across both orientations
        best = None  # (score, rw, rh, x, y)

        for (rw, rh) in [(w, h), (h, w)]:
            # First module of its type → try all valid cells
            # Subsequent modules     → only frontier cells (adjacent to same type)
            if placed_types[mtype] == 0:
                candidates = valid_cells
            else:
                candidates = sorted(type_frontier.get(mtype, set()))

            for (x, y) in candidates:
                if not can_place(rw, rh, x, y):
                    continue
                score = contact_score(rw, rh, x, y)
                # Keep the highest-scoring candidate; row-major order breaks ties
                if best is None or score > best[0]:
                    best = (score, rw, rh, x, y)

        if best is not None:
            _, rw, rh, x, y = best
            do_place(rw, rh, x, y, mtype)
            placements.append({
                "id":   module["id"],
                "type": mtype,
                "x":    x,
                "y":    y,
                "w":    rw,
                "h":    rh,
            })
            placed_types[mtype] += 1
        else:
            unplaced.append(module)

    return placements, unplaced


# =========================
# Visualization
# =========================

def print_layout(space, placements, row_range=(20, 40), col_range=(20, 40)):
    grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]

    for p in placements:
        for i in range(p["h"]):
            for j in range(p["w"]):
                grid[p["x"]+i][p["y"]+j] = 1

    print("\n=== Layout Preview ===")

    for i in range(*row_range):
        row = ""
        for j in range(*col_range):
            if space[i][j] == 0:
                row += " "
            else:
                row += "█" if grid[i][j] else "."
        print(row)


# =========================
# Main
# =========================

if __name__ == "__main__":

    def run_test(label, space, modules, row_range, col_range):
        print("\n" + "="*40)
        print(label)
        print("="*40)
        result, failed = generate_layout(space, modules)
        if failed:
            print(f"\n⚠️  LAYOUT FAILED — {len(failed)} module(s) could not be placed:")
            for m in failed:
                print(f"  - id={m['id']} type={m['type']} size={m['w']}x{m['h']}")
            print("Layout aborted. No placements displayed.")
            return
        print("\n=== Placements ===")
        for r in result:
            print(r)
        print(f"\n✅ All {len(result)} modules placed successfully.")
        print_layout(space, result, row_range=row_range, col_range=col_range)

    # ── Test 1: regular square space ──
    run_test("Test 1: Regular square space",
             mock_space(), mock_modules(),
             row_range=(20, 40), col_range=(20, 40))

    # ── Test 2: irregular L-shape with notch ──
    run_test("Test 2: Irregular L-shape with notch",
             mock_space_2(), mock_modules_2(),
             row_range=(3, 24), col_range=(3, 20))