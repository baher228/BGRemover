from pathlib import Path
from io import BytesIO
from urllib.parse import urlparse

import requests
from withoutbg import WithoutBG
from PIL import Image

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CANVAS_W, CANVAS_H = 1200, 1200
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

model = WithoutBG.opensource()



def remove_bg_from_file(in_path: Path) -> Image.Image:
    return model.remove_background(str(in_path))


def remove_bg_from_image(img: Image.Image) -> Image.Image:
    tmp = OUTPUT_DIR / "_tmp_download.png"
    img.save(tmp)
    result = model.remove_background(str(tmp))
    tmp.unlink(missing_ok=True)
    return result


def download_image(url: str) -> Image.Image:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content))


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


def filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).stem
    return name if name else "downloaded"


def process_local_files():
    files = [
        f for f in INPUT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXT
    ]
    if not files:
        print("No supported images found in", INPUT_DIR)
        return

    for in_file in files:
        try:
            fg = remove_bg_from_file(in_file)
            out_img = place_on_white_canvas(fg)
            out_name = in_file.stem + ".jpg"
            out_path = OUTPUT_DIR / out_name
            out_img.save(out_path, quality=95)
            print("Processed:", in_file, "->", out_path)
        except Exception as e:
            print("Error on", in_file, ":", e)


def process_url(url: str):
    print(f"Downloading image from: {url}")
    img = download_image(url)
    print("Download complete. Removing background...")
    fg = remove_bg_from_image(img)
    out_img = place_on_white_canvas(fg)
    out_name = filename_from_url(url) + ".jpg"
    out_path = OUTPUT_DIR / out_name
    out_img.save(out_path, quality=95)
    print("Saved:", out_path)


def main():
    print("=== Background Remover ===")
    print("1) Process local files  (from input/ folder)")
    print("2) Process image from URL")
    choice = input("Choose [1/2]: ").strip()

    if choice == "2":
        url = input("Paste image URL: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            return
        try:
            process_url(url)
        except Exception as e:
            print("Error processing URL:", e)
    else:
        process_local_files()


if __name__ == "__main__":
    main()
