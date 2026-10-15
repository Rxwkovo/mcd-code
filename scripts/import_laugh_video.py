#!/usr/bin/env python3
"""Convert a local laugh video into a private, moving terminal block animation.

FFmpeg is used only when importing video. Runtime playback needs only Python's
standard library. The default preserves full RGB colour, with two vertical
source pixels per terminal character. Legacy solid blocks and ASCII density
rendering remain available through --render.
"""

from __future__ import annotations

import argparse
import base64
from collections import deque
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import wave
import zlib


ROOT = Path(__file__).resolve().parents[1]
WIDTH, MAX_ROWS = 72, 40
BLOCK_WIDTH = 64
RGB_WIDTH, RGB_MAX_WIDTH, RGB_MAX_ROWS = 128, 192, 224
MAX_FRAMES = 300
GOLD = "\x1b[38;2;255;199;44m"
RED = "\x1b[38;2;218;41;28m"
RESET = "\x1b[0m"
SHADES = " .:-=+*#%@"
BLOCK_PALETTE = (
    (255, 199, 44), (255, 188, 13), (242, 169, 0), (224, 139, 0),
    (197, 113, 18), (255, 244, 217), (237, 217, 169), (206, 183, 135),
    (218, 41, 28), (125, 78, 38), (78, 49, 29), (74, 20, 14),
)
# Coordinates of the full moving subject in the supplied 1280x720 clip.
DEFAULT_CROP = "iw*0.46875:ih*0.861111:iw*0.2890625:ih*0.125"
DEFAULT_CLOSE_CROP = "460:440:450:100"


def run_ffmpeg(executable: str, arguments: list[str]) -> bytes:
    result = subprocess.run(
        [executable, "-nostdin", "-hide_banner", "-loglevel", "error", *arguments],
        capture_output=True, timeout=45, check=False,
    )
    if result.returncode:
        raise RuntimeError("FFmpeg 无法读取视频；请确认路径、裁切范围及采样起点。")
    return result.stdout


def validate_settings(start: float, duration: float, fps: int, width: int,
                      render: str = "block-ascii") -> None:
    if not math.isfinite(start) or start < 0:
        raise ValueError("--start 必须是不小于 0 的有限秒数。")
    if not math.isfinite(duration) or not 0.5 <= duration <= 10:
        raise ValueError("--duration 必须在 0.5 到 10 秒之间。")
    if not 1 <= fps <= 30 or math.ceil(duration * fps) > MAX_FRAMES:
        raise ValueError("--fps 必须在 1 到 30 之间，且总帧数不能超过 300。")
    maximum = RGB_MAX_WIDTH if render == "truecolor-halfblock" else WIDTH
    if render not in ("truecolor-halfblock", "block-ascii", "ascii"):
        raise ValueError("--render 必须为 truecolor-halfblock、block-ascii 或 ascii。")
    if not 24 <= width <= maximum:
        raise ValueError(f"--width 必须在 24 到 {maximum} 像素/列之间。")


def parse_ppm_frames(data: bytes, max_width: int = WIDTH,
                     max_height: int = MAX_ROWS) -> list[tuple[int, int, bytes]]:
    """Read FFmpeg's concatenated binary PPM frames, preserving whitespace RGB."""
    frames: list[tuple[int, int, bytes]] = []
    offset = 0
    header = re.compile(rb"P6\s+(\d+)\s+(\d+)\s+255(?:\r\n|[ \t\r\n])")
    while offset < len(data):
        match = header.match(data, offset)
        if match is None:
            raise ValueError("视频帧数据不完整或不是 RGB PPM 格式。")
        width, height = int(match[1]), int(match[2])
        if not 1 <= width <= max_width or not 1 <= height <= max_height:
            raise ValueError(f"视频帧超过允许的 {max_width} × {max_height} 像素范围。")
        begin = match.end()
        end = begin + width * height * 3
        if end > len(data):
            raise ValueError("没有取得完整视频帧，请选择更早的 --start 时间。")
        frames.append((width, height, data[begin:end]))
        if len(frames) > MAX_FRAMES:
            raise ValueError("动画不能超过 300 帧。")
        offset = end
    if not frames:
        raise ValueError("没有取得视频画面，请选择更早的 --start 时间。")
    geometry = frames[0][:2]
    if any(frame[:2] != geometry for frame in frames):
        raise ValueError("视频采样时画面尺寸发生变化。")
    return frames


