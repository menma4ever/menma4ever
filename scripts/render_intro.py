"""Render a self-hosted, word-by-word profile introduction GIF."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "token-intro.gif"
SIZE = (900, 172)
BG = "#0d1117"
WHITE = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#7ee787"
BLUE = "#79c0ff"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    choices = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for path in choices:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def frame(visible: int) -> Image.Image:
    image = Image.new("RGB", SIZE, BG)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((1, 1, 898, 170), radius=18, outline="#30363d", width=2)
    d.ellipse((25, 21, 35, 31), fill="#ff7b72")
    d.ellipse((43, 21, 53, 31), fill="#e3b341")
    d.ellipse((61, 21, 71, 31), fill="#7ee787")
    d.text((91, 18), "ufl / intro", font=font(14), fill=MUTED)
    d.line((24, 48, 876, 48), fill="#30363d", width=1)
    d.text((27, 65), ">", font=font(23, True), fill=GREEN)
    d.text((52, 66), "generate_profile_intro()", font=font(21), fill=BLUE)

    chunks = [
        ("Hi,", 52, 105, WHITE),
        ("I'm", 111, 105, WHITE),
        ("Abdulaziz", 170, 105, WHITE),
        ("Komilov.", 313, 105, WHITE),
        ("I", 52, 136, WHITE),
        ("build", 77, 136, WHITE),
        ("Uzbek", 155, 136, GREEN),
        ("LLMs", 247, 136, WHITE),
        ("&", 313, 136, WHITE),
        ("practical", 339, 136, WHITE),
        ("AI", 473, 136, WHITE),
        ("agents.", 511, 136, WHITE),
    ]
    body = font(20, True)
    for token, x, y, color in chunks[:visible]:
        d.text((x, y), token, font=body, fill=color)
    if visible < len(chunks):
        x = chunks[visible][1]
        y = chunks[visible][2]
        d.rectangle((x, y + 2, x + 10, y + 23), fill=GREEN)
    return image


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images = [frame(i) for i in range(13)]
    durations = [200] + [180] * 11 + [2300]
    images[0].save(OUT, save_all=True, append_images=images[1:], duration=durations,
                   loop=0, optimize=True, disposal=2)
    print(OUT)


if __name__ == "__main__":
    main()
