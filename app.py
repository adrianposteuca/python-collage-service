import os
from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI()

# ─── PATH SETUP ────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.resolve()
PUBLIC_DIR   = BASE_DIR / "public"    # contains index.html
STATIC_DIR   = BASE_DIR / "static"    # contains template.png, css/js etc.
TEMPLATE_PNG = STATIC_DIR / "template.png"

# ─── SERVE FORM (GET /) ────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def serve_form():
    index_path = PUBLIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(500, detail="index.html not found")
    return FileResponse(index_path)

# ─── EXPOSE STATIC ASSETS (/static/<filename>) ───────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ─── SLOT DEFINITIONS (your measured holes) ───────────────
HOLES = [
    {"left": 202,  "top":  311, "width": 943, "height": 1095},
    {"left":1341,  "top":  311, "width": 937, "height": 1095},
    {"left": 202,  "top": 1954, "width": 943, "height": 1149},
    {"left":1341,  "top": 1954, "width": 937, "height": 1149},
]

# ─── GENERATE COLLAGE (POST /generate) ────────────────────
@app.post("/generate")
async def generate_collage(
    photo1: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
):
    # load template
    if not TEMPLATE_PNG.exists():
        raise HTTPException(500, detail=f"Template missing: {TEMPLATE_PNG}")
    template = Image.open(TEMPLATE_PNG).convert("RGBA")

    uploads = [photo1, photo2, photo3, photo4]

    # paste each photo into its hole
    for idx, (up, hole) in enumerate(zip(uploads, HOLES), start=1):
        try:
            img = Image.open(up.file).convert("RGBA")
        except Exception:
            raise HTTPException(400, detail=f"Cannot open photo #{idx}")

        # scale down to fit hole, preserving aspect ratio
        img.thumbnail((hole["width"], hole["height"]), Image.ANTIALIAS)

        # center within the hole
        dx = hole["left"] + (hole["width"]  - img.width ) // 2
        dy = hole["top"]  + (hole["height"] - img.height) // 2

        template.alpha_composite(img, (dx, dy))

    # save and return
    out_path = BASE_DIR / "collage.png"
    template.save(out_path, format="PNG")

    return FileResponse(
        path=str(out_path),
        media_type="image/png",
        filename="collage.png"
    )

# ─── LOCAL DEV ENTRY ───────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
