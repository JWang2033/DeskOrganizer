# layout_engine.py

import copy

GRID_SIZE = 50


# =========================
# Mock Data
# =========================

def mock_space():
    space = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]

    # 一个测试区域
    for i in range(20, 35):
        for j in range(20, 35):
            space[i][j] = 1

    return space


def mock_modules():
    """
    module 已经是展开后的，每个有 type
    """
    return [
        {"id": 1, "type": "pen", "w": 2, "h": 2},
        {"id": 2, "type": "pen", "w": 2, "h": 3},
        {"id": 3, "type": "tray", "w": 4, "h": 6},
        {"id": 4, "type": "tray", "w": 5, "h": 7},
        {"id": 5, "type": "sd", "w": 3, "h": 2},
    ]


# =========================
# Core Algorithm  (greedy — no backtracking)
# =========================

def generate_layout(space, module_list):
    """
    Greedy layout engine.

    Strategy:
      1. Sort modules by type, then by descending area (largest first).
      2. For each module try both orientations and scan candidate cells
         in row-major order.
      3. Cluster constraint: if a module of the same type has already been
         placed, only try cells that are adjacent to an existing module of
         that type (frontier).  This keeps same-type modules together without
         expensive backtracking.
      4. Accept the first valid position found — O(modules × cells).
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

    # Precompute valid cells once
    valid_cells = [
        (i, j)
        for i in range(GRID_SIZE)
        for j in range(GRID_SIZE)
        if space[i][j] == 1
    ]

    # ---------- helpers ----------
    def can_place(rw, rh, x, y):
        if x + rh > GRID_SIZE or y + rw > GRID_SIZE:
            return False
        for i in range(rh):
            for j in range(rw):
                if space[x+i][y+j] == 0 or grid[x+i][y+j] == 1:
                    return False
        return True

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

    # ---------- greedy placement ----------
    for module in module_list:
        mtype = module["type"]
        w, h  = module["w"], module["h"]
        placed_types.setdefault(mtype, 0)

        placed = False
        for (rw, rh) in [(w, h), (h, w)]:
            if placed:
                break

            # First module of its type → try all valid cells
            # Subsequent modules     → only frontier cells (adjacent to same type)
            if placed_types[mtype] == 0:
                candidates = valid_cells
            else:
                candidates = sorted(type_frontier.get(mtype, set()))

            for (x, y) in candidates:
                if can_place(rw, rh, x, y):
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
                    placed = True
                    break

        if not placed:
            print(f"Warning: could not place module id={module['id']} type={mtype}")

    return placements


# =========================
# Visualization
# =========================

def print_layout(space, placements):
    grid = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]

    for p in placements:
        for i in range(p["h"]):
            for j in range(p["w"]):
                grid[p["x"]+i][p["y"]+j] = 1

    print("\n=== Layout Preview ===")

    for i in range(20, 40):
        row = ""
        for j in range(20, 40):
            if space[i][j] == 0:
                row += " "
            else:
                row += "█" if grid[i][j] else "."
        print(row)


# =========================
# Main
# =========================

if __name__ == "__main__":

    space = mock_space()
    modules = mock_modules()

    result = generate_layout(space, modules)

    print("\n=== Placements ===")
    for r in result:
        print(r)

    print_layout(space, result)