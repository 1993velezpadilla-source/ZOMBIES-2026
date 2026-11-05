#!/usr/bin/env python3
"""Package upstream Luanti 5.18.0 + unmodified VoxeLibre into a separate Android app.

This script edits only the local checkout used by GitHub Actions.
"""
from pathlib import Path
import sys

PACKAGE = "com.xziel.voxelsandbox"
APP_NAME = "Voxel Sandbox Dev"


def replace_checked(path: Path, old: str, new: str) -> None:
    contents = path.read_text(encoding="utf-8")
    if old not in contents:
        raise RuntimeError(f"{path}: expected upstream text not found: {old[:120]!r}")
    path.write_text(contents.replace(old, new), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: prepare.py /path/to/luanti")
    root = Path(sys.argv[1]).resolve()
    game = root / "games" / "voxelibre"
    if not (game / "game.conf").is_file() or not (game / "mods").is_dir():
        raise RuntimeError(f"VoxeLibre incomplete at {game}")

    app = root / "android" / "app"
    app_gradle = app / "build.gradle"
    native_gradle = root / "android" / "native" / "build.gradle"
    manifest = app / "src/main/AndroidManifest.xml"
    activity = app / "src/main/java/net/minetest/minetest/GameActivity.java"
    strings = app / "src/main/res/values/strings.xml"

    # Non-conflicting Android package; retain upstream Java namespace.
    replace_checked(app_gradle, "applicationId 'net.minetest.minetest'",
                    f"applicationId '{PACKAGE}'")
    replace_checked(manifest, "net.minetest.minetest.fileprovider",
                    f"{PACKAGE}.fileprovider")
    replace_checked(manifest, "net.minetest.minetest.documents",
                    f"{PACKAGE}.documents")
    replace_checked(activity, '"net.minetest.minetest.fileprovider"',
                    f'"{PACKAGE}.fileprovider"')
    replace_checked(strings, '<string name="label">Luanti</string>',
                    f'<string name="label">{APP_NAME}</string>')

    # Initial Android test build targets ARM64 only.
    original = "include 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'"
    replace_checked(app_gradle, original, "include 'arm64-v8a'")
    replace_checked(native_gradle, original, "include 'arm64-v8a'")

    # Luanti 5.18 no longer packages a game by default.
    # Add VoxeLibre to the shared assets ZIP before zipAssets runs.
    with app_gradle.open("a", encoding="utf-8") as fh:
        fh.write("""
\n// Ship VoxeLibre inside the initial APK, no ContentDB download required.
tasks.named('prepareAssets') {
    doLast {
        copy {
            from "${projRoot}/games/voxelibre"
            into "${assetsFolder}/games/voxelibre"
            exclude ".git/**"
        }
    }
}
""")
    print(f"Prepared {APP_NAME} ({PACKAGE}); game: {game}")


if __name__ == "__main__":
    main()
