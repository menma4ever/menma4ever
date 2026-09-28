"""Render real GitHub activity beside a small, deterministic Tetris game.

Calendar cells come from GitHub GraphQL. Game blocks are decorative and use
collision, gravity, stacking, and line clearing; they never alter the calendar.
"""

import argparse
import json
import os
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""

ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_COLORS = {
    "NONE": "#21262d",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353",
}
BOARD_W, BOARD_H = 10, 14
PIECES = {
    "O": ([(0, 0), (1, 0), (0, 1), (1, 1)], "#e3b341"),
    "I": ([(0, 0), (1, 0), (2, 0), (3, 0)], "#79c0ff"),
    "T": ([(0, 0), (1, 0), (2, 0), (1, 1)], "#d2a8ff"),
    "L": ([(0, 0), (0, 1), (0, 2), (1, 2)], "#ffa657"),
    "S": ([(1, 0), (2, 0), (0, 1), (1, 1)], "#7ee787"),
    "V": ([(0, 0), (0, 1), (0, 2), (0, 3)], "#ff7b72"),
}
# First five placements clear two lines; later pieces visibly stack.
GAME = [("O", 0), ("I", 2), ("I", 6), ("I", 2), ("I", 6),
        ("T", 3), ("L", 0), ("S", 7), ("O", 5), ("V", 9)]


