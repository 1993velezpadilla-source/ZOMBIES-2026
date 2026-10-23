#!/usr/bin/env python3
"""Download a user-specified MediaFire APK without executing it.

Validates archive signature, basic Android package structure, and records SHA-256.
No code from the APK is run.
"""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import zipfile
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup

USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
DOWNLOAD_DIR = Path("_mediafire_import")
NAME = "COD4.apk"


def is_download_url(link: str) -> bool:
    if not link or not link.startswith("https://"):
        return False
    host = (urlparse(link).hostname or "").lower()
    return host.endswith(".mediafire.com") and (
        host.startswith("download") or host.startswith("www") is False
    )


def extract_link(raw_html: str) -> str | None:
    soup = BeautifulSoup(raw_html, "html.parser")
    button = soup.find(id="downloadButton")
    if button:
        href = button.get("href", "")
        if is_download_url(href):
            return href
    for tag in soup.select("a[href]"):
        link = tag.get("href", "")
        if is_download_url(link):
            return link
    raw_html = html.unescape(raw_html).replace(r"\/", "/")
    for match in re.finditer(r"https://(?:download[0-9]*|[a-z0-9-]+)\.mediafire\.com/[^\"'\s<>]+", raw_html):
        link = match.group(0)
        if is_download_url(link):
            return link
    return None


def discover_with_requests(page_url: str, session: requests.Session) -> str | None:
    r = session.get(page_url, timeout=45, headers={"Referer": "https://www.mediafire.com/"})
    print(f"MediaFire page HTTP status: {r.status_code}, content length: {len(r.content)}", flush=True)
    r.raise_for_status()
    return extract_link(r.text)


def discover_with_browser(page_url: str) -> str:
    """Browser fallback for MediaFire pages that render download link using JS."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(user_agent=USER_AGENT, viewport={"width": 1250, "height": 800})
        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(6000)
            button = page.locator("#downloadButton")
            if button.count():
                for _ in range(15):
                    link = button.first.get_attribute("href")
                    if is_download_url(link):
                        return link
                    page.wait_for_timeout(1000)
            link = extract_link(page.content())
            if link:
                return link
            raise RuntimeError("Browser loaded page but no downloadable link was found (file unavailable or blocked).")
        finally:
            browser.close()


def stream_download(session: requests.Session, url: str, file_path: Path) -> int:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(3):
        if attempt:
            time.sleep(attempt * 3)
        try:
            with session.get(url, stream=True, timeout=(45, 180),
                             headers={"Referer": "https://www.mediafire.com/"}) as r:
                print(f"Download HTTP status: {r.status_code}", flush=True)
                r.raise_for_status()
                ct = r.headers.get("Content-Type", "").lower()
                if "text/html" in ct:
                    raise ValueError("MediaFire returned HTML, not APK bytes")
                declared = int(r.headers.get("Content-Length", 0))
                total = 0
                with file_path.open("wb") as out:
                    for chunk in r.iter_content(4 * 1024 * 1024):
                        if chunk:
                            out.write(chunk)
                            total += len(chunk)
                            if total > 32 * 1024 ** 3:
                                raise ValueError("File exceeds safety limit (32 GiB)")
                if declared and total != declared:
                    raise ValueError(f"Truncated download: {total} / {declared}")
                return total
        except Exception as exc:
            last_error = exc
            print(f"Download attempt {attempt+1}/3 failed: {exc}", flush=True)
    raise RuntimeError(f"Failed to download MediaFire APK after retries: {last_error}")


def validate(file_path: Path, source: str) -> None:
    if not zipfile.is_zipfile(file_path):
        raise ValueError("Downloaded object is NOT a valid APK/ZIP archive.")
    with zipfile.ZipFile(file_path) as archive:
        files = archive.namelist()
        if "AndroidManifest.xml" not in files:
            raise ValueError("Valid ZIP but no AndroidManifest.xml: not an APK.")
        if not any(x.startswith("META-INF/") for x in files):
            print("NOTE: No META-INF directory found; may use APK signature v2/v3.", flush=True)
        num_files = len(files)
    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            digest.update(block)
    manifest = {
        "source": source,
        "filename": NAME,
        "bytes": file_path.stat().st_size,
        "sha256": digest.hexdigest(),
        "zip_entries": num_files,
        "android_manifest_present": True,
        "execution_performed": False,
    }
    (DOWNLOAD_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("VALIDATION:", json.dumps(manifest), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.hostname not in ("mediafire.com", "www.mediafire.com"):
        raise SystemExit("Refusing non-MediaFire source URL.")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    link = discover_with_requests(args.url, session)
    if not link:
        print("No static MediaFire link; using headless-browser fallback.", flush=True)
        link = discover_with_browser(args.url)
    print("Resolved MediaFire CDN host:", urlparse(link).hostname, flush=True)
    output = DOWNLOAD_DIR / NAME
    amount = stream_download(session, link, output)
    print("Downloaded bytes:", amount, flush=True)
    validate(output, args.url)


if __name__ == "__main__":
    main()
