from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from PIL import Image
import io
import os

app = FastAPI()

# Load your transparent template once at startup
TEMPLATE_PATH = os.path.join("static", "template.png")
template = Image.open(TEMPLATE_PATH).convert("RGBA")
W, H = template.size

@app.get("/", response_class=HTMLResponse)
async def get_form():
    # serve the same index.html
    return open("public/index.html", "r", encoding="utf-8").read()

@app.post("/generate")
async def generate(
    photo1: UploadFile = File(...),
    p1Left: int = Form(...),
    p1Top:  int = Form(...),

    photo2: UploadFile = File(...),
    p2Left: int = Form(...),
    p2Top:  int = Form(...),

    photo3: UploadFile = File(...),
    p3Left: int = Form(...),
    p3Top:  int = Form(...),

    photo4: UploadFile = File(...),
    p4Left: int = Form(...),
    p4Top:  int = Form(...)
):
    try:
        # Read uploads into PIL images
        photos = []
        for up in (photo1, photo2, photo3, photo4):
            data = await up.read()
            img  = Image.open(io.BytesIO(data)).convert("RGBA")
            photos.append(img)
    except Exception:
        raise HTTPException(400, "Invalid image upload")

    # Create white background
    canvas = Image.new("RGBA", (W, H), (255,255,255,255))

    # Paste photos scaled‐to‐fit (object-fit: cover)
    slots = [
        (p1Left, p1Top),
        (p2Left, p2Top),
        (p3Left, p3Top),
        (p4Left, p4Top),
    ]
    SLOT_W, SLOT_H = (384, 384)  # adjust to your hole size

    for img, (left, top) in zip(photos, slots):
        # calculate cover scale
        scale = max(SLOT_W/img.width, SLOT_H/img.height)
        nw, nh = int(img.width*scale), int(img.height*scale)
        img2 = img.resize((nw, nh), Image.LANCZOS)
        # center‐crop position
        dx = left - (nw - SLOT_W)//2
        dy = top  - (nh - SLOT_H)//2
        canvas.paste(img2, (dx, dy), img2)

    # Overlay template
    canvas.alpha_composite(template, (0,0))

    # Encode to PNG
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png",
                             headers={"Content-Disposition":"attachment; filename=collage.png"})