def pixels_to_ascii_frame(raw: bytes, width: int = WIDTH, height: int = 37) -> dict[str, list[str]]:
    """Map RGB samples to ASCII ink, emphasizing saturated yellow on white."""
    if not 1 <= width <= WIDTH or not 1 <= height <= MAX_ROWS:
        raise ValueError("ASCII 画面尺寸超出终端范围。")
    if len(raw) != width * height * 3:
        raise ValueError("没有取得完整视频帧，请选择更早的 --start 时间。")
    ansi_rows, text_rows = [], []
    for y in range(height):
        ansi, text, previous_color = [], [], None
        for x in range(width):
            pixel = (y * width + x) * 3
            red, green, blue = raw[pixel:pixel + 3]
            luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
            saturation = (max(red, green, blue) - min(red, green, blue)) / 255
            ink = max(1 - luminance, saturation * 0.68)
            char = SHADES[min(len(SHADES) - 1, round(ink * (len(SHADES) - 1)))]
            text.append(char)
            color = RED if luminance < 0.30 else GOLD
            if char != " " and color != previous_color:
                ansi.append(color)
                previous_color = color
            ansi.append(char)
        ansi_rows.append("".join(ansi) + RESET)
        text_rows.append("".join(text))
    return {"ansi": ansi_rows, "text": text_rows}


def white_background_mask(raw: bytes, width: int, height: int) -> set[int]:
    """Remove only pale pixels connected to an outer border, keeping teeth inside."""
    candidates = set()
    for index in range(width * height):
        rgb = raw[index * 3:index * 3 + 3]
        luminance = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255
        saturation = (max(rgb) - min(rgb)) / 255
        if luminance > 0.82 and saturation < 0.12:
            candidates.add(index)
    border = {x for x in range(width)} | {(height - 1) * width + x for x in range(width)}
    border |= {y * width for y in range(height)} | {y * width + width - 1 for y in range(height)}
    background = candidates & border
    pending = deque(background)
    while pending:
        index = pending.popleft()
        x, y = index % width, index // width
        neighbors = []
        if x: neighbors.append(index - 1)
        if x + 1 < width: neighbors.append(index + 1)
        if y: neighbors.append(index - width)
        if y + 1 < height: neighbors.append(index + width)
        for neighbor in neighbors:
            if neighbor in candidates and neighbor not in background:
                background.add(neighbor)
                pending.append(neighbor)
    return background


def pixels_to_frame(raw: bytes, width: int = 32, height: int = 33,
                    render: str = "block-ascii") -> dict[str, list[str]]:
    """Use two solid text blocks per source pixel; square pixels preserve shape."""
    if render == "ascii":
        return pixels_to_ascii_frame(raw, width, height)
    if render != "block-ascii" or not 1 <= width <= WIDTH // 2 or not 1 <= height <= MAX_ROWS:
        raise ValueError("色块画面尺寸超出终端范围。")
    if len(raw) != width * height * 3:
        raise ValueError("没有取得完整视频帧，请选择更早的 --start 时间。")
    background = white_background_mask(raw, width, height)
    ansi_rows, text_rows = [], []
    for y in range(height):
        ansi, text, previous_color = [], [], None
        for x in range(width):
            index = y * width + x
            if index in background:
                ansi.append("  ")
                text.append("  ")
                continue
            rgb = tuple(raw[index * 3:index * 3 + 3])
            luminance = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255
            color = BLOCK_PALETTE[-1] if luminance < 0.19 else min(
                BLOCK_PALETTE, key=lambda candidate: sum((a - b) ** 2 for a, b in zip(candidate, rgb)))
            if color != previous_color:
                ansi.append("\x1b[38;2;%d;%d;%dm" % color)
                previous_color = color
            ansi.append("██")
            text.append("██")
        ansi_rows.append("".join(ansi) + RESET)
        text_rows.append("".join(text))
    return {"ansi": ansi_rows, "text": text_rows}


