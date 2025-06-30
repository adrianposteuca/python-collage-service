# app.py
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from io import BytesIO

app = FastAPI()

# mount the static/ folder so FastAPI can serve index.html (and anything else)# app.py
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from PIL import Image

app = FastAPI()

# --- CONFIGURARE ---

# Unde se află template-ul (cu transparență)
BASE_DIR = Path(__file__).parent
TEMPLATE_PATH = BASE_DIR / "static" / "template.png"

# Dimensiunile sloturilor (width, height) în pixeli.
# ==> Ajustează aceste valori după dimensiunea găurilor din template-ul tău!
SLOT_SIZES = [
    (600, 600),  # slot pentru poza 1
    (600, 600),  # slot pentru poza 2
    (600, 600),  # slot pentru poza 3
    (600, 600),  # slot pentru poza 4
]


# --- HANDLER POST /generate ---

@app.post("/generate")
async def generate(
    # cele 4 fișiere
    photo1: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
    # coordonatele X/Y (left/top) pentru fiecare poză
    p1Left: int = Form(...), p1Top: int = Form(...),
    p2Left: int = Form(...), p2Top: int = Form(...),
    p3Left: int = Form(...), p3Top: int = Form(...),
    p4Left: int = Form(...), p4Top: int = Form(...),
):
    # 1) Încarcă template-ul
    if not TEMPLATE_PATH.exists():
        raise HTTPException(500, detail=f"Template not found at {TEMPLATE_PATH}")
    template = Image.open(TEMPLATE_PATH).convert("RGBA")

    # 2) Pregătește lista parametrilor
    uploads = [
        (photo1, p1Left, p1Top, SLOT_SIZES[0]),
        (photo2, p2Left, p2Top, SLOT_SIZES[1]),
        (photo3, p3Left, p3Top, SLOT_SIZES[2]),
        (photo4, p4Left, p4Top, SLOT_SIZES[3]),
    ]

    # 3) Pentru fiecare imagine:
    for idx, (up_file, left, top, (slot_w, slot_h)) in enumerate(uploads, start=1):
        # a) Încarcă și convertește
        try:
            img = Image.open(up_file.file).convert("RGBA")
        except Exception:
            raise HTTPException(400, detail=f"Could not open image #{idx}")

        # b) Redimensionează păstrând proporțiile, maxim slot_w×slot_h
        img.thumbnail((slot_w, slot_h), Image.ANTIALIAS)

        # c) Centrează în slot
        dx = left + (slot_w - img.width) // 2
        dy = top  + (slot_h - img.height) // 2

        # d) Suprapune pe template
        template.alpha_composite(img, (dx, dy))

    # 4) Salvează colajul și trimite-l clientului
    out_path = BASE_DIR / "output.png"
    template.save(out_path)

    return FileResponse(
        path=out_path,
        media_type="image/png",
        filename="colaj-before-after.png"
    )


# --- (opțional) pornire locală cu Uvicorn ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

TEMPLATE_PATH = os.path.join("static", "template.png")

@app.get("/", response_class=HTMLResponse)
async def serve_form():
    """
    Serve your index.html (it should be located at public/index.html)
    """
    with open(os.path.join("public", "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/generate")
async def generate_collage(
    photo1: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
    p1Left: int = Form(...),
    p1Top: int = Form(...),
    p2Left: int = Form(...),
    p2Top: int = Form(...),
    p3Left: int = Form(...),
    p3Top: int = Form(...),
    p4Left: int = Form(...),
    p4Top: int = Form(...),
):
    # Load your transparent template
    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    canvas_w, canvas_h = template.size

    # Create a white background canvas
    collage = Image.new("RGBA", (canvas_w, canvas_h), "WHITE")

    # Helper to read & paste each photo
    async def paste_photo(upload: UploadFile, x: int, y: int):
        data = await upload.read()
        im = Image.open(BytesIO(data)).convert("RGBA")
        # If you ever need to scale to a fixed size, do it here, e.g.:
        # im = im.resize((SLOT_WIDTH, SLOT_HEIGHT), Image.LANCZOS)
        collage.paste(im, (x, y), im)

    # Paste all four
    await paste_photo(photo1, p1Left, p1Top)
    await paste_photo(photo2, p2Left, p2Top)
    await paste_photo(photo3, p3Left, p3Top)
    await paste_photo(photo4, p4Left, p4Top)

    # Finally overlay the template so the photos only show in the "holes"
    collage.paste(template, (0, 0), template)

    # Save out
    out_path = "collage.png"
    # convert to RGB to drop alpha for maximum compatibility
    collage.convert("RGB").save(out_path, "PNG")

    return FileResponse(
        out_path,
        media_type="image/png",
        filename="collage.png"
    )
