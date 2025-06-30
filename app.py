import io
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI()

# 1) Mount static files & serve index.html at /
app.mount("/", StaticFiles(directory="public", html=True), name="public")

# 2) Load the transparent template once
TEMPLATE_PATH = os.path.join("static", "template.png")
template = Image.open(TEMPLATE_PATH).convert("RGBA")
CANVAS_W, CANVAS_H = template.size

@app.post("/generate")
async def generate(
    photo1: UploadFile = File(...),
    p1Left: int = Form(...), p1Top: int = Form(...),
    photo2: UploadFile = File(...),
    p2Left: int = Form(...), p2Top: int = Form(...),
    photo3: UploadFile = File(...),
    p3Left: int = Form(...), p3Top: int = Form(...),
    photo4: UploadFile = File(...),
    p4Left: int = Form(...), p4Top: int = Form(...),
):
    # 3) Read uploads into PIL Images
    photos = []
    for up in (photo1, photo2, photo3, photo4):
        data = await up.read()
        img  = Image.open(io.BytesIO(data)).convert("RGBA")
        photos.append(img)

    # 4) Create a white background canvas
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (255,255,255,255))

    # 5) Define slots and positions
    slots = [
        (p1Left, p1Top),
        (p2Left, p2Top),
        (p3Left, p3Top),
        (p4Left, p4Top),
    ]
    SLOT_W, SLOT_H = 384, 384  # adjust to hole size in your template

    # 6) Paste each photo with "cover" logic
    for img, (left, top) in zip(photos, slots):
        scale = max(SLOT_W/img.width, SLOT_H/img.height)
        nw, nh = int(img.width*scale), int(img.height*scale)
        img2 = img.resize((nw, nh), Image.LANCZOS)
        # center‐crop within slot
        dx = left - (nw - SLOT_W)//2
        dy = top  - (nh - SLOT_H)//2
        canvas.paste(img2, (dx, dy), img2)

    # 7) Overlay the transparent template on top
    canvas.alpha_composite(template, (0,0))

    # 8) Export to PNG
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition":"attachment; filename=collage.png"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", port=8000, reload=True)
