# app.py
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from io import BytesIO

app = FastAPI()

# mount the static/ folder so FastAPI can serve index.html (and anything else)
app.mount("/static", StaticFiles(directory="static"), name="static")

TEMPLATE_PATH = os.path.join("static", "template.png")

@app.get("/", response_class=HTMLResponse)
async def serve_form():
    """
    Serve your index.html (it should be located at static/index.html)
    """
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
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
