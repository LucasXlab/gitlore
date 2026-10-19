#!/usr/bin/env python3
"""Regenerate GitLore's animated demo assets from a REAL repository run.

The GIF is rendered from actual `gitlore` output (not fabricated numbers),
so it can be regenerated at any time:

    pip install Pillow
    python scripts/make_demo.py --repo /tmp/gitlore-demo-repo

Produces assets/demo.gif (animated) and assets/demo.png (final frame).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("This script needs Pillow: pip install Pillow")

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Monospace fonts available on macOS; falls back elsewhere.
_FONTS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Courier.ttc",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

W = 980
PAD = 26
TOP = 52
LINE_H = 22
FONT_SIZE = 15

BG = (15, 23, 42)
TOPBAR = (30, 41, 59)
FG = (226, 232, 240)
CYAN = (56, 189, 248)
BLUE = (96, 165, 250)
MUTED = (71, 85, 105)
GREY = (148, 163, 184)
# risk rank gradient: hottest -> coolest
HOT = [
    (248, 113, 113),
    (251, 146, 60),
    (250, 204, 21),
    (190, 227, 120),
    (134, 239, 172),
    (45, 212, 191),
    (186, 230, 253),
    (203, 213, 225),
    (148, 163, 184),
    (148, 163, 184),
]


def load_font(size: int):
    for path in _FONTS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def color_for(line: str):
    s = line.strip()
    if s.startswith("$") or s.startswith("GitLore"):
        return CYAN
    if s and set(s) <= set("-= "):
        return MUTED
    if "Activity" in s:
        return BLUE
    head = s.split(".")[0]
    if head.isdigit() and len(head) <= 2:
        idx = int(head) - 1
        return HOT[idx] if 0 <= idx < len(HOT) else GREY
    if s.startswith("Top "):
        return GREY
    return FG


def truncate(text: str, font, max_px: int) -> str:
    if font.getlength(text) <= max_px:
        return text
    while text and font.getlength(text + "...") > max_px:
        text = text[:-1]
    return text + "..."


def new_frame(height: int) -> Image.Image:
    img = Image.new("RGB", (W, height), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34], fill=TOPBAR)
    for i, c in enumerate([(239, 68, 68), (234, 179, 8), (34, 197, 94)]):
        x = 16 + i * 22
        d.ellipse([x, 11, x + 12, 23], fill=c)
    d.text((W / 2 - 55, 9), "gitlore — demo", font=load_font(13), fill=GREY)
    return img


def render(items: list[tuple[str, tuple]], height: int) -> Image.Image:
    img = new_frame(height)
    d = ImageDraw.Draw(img)
    font = load_font(FONT_SIZE)
    y = TOP
    for text, color in items:
        if y > height - PAD:
            break
        d.text((PAD, y), truncate(text, font, W - 2 * PAD), font=font, fill=color)
        y += LINE_H
    return img


def run_gitlore(repo: str, top: int, name: str) -> list[str]:
    out = subprocess.run(
        [sys.executable, "-m", "gitlore", "--repo", repo, "--no-color", "--top", str(top)],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    ).stdout
    lines = []
    for line in out.splitlines():
        if line.startswith("Repository :"):
            line = f"Repository : {name}"
        lines.append(line)
    # keep the demo compact: hotspots + up to 5 contributors
    if "Top contributors:" in lines:
        idx = lines.index("Top contributors:")
        lines = lines[: idx + 6]
    return lines


def build_frames(lines: list[str], name: str, step: int):
    """Yield successive states of the terminal screen."""
    display: list[tuple[str, tuple]] = []

    def push(text: str, color=None):
        display.append((text, color or color_for(text)))

    # 1) type `pip install gitlore`
    cmd1 = "pip install gitlore"
    typed = ""
    for i in range(0, len(cmd1) + 1, 2):
        typed = cmd1[:i]
        yield display + [(f"$ {typed}", CYAN)]
    display.append((f"$ {cmd1}", CYAN))
    yield list(display)

    display.append(("Successfully installed gitlore-0.1.0", MUTED))
    yield list(display)

    # 2) type the gitlore command
    cmd2 = f"cd {name} && gitlore"
    for i in range(0, len(cmd2) + 1, 2):
        yield display + [(f"$ {cmd2[:i]}", CYAN)]
    display.append((f"$ {cmd2}", CYAN))
    yield list(display)

    # 3) reveal output progressively
    for i in range(0, len(lines), step):
        yield display + [(ln, color_for(ln)) for ln in lines[i : i + step]]
    yield display + [(ln, color_for(ln)) for ln in lines]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Repository to record against")
    ap.add_argument("--name", default=None, help="Display name for the repo")
    ap.add_argument("--top", type=int, default=8, help="Hotspots to show")
    ap.add_argument("--step", type=int, default=2, help="Lines revealed per frame")
    ap.add_argument("--duration", type=int, default=110, help="Frame duration (ms)")
    args = ap.parse_args()

    name = args.name or Path(args.repo).resolve().name
    lines = run_gitlore(args.repo, args.top, name)
    total = 4 + len(lines)
    height = TOP + LINE_H * total + PAD
    height = max(height, 420)

    frames = [render(state, height) for state in build_frames(lines, name, args.step)]
    if not frames:
        return 1

    final = frames[-1]
    # hold the final frame a bit longer
    frames += [final] * 6

    ASSETS.mkdir(exist_ok=True)
    final.save(ASSETS / "demo.png")
    frames[0].save(
        ASSETS / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=args.duration,
        loop=0,
        optimize=True,
    )
    print(f"wrote assets/demo.png ({height}px tall)")
    print(f"wrote assets/demo.gif ({len(frames)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