def pixels_to_rgb_frame(raw: bytes, width: int, height: int,
                        matte: bool = True) -> dict[str, str]:
    """Keep actual RGB values, compressing losslessly rather than storing ANSI.

    White removal is restricted to border-connected near-white pixels so teeth
    enclosed by the mouth retain their source colours. No palette quantization
    or horizontally duplicated pixels is used by the high-resolution format.
    """
    if not 1 <= width <= RGB_MAX_WIDTH or not 1 <= height <= RGB_MAX_ROWS:
        raise ValueError("高清 RGB 画面尺寸超出允许范围。")
    if len(raw) != width * height * 3:
        raise ValueError("没有取得完整视频帧，请选择更早的 --start 时间。")
    rgb = bytearray(raw)
    if matte:
        for index in white_background_mask(raw, width, height):
            rgb[index * 3:index * 3 + 3] = b"\x12\x12\x12"
    return {"rgb_zlib": base64.b64encode(zlib.compress(rgb, level=9)).decode("ascii")}


def decode_frames(executable: str, video: Path, start: float, duration: float,
                  fps: int, width: int, crop: str, render: str = "block-ascii") -> list[tuple[int, int, bytes]]:
    """Decode the complete animation with one FFmpeg process at a steady cadence."""
    validate_settings(start, duration, fps, width, render)
    filters = [] if crop.lower() == "none" else ["crop=" + crop]
    if render == "truecolor-halfblock":
        filters += [f"fps={fps}",
                    f"scale={width}:{RGB_MAX_ROWS}:force_original_aspect_ratio=decrease:flags=lanczos",
                    "setsar=1"]
    elif render == "block-ascii":
        # Two full blocks are a square cell: one source pixel becomes ██.
        filters += [f"fps={fps}",
                    f"scale={width // 2}:{MAX_ROWS}:force_original_aspect_ratio=decrease:flags=area",
                    "setsar=1"]
    elif render == "ascii":
        filters += [f"fps={fps}",
                    f"scale={width}:{MAX_ROWS * 2}:force_original_aspect_ratio=decrease:flags=area",
                    "scale=iw:trunc(ih/2):flags=area", "setsar=1"]
    else:
        raise ValueError("--render 必须为 truecolor-halfblock、block-ascii 或 ascii。")
    raw = run_ffmpeg(executable, [
        "-ss", str(start), "-i", str(video.resolve()), "-t", str(duration),
        "-an", "-frames:v", str(math.ceil(duration * fps)), "-vf", ",".join(filters),
        "-c:v", "ppm", "-f", "image2pipe", "pipe:1",
    ])
    if render == "truecolor-halfblock":
        return parse_ppm_frames(raw, RGB_MAX_WIDTH, RGB_MAX_ROWS)
    return parse_ppm_frames(raw)


