import cadquery as cq

# ==========================
# 1. User-editable parameters (Edit Here)
# ==========================
num_small_slots = 4   # Total number of small slots
num_large_slots = 4   # Total number of large slots

# Slot dimensions (Width, Depth, Height)
small_size = (12.0, 2.0, 6.0)
large_size = (26.0, 3.0, 10.0)

# Spacing and margins
margin = 5.0          # Edge clearance
gap_x = 6.0           # Horizontal spacing between small slots
gap_y = 5.0           # Vertical spacing between rows

holder_height = 15.0  # Total base height

# ==========================
# 2. Logical calculations (Scaling Logic)
# ==========================

rows_small = (num_small_slots + 1) // 2
rows_large = num_large_slots

content_width_small = (2 * small_size[0]) + gap_x
content_width_large = large_size[0]
outer_x = max(content_width_small, content_width_large) + (2 * margin)

def get_row_y(row_index):
    current_y = margin
    for i in range(row_index):
        if i < rows_small:
            current_y += small_size[1] + gap_y
        else:
            current_y += large_size[1] + gap_y
    return current_y

total_rows = rows_small + rows_large
outer_y = get_row_y(total_rows - 1) + (small_size[1] if total_rows <= rows_small else large_size[1]) + margin

# ==========================
# 3. Modeling
# ==========================

# Create base (centered=False places the bottom-left corner at 0,0,0)
result = cq.Workplane("XY").box(outer_x, outer_y, holder_height, centered=(False, False, False))

# --- Prepare small-slot coordinate list ---
small_points = []
for i in range(num_small_slots):
    row = i // 2
    col = i % 2
    start_x = (outer_x - content_width_small) / 2
    slot_x = start_x + (col * (small_size[0] + gap_x)) + small_size[0]/2
    slot_y = get_row_y(row) + small_size[1]/2
    small_points.append((slot_x, slot_y))

# Cut all small slots in one pass (move to the top face for cutting)
if small_points:
    result = result.faces(">Z").workplane().pushPoints(small_points)\
                   .rect(small_size[0], small_size[1]).cutBlind(-small_size[2])

# --- Prepare large-slot coordinate list ---
large_points = []
for i in range(num_large_slots):
    row = rows_small + i
    slot_x = outer_x / 2
    slot_y = get_row_y(row) + large_size[1]/2
    large_points.append((slot_x, slot_y))

# Cut all large slots in one pass
if large_points:
    result = result.faces(">Z").workplane().pushPoints(large_points)\
                   .rect(large_size[0], large_size[1]).cutBlind(-large_size[2])

# ==========================
# 4. Output
# ==========================
filename = "sd_card_holder.stl"
cq.exporters.export(result, filename)
print(f"Done! 尺寸: {outer_x:.1f} x {outer_y:.1f} x {holder_height:.1f}mm")
print(f"file saved: {filename}")