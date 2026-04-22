import io
import os
import tempfile
import zipfile

import cadquery as cq
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.pipeline import run_pipeline

router = APIRouter()


class Items(BaseModel):
    pens: int = 0
    standardSD: int = 0
    microSD: int = 0


class Tray(BaseModel):
    length: int
    width: int
    height: str  # "short" or "high"
    divX: int = 0
    divY: int = 0


class GenerateOrganizerRequest(BaseModel):
    items: Items
    trays: list[Tray]
    availableSpace: list[list[int]]


@router.post("/api/generate-organizer")
def generate_organizer(req: GenerateOrganizerRequest):
    if not req.availableSpace:
        raise HTTPException(400, "No available space selected on the grid.")
    if req.items.pens + req.items.standardSD + req.items.microSD == 0 and not req.trays:
        raise HTTPException(400, "No items requested (pens, SD cards, or trays).")

    result = run_pipeline(req.items, req.trays, req.availableSpace)

    if result["unplaced"]:
        details = ", ".join(
            f"{m['type']} {m['w']}x{m['h']}" for m in result["unplaced"]
        )
        raise HTTPException(
            400,
            f"Cannot fit all modules in the selected space. "
            f"{len(result['unplaced'])} module(s) did not fit: {details}. "
            f"Remove some modules or expand the work area.",
        )

    zip_buf = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for m in result["modules"]:
                fname = f"{m['type']}_{m['id']}.stl"
                fpath = os.path.join(tmp, fname)
                cq.exporters.export(m["cad"], fpath)
                zf.write(fpath, fname)

            if result["combined"] is not None:
                combined_path = os.path.join(tmp, "combined.stl")
                cq.exporters.export(result["combined"], combined_path)
                zf.write(combined_path, "combined.stl")

    zip_buf.seek(0)
    return Response(
        content=zip_buf.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="organizer.zip"',
            "X-Placements": str(len(result["placements"])),
        },
    )
