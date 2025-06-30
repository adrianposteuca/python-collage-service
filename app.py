import os
from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

# Instantiate the app
app = FastAPI()

# Base paths
BASE_DIR = Path(__file__).parent
PUBLIC_DIR = BASE_DIR / "public"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_PATH = STATIC_DIR / "template.png"  # your transparent PNG

# 1) Serve the HTML page on GET /
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse(PUBLIC_DIR / "index.html")


# 2) Handle the form POST at /generate
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
    # Open the template overlay
    template = Image.open(TEMPLATE_PATH).convert("RGBA")

    # Paste each uploaded image into its slot,
    # using its alpha channel as mask if present
    for img_file, left, top in [
        (photo1, p1Left, p1Top),
        (photo2, p2Left, p2Top),
        (photo3, p3Left, p3Top),
        (photo4, p4Left, p4Top),
    ]:
        img = Image.open(img_file.file).convert("RGBA")
        template.paste(img, (left, top), img)

    # Write result to in-memory buffer
    buf = BytesIO()
    template.save(buf, format="PNG")
    buf.seek(0)

    # Return as downloadable attachment
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="collage.png"'},
    )


# 3) Mount only /static for assets (CSS/JS, template.png, etc.)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# 4) If you run locally, allow `python app.py` to start it:
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
