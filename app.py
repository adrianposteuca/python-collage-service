from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from PIL import Image

app = FastAPI()

# --- CONFIGURARE PATH ---
BASE_DIR     = Path(__file__).resolve().parent
TEMPLATE_PNG = BASE_DIR / "static" / "template.png"   # asigură-te că există aici

# --- DEFINIRE SLOT-URI după ce le-ai măsurat ---
# Am păstrat ordinea: poza1 → găură1, poza2 → găură2, etc.
HOLES = [
    # găura 1 (top-stânga în template-ul tău)  
    {"left": 202,  "top":  311, "width": 943, "height": 1095},
    # găura 2 (top-dreapta)  
    {"left":1341,  "top":  311, "width": 937, "height": 1095},
    # găura 3 (bottom-stânga)  
    {"left": 202,  "top": 1954, "width": 943, "height": 1149},
    # găura 4 (bottom-dreapta)  
    {"left":1341,  "top": 1954, "width": 937, "height": 1149},
]

@app.post("/generate")
async def generate(
    photo1: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
):
    # 1) Verificăm existența template-ului
    if not TEMPLATE_PNG.exists():
        raise HTTPException(500, detail=f"Template not found at {TEMPLATE_PNG}")

    # 2) Deschidem template-ul ca RGBA (are transparență)
    template = Image.open(TEMPLATE_PNG).convert("RGBA")

    uploads = [photo1, photo2, photo3, photo4]

    # 3) Pentru fiecare poză: redimensionăm și o poziționăm centrat în gaura sa
    for idx, (photo, hole) in enumerate(zip(uploads, HOLES), start=1):
        try:
            img = Image.open(photo.file).convert("RGBA")
        except Exception:
            raise HTTPException(400, detail=f"Could not open image #{idx}")

        # 3a) facem thumbnail păstrând proporțiile
        img.thumbnail((hole["width"], hole["height"]), Image.ANTIALIAS)

        # 3b) calculăm un offset astfel încât să fie centrat în interiorul găurii
        dx = hole["left"] + (hole["width"]  - img.width ) // 2
        dy = hole["top"]  + (hole["height"] - img.height) // 2

        # 3c) suprapunem
        template.alpha_composite(img, (dx, dy))

    # 4) Salvăm pe disc și trimitem ca răspuns
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
