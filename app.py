from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI()

# --- DIRECTOARE ȘI PATHURI ---
BASE_DIR     = Path(__file__).parent.resolve()
TEMPLATE_PNG = BASE_DIR / "static" / "template.png"
PUBLIC_DIR   = BASE_DIR / "public"    # aici pui index.html, .css, .js etc.

# 1) Montează conţinutul din public/ la rădăcină
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")


# 2) Slot-urile „goale” din template (left, top, width, height)
HOLES = [
    {"left": 202,  "top":  311, "width": 943, "height": 1095},  # P1
    {"left":1341,  "top":  311, "width": 937, "height": 1095},  # P2
    {"left": 202,  "top": 1954, "width": 943, "height": 1149},  # P3
    {"left":1341,  "top": 1954, "width": 937, "height": 1149},  # P4
]


@app.post("/generate")
async def generate(
    photo1: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
):
    # 1. Verificăm că template-ul există
    if not TEMPLATE_PNG.exists():
        raise HTTPException(500, detail=f"Template not found: {TEMPLATE_PNG}")

    # 2. Îl deschidem cu transparență
    template = Image.open(TEMPLATE_PNG).convert("RGBA")

    uploads = [photo1, photo2, photo3, photo4]

    # 3. Pentru fiecare poză: thumbnail + centrare + alpha_composite
    for idx, (photo, hole) in enumerate(zip(uploads, HOLES), start=1):
        try:
            img = Image.open(photo.file).convert("RGBA")
        except Exception:
            raise HTTPException(400, detail=f"Cannot open image #{idx}")

        # redimensionăm fără depășiri
        img.thumbnail((hole["width"], hole["height"]), Image.ANTIALIAS)

        # centrare în interiorul „găurii”
        dx = hole["left"] + (hole["width"]  - img.width ) // 2
        dy = hole["top"]  + (hole["height"] - img.height) // 2

        template.alpha_composite(img, (dx, dy))

    # 4. Salvăm și returnăm PNG-ul final
    out_path = BASE_DIR / "output.png"
    template.save(out_path, format="PNG")

    return FileResponse(
        path=str(out_path),
        media_type="image/png",
        filename="colaj-before-after.png"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
