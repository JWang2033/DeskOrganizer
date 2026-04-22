import math
import cadquery as cq

# Slot dimensions (Width, Depth, Height)
SMALL_SIZE = (12.0, 2.0, 6.0)
LARGE_SIZE = (26.0, 3.0, 10.0)

# Spacing and margins
MARGIN = 5.0
GAP_X = 6.0
GAP_Y = 5.0
HOLDER_HEIGHT = 15.0


def make_sd_holder(
    num_small_slots: int,
    num_large_slots: int,
    small_size: tuple[float, float, float] = SMALL_SIZE,
    large_size: tuple[float, float, float] = LARGE_SIZE,
    margin: float = MARGIN,
    gap_x: float = GAP_X,
    gap_y: float = GAP_Y,
    holder_height: float = HOLDER_HEIGHT,
    export_path: str | None = None,
) -> cq.Workplane:
    """Build an SD-card holder with small slots (2 per row) and large slots (1 per row)."""
    rows_small = (num_small_slots + 1) // 2
    rows_large = num_large_slots

    content_width_small = (2 * small_size[0]) + gap_x
    content_width_large = large_size[0]
    outer_x = max(content_width_small, content_width_large) + (2 * margin)

    def get_row_y(row_index: int) -> float:
        y = margin
        for i in range(row_index):
            depth = small_size[1] if i < rows_small else large_size[1]
            y += depth + gap_y
        return y

    total_rows = rows_small + rows_large
    last_depth = small_size[1] if total_rows <= rows_small else large_size[1]
    outer_y = get_row_y(total_rows - 1) + last_depth + margin

    # Round outer dimensions up to the nearest 10 mm (1 cm grid)
    # Slot sizes, gaps, and margins are intentionally kept exact.
    def ceil10(v: float) -> float:
        return math.ceil(v / 10) * 10

    outer_x = ceil10(outer_x)
    outer_y = ceil10(outer_y)
    holder_height = ceil10(holder_height)

    result = cq.Workplane("XY").box(
        outer_x, outer_y, holder_height, centered=(False, False, False)
    )

    small_points = []
    for i in range(num_small_slots):
        row, col = i // 2, i % 2
        start_x = (outer_x - content_width_small) / 2
        slot_x = start_x + col * (small_size[0] + gap_x) + small_size[0] / 2
        slot_y = get_row_y(row) + small_size[1] / 2
        small_points.append((slot_x, slot_y))

    if small_points:
        result = (
            result.faces(">Z").workplane()
            .pushPoints(small_points)
            .rect(small_size[0], small_size[1])
            .cutBlind(-small_size[2])
        )

    large_points = []
    for i in range(num_large_slots):
        row = rows_small + i
        slot_x = outer_x / 2
        slot_y = get_row_y(row) + large_size[1] / 2
        large_points.append((slot_x, slot_y))

    if large_points:
        result = (
            result.faces(">Z").workplane()
            .pushPoints(large_points)
            .rect(large_size[0], large_size[1])
            .cutBlind(-large_size[2])
        )

    if export_path:
        cq.exporters.export(result, export_path)

    return result


if __name__ == "__main__":
    make_sd_holder(
        num_small_slots=4, num_large_slots=4, export_path="sd_card_holder.stl"
    )
