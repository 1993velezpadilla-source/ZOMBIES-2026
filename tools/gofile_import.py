#!/usr/bin/env python3
"""Download ZIP files from a shared Gofile folder using its guest web API.

Implements the website-token generation introduced by Gofile in 2026.
Downloads bytes without executing or extracting uploaded archives.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import sys
import time

import requests

API = "https://api.gofile.io"
AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
LANGUAGE = "en-US"
SALT = os.getenv("GOFILE_WT_SALT", "12af056dacea0b")
ROOT = Path("_gofile_import")


def safe_name(value: str) -> str:
    name = Path(value.replace("\\", "/")).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if name in ("", ".", ".."):
        raise ValueError(f"Unsafe or empty file name: {value!r}")
    return name


def new_guest(session: requests.Session) -> str:
    response = session.post(f"{API}/accounts",
                            headers={"User-Agent": AGENT,
                                     "Origin": "https://gofile.io"},
                            timeout=45)
    response.raise_for_status()
    result = response.json()
    if result.get("status") != "ok":
        raise RuntimeError(f"Gofile guest account failed: {result.get('status')}")
    return result["data"]["token"]


def listing(session: requests.Session, folder_id: str, token: str) -> dict:
    for offset in (0, -1):
        window = int(time.time() // 14400) + offset
        raw = f"{AGENT}::{LANGUAGE}::{token}::{window}::{SALT}"
        website_token = hashlib.sha256(raw.encode()).hexdigest()
        response = session.get(
            f"{API}/contents/{folder_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Website-Token": website_token,
                "X-BL": LANGUAGE,
                "User-Agent": AGENT,
                "Origin": "https://gofile.io",
                "Referer": "https://gofile.io/",
                "Accept": "*/*",
            },
            params={
                "contentFilter": "",
                "page": 1,
                "pageSize": 1000,
                "sortField": "createTime",
                "sortDirection": -1,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            return data["data"]
        if data.get("status") == "error-notPremium":
            continue
        raise RuntimeError(f"Cannot list {folder_id}: {data.get('status')}")
    raise RuntimeError(
        "Gofile rejected the guest website token (error-notPremium). "
        "The salt in gofile.io/dist/js/wt.obf.js may have changed."
    )


def download(session: requests.Session, child: dict, directory: Path, token: str) -> None:
    link = child.get("link")
    if not link or not str(link).startswith("https://"):
        raise RuntimeError(f"Missing HTTPS download link for {child.get('name')}")
    filename = safe_name(child["name"])
    target = directory / filename
    if target.exists():
        raise RuntimeError(f"Duplicate filename: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading ZIP: {filename} (reported {child.get('size', 'unknown')} bytes)", flush=True)
    with session.get(
        link,
        headers={
            "User-Agent": AGENT,
            "Cookie": f"accountToken={token}",
            "Referer": "https://gofile.io/",
        },
        stream=True,
        timeout=(30, 120),
        allow_redirects=True,
    ) as response:
        response.raise_for_status()
        ctype = response.headers.get("Content-Type", "").lower()
        if "text/html" in ctype:
            raise RuntimeError(f"Got HTML instead of ZIP for {filename}")
        with target.open("wb") as out:
            for chunk in response.iter_content(2 * 1024 * 1024):
                if chunk:
                    out.write(chunk)
    expected = child.get("size")
    if expected is not None and int(expected) != target.stat().st_size:
        raise RuntimeError(f"Size mismatch for {filename}: {target.stat().st_size} != {expected}")
    checksum = child.get("md5")
    if checksum:
        hasher = hashlib.md5()
        with target.open("rb") as inp:
            for block in iter(lambda: inp.read(2 * 1024 * 1024), b""):
                hasher.update(block)
        if hasher.hexdigest().lower() != checksum.lower():
            raise RuntimeError(f"MD5 mismatch for {filename}")
    print(f"ZIP downloaded: {target} ({target.stat().st_size} bytes)", flush=True)


def traverse(session: requests.Session, folder_id: str, token: str,
             directory: Path, depth: int = 0) -> int:
    if depth > 12:
        raise RuntimeError("Folder nesting exceeds safety limit")
    data = listing(session, folder_id, token)
    children = data.get("children") or data.get("contents") or {}
    if isinstance(children, list):
        children = {item["id"]: item for item in children}
    downloaded = 0
    for child in children.values():
        name = safe_name(child.get("name", "unnamed"))
        if child.get("type") == "folder":
            downloaded += traverse(session, child["id"], token,
                                   directory / name, depth + 1)
        elif child.get("type") == "file" and name.lower().endswith(".zip"):
            download(session, child, directory, token)
            downloaded += 1
    return downloaded


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/gofile_import.py Gofile-folder-ID")
    ROOT.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        token = new_guest(session)
        num = traverse(session, sys.argv[1], token, ROOT)
    if num < 1:
        raise SystemExit("Folder accessible but no ZIP archive found.")
    print(f"Downloaded {num} ZIP archive(s).", flush=True)


if __name__ == "__main__":
    main()
