"""Render a high-resolution README animation from real o200k_base BPE tokens.

This is a token-stream visual, not a claim about a private model's exact tokenizer.
Run locally with Pillow and tiktoken installed.
"""

from pathlib import Path

import tiktoken
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "token-intro.gif"
ENCODING = tiktoken.get_encoding("o200k_base")
SIZE = (900, 190)
SCALE = 2
BG = "#0d1117"
WHITE = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#7ee787"
BLUE = "#79c0ff"

MESSAGES = [
    "Built UFL-01.\nAward entry: First Uzbek Multimodal Agentic LLM.",
    "Tokenizer + CPT + SFT + DPO\ncompleted for UFL-01.",
    "Quantized model complete.\nPublic Hugging Face release pending.",
    "Agentic MCP systems:\ntools, review, and recovery.",
    "Low-bit quantization research\nfor local AI.",
]


def s(value: int | float) -> int:
    return round(value * SCALE)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    choices = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for path in choices:
        if Path(path).exists():
            return ImageFont.truetype(path, s(size))
    return ImageFont.load_default()


def draw_frame(message_index: int, visible_tokens: int) -> Image.Image:
    ids = ENCODING.encode(MESSAGES[message_index])
    prefix = ENCODING.decode(ids[:visible_tokens])
    image = Image.new("RGB", (s(SIZE[0]), s(SIZE[1])), BG)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((s(1), s(1), s(899), s(189)), radius=s(16),
                        outline="#30363d", width=s(2))
    for x, color in ((28, "#ff7b72"), (47, "#e3b341"), (66, GREEN)):
        d.ellipse((s(x), s(22), s(x + 10), s(32)), fill=color)
    d.text((s(91), s(19)), "ufl / token stream", font=font(14), fill=MUTED)
    d.text((s(757), s(19)), "o200k_base", font=font(13), fill=MUTED)
    d.line((s(25), s(49), s(874), s(49)), fill="#30363d", width=s(1))

    d.text((s(28), s(64)), ">", font=font(23, True), fill=GREEN)
    d.text((s(53), s(64)), "stream_profile()", font=font(22), fill=BLUE)

    body_font = font(23, True)
    line_y = (104, 137)
    for line_number, line in enumerate(prefix.split("\n")):
        if line_number < len(line_y):
            d.text((s(53), s(line_y[line_number])), line, font=body_font, fill=WHITE)

    if visible_tokens:
        piece = ENCODING.decode([ids[visible_tokens - 1]])
        before = ENCODING.decode(ids[:visible_tokens - 1])
        before_lines = before.split("\n")
        line_number = len(before_lines) - 1
        x = s(53) + d.textlength(before_lines[-1], font=body_font)
        for segment in piece.split("\n"):
            if line_number < len(line_y) and segment:
                d.text((round(x), s(line_y[line_number])), segment,
                       font=body_font, fill=GREEN)
            line_number += 1
            x = s(53)

    lines = prefix.split("\n")
    current_line = min(len(lines) - 1, len(line_y) - 1)
    cursor_x = s(53) + d.textlength(lines[-1], font=body_font) + s(4)
    d.rounded_rectangle((round(cursor_x), s(line_y[current_line] + 2),
                         round(cursor_x) + s(9), s(line_y[current_line] + 26)),
                        radius=s(1), fill=GREEN)
    d.text((s(718), s(164)), f"TOKEN {visible_tokens:02d}/{len(ids):02d}",
           font=font(12), fill=MUTED)
    return image


def main() -> None:
    frames: list[Image.Image] = []
    durations: list[int] = []
    for message_index, message in enumerate(MESSAGES):
        ids = ENCODING.encode(message)
        for count in range(1, len(ids) + 1):
            frames.append(draw_frame(message_index, count))
            durations.append(130 if count < len(ids) else 1150)
        for remaining in (len(ids) // 2, len(ids) // 4, 0):
            frames.append(draw_frame(message_index, remaining))
            durations.append(65)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True, disposal=2)
    print(f"Rendered {len(frames)} frames from real {ENCODING.name} tokens to {OUT}")


if __name__ == "__main__":
    main()
