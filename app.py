# app.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image
from io import BytesIO
from pathlib import Path   # ← add this import!

app = FastAPI()

# resolve template.png relative to this file
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "static" / "template.png"

@app.post("/generate")
async def generate(
    photo1: UploadFile = File(...),
    photo2: UploadFile = File(...),
    photo3: UploadFile = File(...),
    photo4: UploadFile = File(...),
    p1Left: int = 120, p1Top: int = 180,
    p2Left: int = 788, p2Top: int = 180,
    p3Left: int = 120, p3Top: int = 1140,
    p4Left: int = 788, p4Top: int = 1140,
):
    # open the template
    template = Image.open(TEMPLATE_PATH).convert("RGBA")

    # load each upload into an RGBA image
    def load_upload(u):
        return Image.open(BytesIO(u.file.read())).convert("RGBA")

    imgs = {
        (p1Left, p1Top): load_upload(photo1),
        (p2Left, p2Top): load_upload(photo2),
        (p3Left, p3Top): load_upload(photo3),
        (p4Left, p4Top): load_upload(photo4),
    }

    # composite each photo onto the template
    out = template.copy()
    for (x, y), img in imgs.items():
        # optionally resize img to fit hole here…
        out.alpha_composite(img, dest=(x, y))

    # return as PNG
    buf = BytesIO()
    out.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
