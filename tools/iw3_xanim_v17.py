#!/usr/bin/env python3
"""Strict, bounded reader for IW3 OpenAssetTools raw XANIM v17.

Port of the v17 layout from OpenAssetTools CompiledXAnimLoader.cpp.
Reads data in memory with bounds checking; no game files are ever checked in.
This module does not claim gameplay-correct bone retargeting or Godot animations.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import struct

MAX_FILE = 32 * 1024 * 1024
MAX_BONES = 512
MAX_FRAMES = 32767
MAX_KEYS = 32768


class AnimFormatError(ValueError):
    pass


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read(self, size: int) -> bytes:
        if size < 0 or self.pos + size > len(self.data):
            raise AnimFormatError(f"truncated animation at byte {self.pos} ({size} requested)")
        buf = self.data[self.pos:self.pos + size]
        self.pos += size
        return buf

    def unpack(self, spec: str):
        return struct.unpack("<" + spec, self.read(struct.calcsize("<" + spec)))

    def cstring(self) -> str:
        start = self.pos
        end = self.data.find(b"\x00", start, min(len(self.data), start + 256))
        if end == -1:
            raise AnimFormatError("unterminated xanim string")
        self.pos = end + 1
        try:
            value = self.data[start:end].decode("utf-8")
        except UnicodeDecodeError as e:
            raise AnimFormatError("invalid string encoding") from e
        if not value or any(ord(ch) < 32 for ch in value):
            raise AnimFormatError("invalid xanim bone/notetrack name")
        return value


@dataclass
class Track:
    indices: list[int]
    values: list[tuple[float, ...]]


@dataclass
class Bone:
    name: str
    rotations: Track | None
    translations: Track | None
    rotation_type: str
    translation_type: str


@dataclass
class XAnim:
    name: str
    frame_count: int
    fps: int
    looping: bool
    flags: int
    asset_type: int
    bones: list[Bone]
    delta_quat: Track | None
    delta_trans: Track | None
    notes: list[tuple[str, int]]
    trailing_bytes: int


def read_indices(reader: Reader, n: int, num_loop_frames: int, short_index: bool) -> list[int]:
    if n > MAX_KEYS or n < 0:
        raise AnimFormatError("index count out of bounds")
    if n >= num_loop_frames:
        return list(range(n))  # OAT sequential implicit indices.
    if not short_index:
        return list(reader.unpack(f"{n}B"))
    return list(reader.unpack(f"{n}H"))


def read_quat(reader: Reader, half: bool, flip: bool = False) -> tuple[float, float, float, float]:
    if half:
        z, = reader.unpack("h")
        w = round(math.sqrt(max(0, 0x3FFF0001 - z * z)))
        vec = (0, 0, z, w)  # HALF_QUAT is 2D yaw along Z in IW3 coordinates (needs visual gate).
    else:
        x, y, z = reader.unpack("hhh")
        w = round(math.sqrt(max(0, 0x3FFF0001 - x*x - y*y - z*z)))
        vec = (x, y, z, w)
    if flip:
        vec = tuple(-value for value in vec)
    normal = math.sqrt(sum(x*x for x in vec))
    if normal < 1:
        raise AnimFormatError("zero quaternion")
    return tuple(float(x)/normal for x in vec)


def read_rot_track(reader: Reader, frames: int, small_index: bool, half: bool, flip: bool) -> Track | None:
    n, = reader.unpack("H")
    if n == 0:
        return None
    if n == 1:
        return Track([0], [read_quat(reader, half, flip)])
    indices = read_indices(reader, n, frames, not small_index)
    values = []
    for _ in range(n):
        q = read_quat(reader, half, flip if not values else False)
        if values and sum(a*b for a,b in zip(values[-1], q)) < 0:
            q = tuple(-x for x in q)
        values.append(q)
    return Track(indices, values)


def read_trans_track(reader: Reader, frames: int, small_index: bool) -> Track | None:
    n, = reader.unpack("H")
    if n == 0:
        return None
    if n == 1:
        return Track([0], [reader.unpack("fff")])
    indices = read_indices(reader, n, frames, not small_index)
    tiny, = reader.unpack("B")
    if tiny not in (0, 1):
        raise AnimFormatError("bad smallTrans bit")
    mins = reader.unpack("fff")
    raw_size = reader.unpack("fff")
    factor = 0.003921568859368563 if tiny else 0.00001525902189314365
    size = [s * factor for s in raw_size]
    values = []
    for _ in range(n):
        values.append(tuple(mins[i] + v * size[i] for i,v in
                            enumerate(reader.unpack("BBB" if tiny else "HHH"))))
    return Track(indices, values)


def read_delta(reader: Reader, frames: int, small_index: bool):
    n, = reader.unpack("H")
    if n == 0:
        quat = None
    elif n == 1:
        quat = Track([0], [read_quat(reader, True)])
    else:
        ix = read_indices(reader, n, frames, not small_index)
        values = [read_quat(reader, True) for _ in range(n)]
        quat = Track(ix, values)
    trans = read_trans_track(reader, frames, small_index)
    return quat, trans


def load_xanim(path: Path) -> XAnim:
    if path.stat().st_size > MAX_FILE:
        raise AnimFormatError("xanim over safety limit")
    r = Reader(path.read_bytes())
    version, frame_header, bone_count, flags, asset_type, fps = r.unpack("HHHBBH")
    if version != 17:
        raise AnimFormatError(f"unsupported xanim version: {version}")
    if not 0 <= bone_count <= MAX_BONES or not 1 <= frame_header <= MAX_FRAMES or not 1 <= fps <= 240:
        raise AnimFormatError("invalid bone/frame/fps counts")
    looped = bool(flags & 1)
    num_loop_frames = frame_header + int(looped)
    small_index = num_loop_frames - 1 < 256
    delta_rot, delta_trans = read_delta(r, num_loop_frames, small_index) if flags & 2 else (None, None)
    bone_names = []
    bits = []
    if bone_count:
        size = (bone_count + 7)//8
        flip_bits = r.read(size)
        half_bits = r.read(size)
        bone_names = [r.cstring() for _ in range(bone_count)]
        bits = [(bool(flip_bits[i//8] & (1 << (i%8))),
                 bool(half_bits[i//8] & (1 << (i%8)))) for i in range(bone_count)]
    bones = []
    for name, (flip, half) in zip(bone_names, bits):
        rot = read_rot_track(r, num_loop_frames, small_index, half, flip)
        trans = read_trans_track(r, num_loop_frames, small_index)
        bones.append(Bone(name, rot, trans, "half" if half else "full",
                          "track" if trans and len(trans.values)>1 else
                          ("constant" if trans else "none")))
    n_notes, = r.unpack("B")
    notes = [(r.cstring(), r.unpack("H")[0]) for _ in range(n_notes)]
    trail = len(r.data) - r.pos
    if trail:
        raise AnimFormatError(f"unexpected trailing {trail} bytes")
    return XAnim(path.name, num_loop_frames - 1, fps, looped, flags,
                 asset_type, bones, delta_rot, delta_trans, notes, trail)


def duration(anim: XAnim) -> float:
    return anim.frame_count / anim.fps
