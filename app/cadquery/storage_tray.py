import cadquery as cq

# output to Current Working Directory
def storage_tray(unitsX=3, unitsY=3, unitsZ=3, div_x=0, div_y=0):
    # user specified parameters handled by function arguments

    # dvider options
    # (These are now handled by function arguments)

    if unitsX < 3: unitsX = 3
    if unitsY < 3: unitsY = 3
    if unitsZ < 3: unitsZ = 3

    L = unitsX * 10.0
    W = unitsY * 10.0
    H = unitsZ * 10.0

    # wall and floor thickness
    wallT = 1.0
    floorT = 1.0

    # filename based on dimensions
    filename = f"storage_tray_{int(L)}x{int(W)}x{int(H)}mm.stl"

    # base outer box
    result = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))

    # hollow
    result = result.faces(">Z").shell(-wallT)

    # footbed
    inset = wallT + 0.2
    foot_l = L - 2 * inset
    foot_w = W - 2 * inset
    foot_h = 1.0

    result = (
        result.faces("<Z")
        .workplane()
        .rect(foot_l, foot_w)
        .extrude(foot_h)
    )

    # add dividers - 2mm lower than tray height
    inner_L = L - 2 * wallT
    inner_W = W - 2 * wallT
    sep_height = H - floorT - 2.0

    # x-direction dividers
    if div_x > 1:
        spacing_x = inner_L / div_x
        for i in range(1, div_x):
            offset_x = -inner_L/2 + i * spacing_x
            divider = (
                cq.Workplane("XY")
                .workplane(offset=floorT)
                .center(offset_x, 0)
                .box(wallT, inner_W, sep_height, centered=(True, True, False))
            )
            result = result.union(divider)

    # y-direction separators
    if div_y > 1:
        spacing_y = inner_W / div_y
        for i in range(1, div_y):
            offset_y = -inner_W/2 + i * spacing_y
            divider = (
                cq.Workplane("XY")
                .workplane(offset=floorT)
                .center(0, offset_y)
                .box(inner_L, wallT, sep_height, centered=(True, True, False))
            )
            result = result.union(divider)

    # Return the generated CadQuery object and the suggested filename
    return result, filename


# execute only if the script is run directly
if __name__ == "__main__":
    # generate using default parameters
    tray_stl, fname = storage_tray(unitsX=3, unitsY=3, unitsZ=3, div_x=0, div_y=0)

    # save the file
    cq.exporters.export(tray_stl, fname)
    print(f"exported: {fname}")

    # show the result
    if "show_object" in globals():
        show_object(tray_stl)