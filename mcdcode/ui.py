"""Small, dependency-free terminal presentation layer.

Only locally generated SGR colours enter the output. Values from remote tools
must pass through :func:`safe_text` before being displayed.
"""

from __future__ import annotations

import json
import os
import base64
import zlib
from pathlib import Path
import re
import sys
import time
import unicodedata
import shutil
from dataclasses import dataclass
from typing import Callable, Iterable, TextIO


ROOT = Path(__file__).resolve().parents[1]
GOLD = "\x1b[38;2;255;188;13m"
RED = "\x1b[38;2;218;41;28m"
CREAM = "\x1b[38;2;255;244;217m"
MUTED = "\x1b[38;2;176;159;135m"
RESET = "\x1b[0m"
_SGR = re.compile(r"\x1b\[(?:0|1|22|39|49|38;2;(?:\d{1,3};){2}\d{1,3}(?:;48;2;(?:\d{1,3};){2}\d{1,3})?|48;2;(?:\d{1,3};){2}\d{1,3})m")


def safe_text(value: object, max_length: int = 1000) -> str:
    """Convert untrusted values into one printable line without terminal codes."""
    text = str(value)
    clean = []
    for char in text[:max_length]:
        if char in "\r\n\t":
            clean.append(" ")
        elif unicodedata.category(char) in {"Cc", "Cf", "Cs"}:
            clean.append("\\x%02x" % ord(char) if ord(char) < 256 else "\\u%04x" % ord(char))
        else:
            clean.append(char)
    if len(text) > max_length:
        clean.append("…")
    return "".join(clean)


def display_width(value: str) -> int:
    """Approximate terminal columns for the CJK text and block art we emit."""
    text = _SGR.sub("", value)
    return sum(
        0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        for char in text
    )


def _wrap(value: object, width: int) -> list[str]:
    rows: list[str] = []
    current = ""
    columns = 0
    for char in safe_text(value):
        size = display_width(char)
        if current and columns + size > width:
            rows.append(current)
            current, columns = "", 0
        current += char
        columns += size
    rows.append(current)
    return rows


def render_card(title: object, lines: Iterable[object], width: int = 68,
                stream: TextIO | None = None) -> str:
    """Render a screenshot-friendly card, bounded to at most 80 columns."""
    width = max(24, min(80, int(width)))
    inner = width - 4
    heading = safe_text(title)
    body = _wrap(heading, inner)
    body.append("─" * inner)
    for value in lines:
        body.extend(_wrap(value, inner))
    color = _use_color(stream or sys.stdout)
    paint = lambda value, role: theme_text(value, role, stream=stream) if color else value
    rows = [paint("╭" + "─" * (width - 2) + "╮", "border")]
    heading_rows = len(_wrap(heading, inner))
    for index, row in enumerate(body):
        role = "title" if index < heading_rows else "border" if index == heading_rows else "body"
        content = row + " " * max(0, inner - display_width(row))
        rows.append(paint("│ ", "border") + paint(content, role) + paint(" │", "border"))
    rows.append(paint("╰" + "─" * (width - 2) + "╯", "border"))
    return "\n".join(rows)


def _use_color(stream: TextIO) -> bool:
    if "NO_COLOR" in os.environ or os.environ.get("MCD_COLOR", "").lower() == "never":
        return False
    return os.environ.get("MCD_COLOR", "").lower() == "always" or bool(getattr(stream, "isatty", lambda: False)())


def initialize_terminal(stream: TextIO | None = None) -> None:
    """Enable Windows VT colours without changing non-interactive output."""
    stream = stream or sys.stdout
    if os.name == "nt" and getattr(stream, "isatty", lambda: False)():
        try:
            import ctypes
            kernel = ctypes.windll.kernel32
            handle = kernel.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel.SetConsoleMode(handle, mode.value | 0x0004)
        except (AttributeError, OSError, ValueError):
            pass


def theme_text(value: object, role: str = "body", stream: TextIO | None = None) -> str:
    text = safe_text(value, 10000)
    if not _use_color(stream or sys.stdout):
        return text
    colour = {"title": GOLD, "prompt": GOLD, "command": GOLD, "border": RED,
              "accent": RED, "muted": MUTED, "body": CREAM}.get(role, CREAM)
    return colour + text + RESET


