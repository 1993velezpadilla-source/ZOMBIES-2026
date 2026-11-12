#!/usr/bin/env python3
"""Fix Android fresh-install handling of compact XZ-ASSETS-1 game archives.

Preserve the FIX49C native bridge, APK resources, guns and textures. The
original Luanti UnzipService only extracts the single outer XZ member, not
the 9,666 files it contains. This patch adds a streaming XZ -> Zip extractor.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / "android/app/src/main/java/net/minetest/minetest/UnzipService.java"
gradle = root / "android/app/build.gradle"

def replace_once(path, old, new):
    s = path.read_text()
    if s.count(old) != 1:
        raise RuntimeError(f"Unsafe patch: {path}: expected exactly one match {old[:85]!r}, got {s.count(old)}")
    path.write_text(s.replace(old, new))

replace_once(java,
    "import java.util.zip.ZipInputStream;",
    "import java.util.zip.ZipInputStream;\nimport org.tukaani.xz.XZInputStream;")

replace_once(java,
    "\tprivate void unzip(Notification.Builder notificationBuilder, File zipFile, File userDataDirectory) throws IOException {\n",
    """\tprivate void unzip(Notification.Builder notificationBuilder, File zipFile, File userDataDirectory) throws IOException {
\t\t// XZ-ASSETS-1 archive has a single .xz entry containing an entire ZIP.
\t\t// A fresh install otherwise gets NO fonts/builtin/games and cannot boot.
\t\ttry (ZipFile wrapper = new ZipFile(zipFile)) {
\t\t\tif (wrapper.getEntry("luanti-assets.zip.xz") != null) {
\t\t\t\textractCompactAssets(notificationBuilder, wrapper, userDataDirectory);
\t\t\t\treturn;
\t\t\t}
\t\t}
""")

method = """
\t/**
\t * Extract XZ-ASSETS-1:NNNN compressed game archive on fresh Android installs.
\t * ZIP content is streamed and never materialized as a 1GB temporary file.
\t * Keep the regular ZIP extraction route for upstream/plain assets.
\t */
\tprivate void extractCompactAssets(Notification.Builder notificationBuilder,
\t\t\tZipFile wrapper, File userDataDirectory) throws IOException {
\t\tZipEntry wrapped = wrapper.getEntry("luanti-assets.zip.xz");
\t\tString comment = wrapper.getComment();
\t\tif (wrapped == null || wrapper.size() != 1 ||
\t\t\t\tcomment == null || !comment.startsWith("XZ-ASSETS-1:")) {
\t\t\tthrow new IOException("Invalid XZ-ASSETS-1 archive wrapper");
\t\t}
\t\tfinal int expected;
\t\ttry {
\t\t\texpected = Integer.parseInt(comment.substring("XZ-ASSETS-1:".length()).trim());
\t\t} catch (NumberFormatException e) {
\t\t\tthrow new IOException("Malformed compact asset entry count", e);
\t\t}
\t\tif (expected < 1000 || expected > 100000)
\t\t\tthrow new IOException("Unsafe compact asset entry count: " + expected);

\t\tfinal String root = userDataDirectory.getCanonicalPath() + File.separator;
\t\tint count = 0;
\t\tbyte[] readBuffer = new byte[65536];
\t\t// 128 MiB dictionary limit: avoid unbounded memory on Android.
\t\ttry (InputStream compressed = wrapper.getInputStream(wrapped);
\t\t\t\tXZInputStream decoded = new XZInputStream(compressed, 128 * 1024);
\t\t\t\tZipInputStream files = new ZipInputStream(decoded)) {
\t\t\tZipEntry entry;
\t\t\twhile ((entry = files.getNextEntry()) != null) {
\t\t\t\tFile destination = new File(userDataDirectory, entry.getName());
\t\t\t\tif (!destination.getCanonicalPath().startsWith(root))
\t\t\t\t\tthrow new IOException("Unsafe asset path: " + entry.getName());
\t\t\t\tif (entry.isDirectory()) {
\t\t\t\t\tif (!destination.isDirectory() && !destination.mkdirs())
\t\t\t\t\t\tthrow new IOException("Cannot create game asset directory: " + destination);
\t\t\t\t} else {
\t\t\t\t\tFile parent = destination.getParentFile();
\t\t\t\t\tif (parent != null && !parent.isDirectory() && !parent.mkdirs())
\t\t\t\t\t\tthrow new IOException("Cannot create asset parent: " + parent);
\t\t\t\t\ttry (OutputStream output = new FileOutputStream(destination)) {
\t\t\t\t\t\tint length;
\t\t\t\t\t\twhile ((length = files.read(readBuffer)) != -1)
\t\t\t\t\t\t\toutput.write(readBuffer, 0, length);
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tfiles.closeEntry();
\t\t\t\tif (++count > expected)
\t\t\t\t\tthrow new IOException("Compact archive has extra entries");
\t\t\t\tif (count % 32 == 0 || count == expected)
\t\t\t\t\tpublishProgress(notificationBuilder, R.string.loading,
\t\t\t\t\t\t\tMath.min(100, (int) (100L * count / expected)));
\t\t\t}
\t\t}
\t\tif (count != expected)
\t\t\tthrow new IOException("Incomplete compact assets: " + count + "/" + expected);
\t\t// Fail at extraction, not after launching Luanti with missing fonts.
\t\tfor (String required : new String[] {
\t\t\t\t"fonts/Arimo-Regular.ttf", "fonts/DroidSansFallbackFull.ttf",
\t\t\t\t"builtin/mainmenu/init.lua",
\t\t\t\t"games/voxelibre/mods/xz_zombies_classic/init.lua"}) {
\t\t\tif (!new File(userDataDirectory, required).isFile())
\t\t\t\tthrow new IOException("Essential game asset missing: " + required);
\t\t}
\t\tLog.i("UnzipService", "Extracted " + count + " nested Luanti assets and verified fonts");
\t}

"""
replace_once(java, "\tprivate boolean resultSent = false;", method + "\tprivate boolean resultSent = false;")
replace_once(gradle,
    "\timplementation 'androidx.appcompat:appcompat:1.7.1'",
    "\timplementation 'androidx.appcompat:appcompat:1.7.1'\n\timplementation 'org.tukaani:xz:1.12'")

assert 'XZInputStream decoded' in java.read_text()
assert 'org.tukaani:xz:1.12' in gradle.read_text()
print("FIX50B: added streaming XZ compact archive extractor with font/game assertions")