def pcm_to_wav(pcm: bytes) -> bytes:
    """Wrap finite mono 22050 Hz s16le PCM with an accurate seekable WAV header."""
    if len(pcm) % 2:
        raise ValueError("笑声音频采样数据不完整。")
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(22050)
        audio.writeframes(pcm)
    return output.getvalue()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg 可执行文件路径")
    parser.add_argument("--video", type=Path, default=ROOT.parent / "downloads" / "奶龙大笑【原版】_BV1p2Tp6REay.mp4")
    parser.add_argument("--output", type=Path, default=ROOT / ".local" / "laugh.json")
    parser.add_argument("--start", type=float, default=3.0, help="大笑片段起点，默认 3 秒")
    parser.add_argument("--duration", type=float, default=6.0, help="片段时长，默认 6 秒")
    parser.add_argument("--fps", type=int, default=24, help="每秒帧数，默认 24")
    parser.add_argument("--width", type=int, help="采样宽度；高清默认 128 像素，最大 192；旧模式默认 64 列，最大 72")
    parser.add_argument("--render", choices=("truecolor-halfblock", "block-ascii", "ascii"), default="truecolor-halfblock", help="默认保留原视频真彩色，播放时使用上下半格字符；可选旧色块或明暗字符")
    parser.add_argument("--crop", help="FFmpeg crop 表达式；高清默认突出头部、表情和手，旧模式保留全身；none 保留全画面")
    parser.add_argument("--keep-background", action="store_true", help="高清模式保留原视频白色背景")
    parser.add_argument("--no-audio", action="store_true", help="只提取画面")
    args = parser.parse_args()
    try:
        if args.width is None:
            args.width = RGB_WIDTH if args.render == "truecolor-halfblock" else BLOCK_WIDTH
        if args.crop is None:
            args.crop = DEFAULT_CLOSE_CROP if args.render == "truecolor-halfblock" else DEFAULT_CROP
        validate_settings(args.start, args.duration, args.fps, args.width, args.render)
        if not args.video.is_file():
            raise ValueError("请提供有效的本地视频文件。")
        executable = shutil.which(args.ffmpeg)
        if executable is None:
            raise ValueError("找不到 FFmpeg，请用 --ffmpeg 指定其完整路径。")
        output = args.output.resolve()
        if not output.is_relative_to((ROOT / ".local").resolve()):
            raise ValueError("视频衍生素材的 --output 必须位于本项目 .local/ 内。")
        decoded = decode_frames(executable, args.video, args.start, args.duration,
                                args.fps, args.width, args.crop, args.render)
        width, height = decoded[0][:2]
        high_resolution = args.render == "truecolor-halfblock"
        if high_resolution:
            frames = [pixels_to_rgb_frame(rgb, width, height, not args.keep_background)
                      for _, _, rgb in decoded]
            terminal_width = width
        else:
            frames = [pixels_to_frame(rgb, width, height, args.render) for _, _, rgb in decoded]
            terminal_width = len(frames[0]["text"][0])
        duration = len(frames) / args.fps
        source_digest = hashlib.sha256()
        with args.video.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                source_digest.update(chunk)
        source_sha256 = source_digest.hexdigest()
        payload = {
            "schema": "mcd-code-laugh-v3" if high_resolution else "mcd-code-laugh-v2",
            "private": True, "render": args.render,
            "cell_width": 2 if args.render == "block-ascii" else 1,
            "logical_width": width,
            "source_sha256": source_sha256,
            "width": terminal_width, "height": height, "fps": args.fps,
            "duration": duration, "frame_count": len(frames),
            "start": args.start, "frames": frames,
        }
        if high_resolution:
            payload.update(pixel_format="rgb24", crop=args.crop,
                           matte_background="#121212" if not args.keep_background else None)
            payload.pop("cell_width")
        audio_bytes = None
        if not args.no_audio:
            pcm = run_ffmpeg(executable, [
                "-ss", str(args.start), "-i", str(args.video.resolve()), "-t", str(duration),
                "-vn", "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", "-f", "s16le", "pipe:1",
            ])
            audio_bytes = pcm_to_wav(pcm)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > 24 * 1024 * 1024:
            raise ValueError("动画缓存超过 24 MiB，请降低宽度或时长。")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(output)
        audio = output.parent / "laugh.wav"
        if audio_bytes is not None:
            audio.write_bytes(audio_bytes)
        elif audio.exists():
            audio.unlink()
        print(f"已从原视频逐帧生成 {args.render} 大笑：{width} × {height} 采样，{len(frames)} 帧，{args.fps} fps，{duration:.2f} 秒。")
        if high_resolution:
            print("保留原片 RGB 真彩色与表情细节；播放时按终端窗口适配，用 ▀ 同时显示上下两个像素。")
        else:
            print(f"旧模式：{terminal_width} 列 × {height} 行。")
        print("非交互输出显示真实视频静帧。衍生素材仅保存在已忽略的 .local/。")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

