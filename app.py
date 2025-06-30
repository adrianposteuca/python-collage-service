# app.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from PIL import Image
from io import BytesIO
from pathlib import Path

# 1) Create app and mount static dirs
app = FastAPI()

# Serve your HTML+JS+CSS form from ./public
app.mount("/", StaticFiles(directory="public", html=True), name="public")

# Serve your template (and any other assets) from ./static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Path to your transparent template PNG
TEMPLATE_PATH = Path("static") / "template.png"


@app.post("/generate")
async def generate_collage(
    # four uploaded files
    photo1: UploadFile  = File(...),
    photo2: UploadFile  = File(...),
    photo3: UploadFile  = File(...),
    photo4: UploadFile  = File(...),
    # their X/Y positions from the form
    p1Left: int = Form(...),  p1Top: int = Form(...),
    p2Left: int = Form(...),  p2Top: int = Form(...),
    p3Left: int = Form(...),  p3Top: int = Form(...),
    p4Left: int = Form(...),  p4Top: int = Form(...),
):
    # 2) Load template
    template = Image.open(TEMPLATE_PATH).convert("RGBA")

    # 3) Composite each photo onto template
    for img_file, left, top in [
        (photo1, p1Left, p1Top),
        (photo2, p2Left, p2Top),
        (photo3, p3Left, p3Top),
        (photo4, p4Left, p4Top),
    ]:
        img = Image.open(img_file.file).convert("RGBA")
        # If you need to resize photos to fit your “holes”, you can:
        # img = img.resize((hole_width, hole_height), Image.ANTIALIAS)
        template.paste(img, (left, top), img)

    # 4) Stream back a PNG
    buf = BytesIO()
    template.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="collage.png"'},
    )