def font(size: int, bold: bool = False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def fetch_calendar(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode("utf-8")
    request = Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "menma4ever-profile-animation"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError("GitHub GraphQL rejected the contribution query")
    return result


def validate_calendar(result: dict) -> list[list[str]]:
    try:
        weeks = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except (TypeError, KeyError) as exc:
        raise ValueError("Missing GitHub contribution calendar") from exc
    if not 40 <= len(weeks) <= 54:
        raise ValueError(f"Unexpected calendar width: {len(weeks)} weeks")
    grid = []
    total_days = 0
    for week in weeks:
        days = week["contributionDays"]
        if not 1 <= len(days) <= 7:
            raise ValueError("Invalid contribution week")
        column = ["NONE"] * 7
        for day in days:
            level, count = day["contributionLevel"], day["contributionCount"]
            if level not in ACTIVITY_COLORS or type(count) is not int or count < 0:
                raise ValueError("Invalid contribution cell")
            weekday = date.fromisoformat(day["date"]).weekday()
            column[(weekday + 1) % 7] = level  # Sunday is GitHub's first row.
            total_days += 1
        grid.append(column)
    if total_days < 300:
        raise ValueError("Incomplete calendar; refusing to publish a partial graph")
    return grid


def empty_board() -> list[list[str | None]]:
    return [[None for _ in range(BOARD_W)] for _ in range(BOARD_H)]


def fits(board: list[list[str | None]], cells: list[tuple[int, int]], x: int, y: int) -> bool:
    for dx, dy in cells:
        cx, cy = x + dx, y + dy
        if cx < 0 or cx >= BOARD_W or cy >= BOARD_H:
            return False
        if cy >= 0 and board[cy][cx] is not None:
            return False
    return True


def landing_row(board: list[list[str | None]], cells: list[tuple[int, int]], x: int) -> int:
    y = -max(dy for _, dy in cells) - 1
    while fits(board, cells, x, y + 1):
        y += 1
    if any(y + dy < 0 for _, dy in cells):
        raise ValueError("Game board overflowed")
    return y


def lock(board: list[list[str | None]], cells: list[tuple[int, int]], color: str, x: int, y: int) -> list[int]:
    if not fits(board, cells, x, y):
        raise ValueError("Tetris piece overlaps the stack")
    for dx, dy in cells:
        board[y + dy][x + dx] = color
    return [row for row in range(BOARD_H) if all(board[row])]


def clear_lines(board: list[list[str | None]]) -> int:
    remaining = [row for row in board if not all(row)]
    cleared = BOARD_H - len(remaining)
    board[:] = [[None] * BOARD_W for _ in range(cleared)] + remaining
    return cleared


def draw_frame(calendar, board, active, target_x, flash_rows, placed, lines, preview):
    width, height = 1050, 392
    image = Image.new("RGB", (width, height), "#0d1117")
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((1, 1, width - 2, height - 2), radius=18, outline="#30363d", width=2)
    d.text((30, 18), "CONTRIBUTIONS // TETRIS", font=font(22, True), fill="#e6edf3")
    d.text((30, 48), "A real calendar beside a small falling-block game", font=font(12), fill="#8b949e")

    bx, by, step, cell = 30, 82, 20, 18
    d.rounded_rectangle((bx - 5, by - 5, bx + BOARD_W * step + 4, by + BOARD_H * step + 4),
                        radius=6, fill="#111820", outline="#48515b", width=2)
    for row in range(BOARD_H):
        for col in range(BOARD_W):
            px, py = bx + col * step, by + row * step
            color = "#f0f6fc" if row in flash_rows else board[row][col]
            d.rounded_rectangle((px, py, px + cell, py + cell), radius=2,
                                fill=color or "#1c2530", outline="#303c48", width=1)

    if active is not None:
        name, x, y = active
        cells, color = PIECES[name]
        if target_x is not None:
            ghost_y = landing_row(board, cells, target_x)
            for dx, dy in cells:
                px = bx + (target_x + dx) * step
                py = by + (ghost_y + dy) * step
                d.rounded_rectangle((px, py, px + cell, py + cell), radius=2, outline="#667d91", width=2)
        for dx, dy in cells:
            cx, cy = x + dx, y + dy
            if cy < 0:
                continue
            px, py = bx + cx * step, by + cy * step
            d.rounded_rectangle((px, py, px + cell, py + cell), radius=2,
                                fill=color, outline="#f0f6fc", width=1)

    gx, gy, grid_step, grid_cell = 275, 128, 13, 10
    d.text((gx, 87), "PUBLIC GITHUB ACTIVITY", font=font(18, True), fill="#e6edf3")
    d.text((gx, 108), "Each small square is one day in GitHub's calendar", font=font(11), fill="#8b949e")
    for col, week in enumerate(calendar):
        for row, level in enumerate(week):
            px, py = gx + col * grid_step, gy + row * grid_step
            d.rounded_rectangle((px, py, px + grid_cell, py + grid_cell), radius=2,
                                fill=ACTIVITY_COLORS[level])

    d.text((gx, 248), f"PIECES LOCKED  {placed:02d}    LINES CLEARED  {lines:02d}",
           font=font(16, True), fill="#79c0ff")
    d.text((gx, 280), "Pieces travel to columns, land on the stack and clear full rows.",
           font=font(11), fill="#8b949e")
    d.text((gx, 306), "Game blocks are decorative; activity cells are real GitHub data.",
           font=font(11), fill="#8b949e")
    if preview:
        d.text((gx, 342), "DEMO CALENDAR CELLS - NOT LIVE ACTIVITY", font=font(12, True), fill="#ff7b72")
    else:
        d.text((gx, 342), "UFL-01  /  Uzbek NLP  /  local AI", font=font(12, True), fill="#7ee787")
    return image


def render(calendar: list[list[str]], output: Path, preview: bool = False) -> tuple[int, int]:
    board = empty_board()
    frames = [draw_frame(calendar, board, None, None, [], 0, 0, preview)]
    durations = [450]
    lines = 0
    for placed, (name, target) in enumerate(GAME):
        cells, color = PIECES[name]
        x = min(4, BOARD_W - max(dx for dx, _ in cells) - 1)
        y = -max(dy for _, dy in cells) - 1
        for _ in range(40):
            frames.append(draw_frame(calendar, board, (name, x, y), target, [], placed, lines, preview))
            durations.append(95)
            moved = False
            if x != target:
                next_x = x + (1 if target > x else -1)
                if fits(board, cells, next_x, y):
                    x = next_x
                    moved = True
            falls = 0
            for _ in range(2):
                if fits(board, cells, x, y + 1):
                    y += 1
                    falls += 1
            if falls == 0 and x == target:
                break
            if falls == 0 and not moved:
                raise ValueError(f"Piece {name} cannot reach target column {target}")
        else:
            raise ValueError("Tetris animation exceeded frame limit")
        full = lock(board, cells, color, x, y)
        frames.append(draw_frame(calendar, board, None, None, [], placed + 1, lines, preview))
        durations.append(180)
        if full:
            for _ in range(2):
                frames.append(draw_frame(calendar, board, None, None, full, placed + 1, lines, preview))
                durations.append(130)
            lines += clear_lines(board)
            frames.append(draw_frame(calendar, board, None, None, [], placed + 1, lines, preview))
            durations.append(220)
    frames.append(draw_frame(calendar, board, None, None, [], len(GAME), lines, preview))
    durations.append(1700)
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True, disposal=2)
    print(f"Rendered {len(calendar)} activity weeks, {len(GAME)} pieces, {lines} cleared lines to {output}")
    return len(GAME), lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "contribution-tetris.gif")
    parser.add_argument("--fixture", type=Path, help="Synthetic QA only; never use in the workflow")
    args = parser.parse_args()
    if args.fixture:
        result = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GITHUB_TOKEN")
        login = os.environ.get("GITHUB_USER")
        if not token or not login:
            raise SystemExit("GITHUB_TOKEN and GITHUB_USER are required")
        result = fetch_calendar(login, token)
    render(validate_calendar(result), args.output, preview=bool(args.fixture))


if __name__ == "__main__":
    main()
