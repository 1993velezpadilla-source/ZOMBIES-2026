#!/usr/bin/env python3
"""Harden existing Luanti 5.18.0 Android font startup, preserving FIX54 gameplay."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / 'android/app/src/main/java/net/minetest/minetest'
utils = java / 'Utils.java'
service = java / 'UnzipService.java'

def replace_once(path, old, new):
    data = path.read_text()
    if data.count(old) != 1:
        raise RuntimeError(f'Unexpected upstream source in {path}: expected 1 instance, got {data.count(old)}')
    path.write_text(data.replace(old, new))

replace_once(utils,
    """		return userDataDirectory.isDirectory() &&
			new File(userDataDirectory, "builtin").isDirectory() &&
			new File(userDataDirectory, "client").isDirectory() &&
			new File(userDataDirectory, "textures").isDirectory();""",
    """		// Top-level folders are not proof of a completed install. A killed
		// extraction previously allowed the engine to start with missing fonts.
		File mainFont = new File(userDataDirectory, "fonts/Arimo-Regular.ttf");
		File fallback = new File(userDataDirectory, "fonts/DroidSansFallbackFull.ttf");
		File game = new File(userDataDirectory,
			"games/voxelibre/mods/xz_zombies_classic/init.lua");
		return userDataDirectory.isDirectory() &&
			new File(userDataDirectory, "builtin/mainmenu/init.lua").isFile() &&
			new File(userDataDirectory, "client").isDirectory() &&
			new File(userDataDirectory, "textures").isDirectory() &&
			mainFont.isFile() && mainFont.length() > 100000 &&
			fallback.isFile() && fallback.length() > 100000 &&
			game.isFile() && game.length() > 1000;""")

replace_once(service,
    '	private boolean isSuccess = true;',
    """	// Never report successful extraction if Android destroys the service
	// before the large nested archive has finished unpacking.
	private boolean isSuccess = false;""")
if 'extractCompactAssets' not in service.read_text():
    raise RuntimeError('Proven FIX50B XZ decoder not applied; refusing unsafe patch')
assert 'mainFont.length() > 100000' in utils.read_text()
assert 'isSuccess = false;' in service.read_text()
print('FIX54B guarded font startup; no native/game files modified')
