#!/usr/bin/env python3
"""Select a real Android touch target from UIAutomator bounds without inventing a scale.

UIAutomator node bounds are already expressed in the active display coordinate
space. Scaling them by the largest *visible node* is wrong when a modal dialog
does not cover the whole display (it moves taps outside the button).
"""
from __future__ import annotations

import argparse
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
TARGET_PACKAGE = "org.z2026.iw3nativeprobe"


def _bounds(node: ET.Element) -> Optional[tuple[int, int, int, int]]:
    match = BOUNDS_RE.fullmatch(node.get("bounds", ""))
    if not match:
        return None
    x0, y0, x1, y1 = map(int, match.groups())
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _center_in_screen(
    node: ET.Element, screen_w: int, screen_h: int
) -> Optional[tuple[int, int]]:
    bounds = _bounds(node)
    if bounds is None:
        return None
    x0, y0, x1, y1 = bounds
    x = (x0 + x1) // 2
    y = (y0 + y1) // 2
    # Never extrapolate from unrelated node extents. If a node is outside the
    # captured framebuffer, decline to tap and let the caller retry/report it.
    if not (0 <= x < screen_w and 0 <= y < screen_h):
        return None
    return x, y


def select_target(
    xml_text: str, screen_w: int, screen_h: int
) -> tuple[str, int, int]:
    if screen_w <= 0 or screen_h <= 0:
        raise ValueError("Screenshot dimensions must be positive")
    root = ET.fromstring(xml_text)
    nodes = list(root.iter("node"))

    # Resolve the named system modal first; do not touch an app node hidden
    # behind the launcher ANR dialog.
    quickstep_modal = any(
        node.get("text") == "Quickstep isn't responding" for node in nodes
    )
    if quickstep_modal:
        for node in nodes:
            if node.get("resource-id") == "android:id/aerr_wait":
                point = _center_in_screen(node, screen_w, screen_h)
                if point:
                    return "quickstep_anr", point[0], point[1]
        return "retry", 0, 0

    for node in nodes:
        if (
            node.get("package") == TARGET_PACKAGE
            and (
                node.get("class") == "android.widget.TextView"
                or node.get("content-desc")
                == "IW3 native diagnostic touch surface"
            )
        ):
            point = _center_in_screen(node, screen_w, screen_h)
            if point:
                return "target", point[0], point[1]
    return "retry", 0, 0


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Screenshot is not a valid PNG header")
    return struct.unpack(">II", header[16:24])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xml", type=Path)
    parser.add_argument("screenshot", type=Path)
    args = parser.parse_args()
    width, height = _png_size(args.screenshot)
    state, x, y = select_target(
        args.xml.read_text(encoding="utf-8"), width, height
    )
    print(state, x, y)


if __name__ == "__main__":
    main()
