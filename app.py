import os
from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI()

# ─── Directories & Paths ──────────────────────────────────
BASE_DIR     = Path(__file__).parent.resolve()
PUBLIC_DIR   = BASE_DIR / "public"     # your index.html lives here
STATIC_DIR   = BASE_DIR / "static"     # your template.png lives here
TEMPLATE_PNG = STATIC_DIR / "template.png"

# ─── Mount static template/assets ────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ─── Serve the HTML form ──────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_form():
    index_file = PUBLIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(500, detail="index.html not found")
    return FileResponse(index_file)

# ─── Hole definitions (measured in px) ───────────────────
HOLES = [
    {"left": 202,  "top":  311, "width": 943, "height": 1095},  # slot 1
    {"left":1341,  "top":  311, "width": 937, "height": 1095},  # slot 2
    {"left": 202,  "top": 1954, "width": 943, "height": 1149},  # slot 3
    {"left":1341,  "top": 1954, "width": 937, "height": 1149},  # slot 4
]

# ─── POST /generate: composite 4 uploads into the template ─
@app.post("/generate")
async def generate_collage(
    photo1: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
):
    # 1) Load & verify template
    if not TEMPLATE_PNG.exists():
        raise HTTPException(500, detail=f"Template not found: {TEMPLATE_PNG}")
    template = Image.open(TEMPLATE_PNG).convert("RGBA")

    uploads = [photo1, photo2, photo3, photo4]

    # 2) Process each upload
    for idx, (upload, hole) in enumerate(zip(uploads, HOLES), start=1):
        data = await upload.read()
        try:
            img = Image.open(BytesIO(data)).convert("RGBA")
        except Exception:
            raise HTTPException(400, detail=f"Cannot open image #{idx}")

        # 2a) Scale-down to fit hole: use LANCZOS (ANTIALIAS deprecated)
        img.thumbnail((hole["width"], hole["height"]), Image.Resampling.LANCZOS)

        # 2b) Center within hole
        dx = hole["left"] + (hole["width"]  - img.width ) // 2
        dy = hole["top"]  + (hole["height"] - img.height) // 2

        # 2c) Composite under template
        template.alpha_composite(img, (dx, dy))

    # 3) Stream back the result as PNG
    buf = BytesIO()
    template.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="collage.png"'},
    )

# ─── Local dev entrypoint ─────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
