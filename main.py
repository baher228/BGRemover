from pathlib import Path
from withoutbg import WithoutBG
from PIL import Image

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CANVAS_W, CANVAS_H = 1200, 1200  
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

model = WithoutBG.opensource()

def remove_bg(in_path: Path) -> Image.Image:
    return model.remove_background(str(in_path))

def place_on_white_canvas(fg: Image.Image) -> Image.Image:
    img = fg.convert("RGBA")

    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    scale = min(CANVAS_W / w, CANVAS_H / h, 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), (255, 255, 255))

    x = (CANVAS_W - new_w) // 2
    y = (CANVAS_H - new_h) // 2
    canvas.paste(img, (x, y), img)

    return canvas

for in_file in INPUT_DIR.iterdir():
    if not in_file.is_file() or in_file.suffix.lower() not in SUPPORTED_EXT:
        continue

    try:
        fg = remove_bg(in_file)
        out_img = place_on_white_canvas(fg)
        out_name = in_file.stem + ".jpg"  
        out_path = OUTPUT_DIR / out_name
        out_img.save(out_path, quality=95)
        print("Processed:", in_file, "->", out_path)
    except Exception as e:
        print("Error on", in_file, ":", e)