def _arch_pixels(size=30):
    """Sample a curved double arch, with long outer legs and a raised centre."""
    outline = [(0.17, 0.80)]
    def curve(a, b, end):
        start = outline[-1]
        for index in range(1, 25):
            t, u = index / 24, 1-index / 24
            outline.append((u**3*start[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*end[0],
                            u**3*start[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*end[1]))
    curve((.17,.42),(.24,.20),(.35,.20))
    curve((.42,.20),(.47,.32),(.50,.42))
    curve((.53,.32),(.58,.20),(.65,.20))
    curve((.76,.20),(.83,.42),(.83,.80))
    outline.append((.75,.80))
    curve((.75,.48),(.70,.26),(.65,.26))
    curve((.58,.26),(.54,.44),(.54,.76))
    outline.append((.46,.76))
    curve((.46,.44),(.42,.26),(.35,.26))
    curve((.30,.26),(.25,.48),(.25,.80))
    def inside(x, y):
        result = False
        for a, b in zip(outline, outline[1:] + outline[:1]):
            if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
                result = not result
        return result
    pixels = []
    for y in range(size):
        row = []
        for x in range(size):
            px, py = (x+.5)/size, (y+.5)/size
            # Rounded red tile; transparent corners use the terminal background.
            corner_x = max(.12-px, px-.88, 0)
            corner_y = max(.12-py, py-.88, 0)
            row.append(None if corner_x**2+corner_y**2 > .12**2 else
                       (255,188,13) if inside(px,py) else (218,41,28))
        pixels.append(row)
    return pixels


def _logo_rows(color: bool) -> list[str]:
    pixels, result = _arch_pixels(), []
    for y in range(0, len(pixels), 2):
        row = []
        previous = None
        for top, bottom in zip(pixels[y], pixels[y+1]):
            if color:
                fg, bg = (bottom, None) if top is None else (top, bottom)
                pair = (fg, bg)
                if pair != previous:
                    row.append(("\x1b[39m" if fg is None else "\x1b[38;2;%d;%d;%dm" % fg)
                               + ("\x1b[49m" if bg is None else "\x1b[48;2;%d;%d;%dm" % bg))
                    previous = pair
                row.append("▀" if top is not None else "▄" if bottom is not None else " ")
            else:
                a, b = top == (255,188,13), bottom == (255,188,13)
                row.append("█" if a and b else "▀" if a else "▄" if b else " ")
        result.append("".join(row) + (RESET if color else ""))
    return result


def banner(points: object = None, coupons: object = None,
           stream: TextIO | None = None) -> str:
    """Return the opening banner; this function never performs network access."""
    stream = stream or sys.stdout
    logo = _logo_rows(_use_color(stream))
    side = {2: ("麦门 Code", "title"), 3: ("mcd-code / terminal agent", "muted"),
            5: ("奶蛙记得你的口味。", "body"), 6: ("越点，越懂你。", "body"), 7: ("/奶蛙       大笑一下", "command"),
            8: ("/order      找店点餐", "command"), 9: ("/budget 30  预算配餐", "command"),
            10: ("/1024       目标挑战", "command"), 11: ("/偏好       口味小本本", "command"),
            12: ("/help 帮助   /exit 退出", "muted")}
    lines = ["  " + row + "    " + (theme_text(*side[index], stream=stream) if index in side else "")
             for index, row in enumerate(logo)]
    lines.append("")
    lines.append(theme_text("  ──────────────────────────────────────────────────────────", "border", stream))
    status = []
    if points is not None:
        status.append("积分 " + safe_text(points, 16))
    if coupons is not None:
        status.append("可用券 " + safe_text(coupons, 16))
    if status:
        lines.append(theme_text("  " + "  │  ".join(status), "title", stream))
    return "\n".join(lines)


_ORIGINAL_FRAMES = [
    ["       ▄██████▄       ", "     ▄██████████▄     ", "    ███ ▀▀ ██ ▀▀ █    ", "    ██████████████    ", "    ███ ▀████▀ ███    ", "     ▀██▄▄▄▄▄▄██▀     ", "       ▀▀████▀▀       "],
    ["        ▄██████▄      ", "      ▄██████████▄    ", "     ███ ▀▀ ██ ▀▀ █   ", "     ██████████████   ", "     ██  ▀████▀  ██   ", "      ▀██▄▄▄▄▄▄██▀    ", "        ▀▀████▀▀      "],
    ["      ▄██████▄        ", "    ▄██████████▄      ", "   ███ ▀▀ ██ ▀▀ █     ", "   ██████████████     ", "   ██  ▀████▀  ██     ", "    ▀██▄▄▄▄▄▄██▀      ", "      ▀▀████▀▀        "],
    ["       ▄██████▄       ", "     ▄██████████▄     ", "    ███ ▀▀ ██ ▀▀ █    ", "    ██████████████    ", "    ███ ▀████▀ ███    ", "     ▀██▄▄▄▄▄▄██▀     ", "       ▀▀████▀▀       "],
]


def _trusted_sgr(line: str) -> str:
    """Allow only RGB SGR produced by the importer, never cursor/OSC escapes."""
    result = []
    position = 0
    for match in _SGR.finditer(line):
        result.append(safe_text(line[position:match.start()], 10000))
        values = match.group()[2:-1].split(";")
        if values in (["0"], ["1"], ["22"], ["39"], ["49"]) or all(0 <= int(value) <= 255 for value in values[2:]):
            result.append(match.group())
        position = match.end()
    result.append(safe_text(line[position:], 10000))
    return "".join(result)


@dataclass
class Animation:
    text: list[list[str]]
    ansi: list[list[str]]
    fps: float
    video: bool
    version: int
    audio: Path | None = None
    render: str = "ascii"
    cell_width: int = 1
    pixels: list[bytes] | None = None
    pixel_width: int = 0
    pixel_height: int = 0

    @property
    def frame_count(self) -> int:
        return len(self.pixels) if self.pixels is not None else len(self.text)


def _read_animation(path: Path) -> Animation:
    """Read bounded, locally imported video frames, with an original fallback."""
    try:
        if path.stat().st_size > 24_000_000:
            raise ValueError("Frame file too large")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") == "mcd-code-laugh-v3":
            width, height = data["width"], data["height"]
            count, fps = len(data["frames"]), float(data["fps"])
            if (type(width) is not int or type(height) is not int or not 1 <= width <= 256
                    or not 2 <= height <= 256 or not 3 <= count <= 300 or not 1 <= fps <= 30
                    or data.get("pixel_format") != "rgb24" or data.get("frame_count", count) != count
                    or width*height*3*count > 64*1024*1024):
                raise ValueError("Invalid RGB animation geometry")
            pixels, expected = [], width*height*3
            for frame in data["frames"]:
                encoded = frame["rgb_zlib"]
                if not isinstance(encoded,str) or len(encoded) > expected*2+2048:
                    raise ValueError("Invalid RGB frame size")
                decoder = zlib.decompressobj()
                rgb = decoder.decompress(base64.b64decode(encoded,validate=True), expected+1)
                if len(rgb) != expected or not decoder.eof or decoder.unused_data:
                    raise ValueError("Invalid RGB frame data")
                pixels.append(rgb)
            audio = path.parent / "laugh.wav"
            return Animation([], [], fps, True, 3, audio if audio.is_file() else None,
                             "truecolor-halfblock", 1, pixels, width, height)
        version = {"mcd-code-laugh-v1": 1, "mcd-code-laugh-v2": 2}.get(data.get("schema"))
        count = len(data["frames"])
        if version is None or not (3 <= count <= (4 if version == 1 else 300)):
            raise ValueError("Unsupported local animation")
        fps = float(data.get("fps", 2))
        if not 1 <= fps <= 30:
            raise ValueError("Invalid frame rate")
        plain_frames, ansi_frames = [], []
        for frame in data["frames"]:
            rows, ansi = frame["text"], frame.get("ansi", frame["text"])
            if not isinstance(rows, list) or not 1 <= len(rows) <= (24 if version == 1 else 60):
                raise ValueError("Invalid frame rows")
            if not all(isinstance(row, str) and len(row) <= 10000 for row in rows):
                raise ValueError("Invalid frame text")
            if not isinstance(ansi, list) or len(ansi) != len(rows) or not all(isinstance(row,str) and len(row)<=20000 for row in ansi):
                raise ValueError("Invalid frame colours")
            cleaned = [safe_text(row, 10000) for row in rows]
            if any(display_width(row) > 80 for row in cleaned):
                raise ValueError("Frame exceeds terminal width")
            plain_frames.append(cleaned)
            ansi_frames.append([_trusted_sgr(row) for row in ansi])
        audio = path.parent / "laugh.wav"
        return Animation(plain_frames, ansi_frames, fps, True, version, audio if audio.is_file() else None,
                         str(data.get("render", "ascii")), 2 if data.get("cell_width") == 2 else 1)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zlib.error):
        return Animation(_ORIGINAL_FRAMES, [[GOLD + row + RESET for row in frame] for frame in _ORIGINAL_FRAMES],
                         1/.18, False, 1)


def _load_frames(path: Path, color: bool) -> tuple[list[list[str]], Path | None]:
    animation = _read_animation(path)
    if animation.version == 3:
        return _fit_pixel_video(animation, 79, 60, color), animation.audio
    return animation.ansi if color else animation.text, animation.audio


def _colour_ascii(row: str) -> str:
    pieces, previous = [], None
    for char in row:
        colour = RED if char in "#%@" else GOLD
        if colour != previous:
            pieces.append(colour)
            previous = colour
        pieces.append(char)
    return "".join(pieces) + RESET


def _fit_ascii(frames: list[list[str]], columns: int, rows: int) -> list[list[str]]:
    height = max(map(len, frames))
    width = max(display_width(row) for frame in frames for row in frame)
    ratio = min(1, max(1,columns)/max(1,width), max(1,rows)/max(1,height))
    target_w, target_h = max(1,int(width*ratio)), max(1,int(height*ratio))
    if ratio >= 1:
        return frames
    fitted = []
    for frame in frames:
        lines = []
        for y in range(target_h):
            line = frame[min(len(frame)-1,int(y*height/target_h))].ljust(width)
            lines.append("".join(line[min(width-1,int(x*width/target_w))] for x in range(target_w)))
        fitted.append(lines)
    return fitted


def _row_styles(row: str) -> list[str]:
    """Map safe local SGR to character positions, preserving video pixel colours."""
    styles, current, position = [], GOLD, 0
    while position < len(row):
        match = _SGR.match(row, position)
        if match:
            sgr = match.group()
            if sgr == RESET or sgr == "\x1b[39m":
                current = GOLD
            elif sgr.startswith("\x1b[38;2;"):
                current = sgr
            position = match.end()
        else:
            styles.append(current)
            position += 1
    return styles


def _fit_video(animation: Animation, columns: int, rows: int, color: bool) -> list[list[str]]:
    cell = animation.cell_width
    source_h = max(map(len, animation.text))
    source_w = max(len(row) for frame in animation.text for row in frame)
    logical_w = max(1, source_w // cell)
    scale = min(1, max(1,columns)/max(1,source_w), max(1,rows)/max(1,source_h))
    width = max(1,int(logical_w*scale))
    height = max(1,int(source_h*scale))
    result = []
    for index, frame in enumerate(animation.text):
        scaled = []
        for y in range(height):
            source_y = min(len(frame)-1, int(y*source_h/height))
            plain = frame[source_y].ljust(source_w)
            styles = _row_styles(animation.ansi[index][source_y]) if color else []
            line, previous = [], None
            for x in range(width):
                source_x = min(logical_w-1, int(x*logical_w/width))*cell
                if color:
                    style = styles[source_x] if source_x < len(styles) else GOLD
                    if style != previous:
                        line.append(style)
                        previous = style
                line.append(plain[source_x:source_x+cell])
            scaled.append("".join(line)+(RESET if color else ""))
        result.append(scaled)
    return result


def _fit_pixel_video(animation: Animation, columns: int, rows: int, color: bool) -> list[list[str]]:
    """Render two distinct source RGB pixels per terminal character.

    Resize from lossless source pixels for the current viewport, avoiding the
    old cache's duplicated horizontal pixels and fixed twelve-colour palette.
    """
    source_w, source_h = animation.pixel_width, animation.pixel_height
    if not animation.pixels or source_w < 1 or source_h < 2:
        return []
    scale = min(1, max(1,columns)/source_w, max(1,rows)*2/source_h)
    width = max(1,int(source_w*scale))
    pixel_height = max(2,int(source_h*scale)//2*2)
    height = pixel_height//2
    # Centre-aligned sampling preserves facial detail better than truncating
    # the top-left of every source cell. The imported master uses Lanczos.
    source_x = [min(source_w-1,int((x+.5)*source_w/width)) for x in range(width)]
    source_y = [min(source_h-1,int((y+.5)*source_h/pixel_height)) for y in range(pixel_height)]
    result = []
    ramp = " .:-=+*#%@"
    for rgb in animation.pixels:
        frame = []
        for row in range(height):
            parts, last_top, last_bottom = [], None, None
            top_offset, bottom_offset = source_y[row*2]*source_w*3, source_y[row*2+1]*source_w*3
            for x in source_x:
                top = tuple(rgb[top_offset+x*3:top_offset+x*3+3])
                bottom = tuple(rgb[bottom_offset+x*3:bottom_offset+x*3+3])
                if not color:
                    value = sum(top)+sum(bottom)
                    parts.append(" " if max(top+bottom) <= 24 else ramp[min(9,round((1-value/(6*255))*9))])
                    continue
                if top != last_top and bottom != last_bottom:
                    parts.append("\x1b[38;2;%d;%d;%d;48;2;%d;%d;%dm" % (*top,*bottom))
                elif top != last_top:
                    parts.append("\x1b[38;2;%d;%d;%dm" % top)
                elif bottom != last_bottom:
                    parts.append("\x1b[48;2;%d;%d;%dm" % bottom)
                parts.append("▀")
                last_top, last_bottom = top, bottom
            frame.append("".join(parts)+(RESET if color else ""))
        result.append(frame)
    return result


def laugh(
    stream: TextIO | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    frames_path: str | Path | None = None,
) -> None:
    """Play the actual imported ASCII video before any network request.

    Non-interactive streams print labelled still frames, with no ANSI or sleeps.
    MCD_NO_ANIMATION selects one still. NO_COLOR preserves motion without colour.
    """
    stream = stream if stream is not None else sys.stdout
    tty = bool(getattr(stream, "isatty", lambda: False)())
    color = tty and _use_color(stream)
    path = Path(frames_path) if frames_path is not None else ROOT / "assets" / "laugh.json"
    if frames_path is None and not path.is_file():
        path = ROOT / ".local" / "laugh.json"  # Older local imports remain readable.
    animation = _read_animation(path)
    if animation.version == 3:
        size = shutil.get_terminal_size((80,30)) if tty else os.terminal_size((80,48))
        frames = _fit_pixel_video(animation, min(160,size.columns-1), max(1,size.lines-6), color)
    else:
        frames = animation.ansi if color else animation.text
    audio = animation.audio
    if os.environ.get("MCD_SOUND", "1").lower() in {"0", "false", "no", "off"}:
        audio = None
    prefix = ""
    heading = prefix + "奶蛙大笑"
    if animation.video:
        heading += f" · 原视频{'高清字符' if animation.version == 3 else ' ASCII'} · {len(frames)} 帧 / {animation.fps:g}fps"
    else:
        heading += " · 未找到视频字符帧，使用原创占位动画"
    stream.write((theme_text(heading, "title", stream) if color else safe_text(heading)) + "\n")
    disabled = os.environ.get("MCD_NO_ANIMATION", "").lower() not in {"", "0", "false", "no"}
    if disabled:
        chosen = frames[len(frames)//2] if animation.version >= 2 else frames[0]
        stream.write("\n".join(chosen) + "\n")
    elif not tty:
        if animation.version >= 2:
            stream.write("\n".join(frames[len(frames)//2]) + "\n")
            stream.write(prefix + "输出已重定向，仅显示视频中间一帧；交互终端播放完整动画。\n")
        else:
            for index, frame in enumerate(frames, 1):
                stream.write(prefix + f"[帧 {index}/{len(frames)}]\n" + "\n".join(frame) + "\n")
    else:
        size = shutil.get_terminal_size((80,30))
        fitted = _fit_ascii(animation.text, min(79,size.columns-1), max(1,size.lines-6)) if animation.version < 3 else None
        if animation.version == 2:
            frames = _fit_video(animation, min(79,size.columns-1), max(1,size.lines-6), color)
        elif animation.version == 1 and fitted != animation.text:
            frames = [[GOLD+row+RESET for row in frame] for frame in fitted] if color else fitted
        if audio is not None and os.name == "nt":
            try:
                import winsound
                winsound.PlaySound(str(audio), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except (OSError, RuntimeError):
                pass
        height = max(map(len, frames))
        stream.write("\x1b[?25l")
        try:
            interval = 1 / animation.fps
            started = time.monotonic()
            index = 0
            while index < len(frames):
                frame = frames[index]
                if index:
                    stream.write(f"\x1b[{height}A")
                for row in frame + [""] * (height - len(frame)):
                    stream.write("\r\x1b[2K" + row + "\n")
                stream.flush()
                if sleep_fn is time.sleep:
                    deadline = started+(index+1)*interval
                    delay = max(0, deadline-time.monotonic())
                    if delay:
                        sleep_fn(delay)
                    index = max(index+1,int((time.monotonic()-started)/interval))
                else:
                    sleep_fn(interval)
                    index += 1
        finally:
            stream.write((RESET if color else "") + "\x1b[?25h")
            if audio is not None and os.name == "nt":
                try:
                    import winsound
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except (OSError, RuntimeError):
                    pass
    footer = prefix + "哈哈哈哈！笑声编译通过，下一步：看看今天吃什么。"
    stream.write((theme_text(footer, "body", stream) if color else footer) + "\n")
    stream.flush()
