"""Guard the SAF importer for user-owned IW3 data and its honest runtime boundary."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA_ROOT = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe"
IMPORTER = JAVA_ROOT / "GameDataImporter.java"
ACTIVITY = JAVA_ROOT / "MainActivity.java"
BRIDGE = JAVA_ROOT / "EngineBridge.java"


class AndroidGameDataImportTests(unittest.TestCase):
    def test_importer_uses_saf_and_preserves_original_game_relative_paths(self):
        source = IMPORTER.read_text(encoding="utf-8")
        self.assertIn("DocumentsContract.getTreeDocumentId(treeUri)", source)
        self.assertIn("DocumentsContract.buildChildDocumentsUriUsingTree", source)
        self.assertIn("DocumentsContract.buildDocumentUriUsingTree", source)
        self.assertIn('topLevelDirectories.contains("main")', source)
        self.assertIn('topLevelDirectories.contains("zone")', source)
        self.assertIn('lower.endsWith(".iwd")', source)
        self.assertIn('lower.endsWith(".ff")', source)
        self.assertIn('parentPath + "/" + pathSegment', source)
        self.assertIn('directory ? displayName.toLowerCase(Locale.ROOT) : displayName', source)
        self.assertIn("getCanonicalPath()", source)
        self.assertIn('targetPath.startsWith(rootPath + File.separator)', source)
        self.assertIn('name.indexOf(\'/\') < 0', source)
        self.assertIn("name.indexOf(0) < 0", source)

    def test_importer_never_packages_assets_or_claims_engine_loading(self):
        source = IMPORTER.read_text(encoding="utf-8")
        self.assertIn("user's own original IW3 data files", source)
        self.assertIn("does not decrypt, patch, redistribute, mount FastFiles, load a map", source)
        self.assertNotIn("assets/", source)
        self.assertNotIn("third_party/KisakCOD", source)

    def test_activity_requests_persisted_user_permission_and_imports_into_private_root(self):
        activity = ACTIVITY.read_text(encoding="utf-8")
        self.assertIn("Intent.ACTION_OPEN_DOCUMENT_TREE", activity)
        self.assertIn("Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION", activity)
        self.assertIn("takePersistableUriPermission", activity)
        self.assertIn("GameDataImporter.importTree(this, treeUri, getFilesDir())", activity)
        self.assertIn("IW3_GAME_DATA_IMPORT_PASS", activity)
        self.assertIn("Original FS/FastFile/map loading is still pending.", activity)
        self.assertIn('setContentDescription("IW3 native diagnostic touch surface")', activity)
        self.assertIn("label.setOnTouchListener((view, motion) -> onTouchEvent(motion))", activity)

    def test_native_root_and_bridge_remain_explicitly_diagnostic(self):
        activity = ACTIVITY.read_text(encoding="utf-8")
        bridge = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("EngineBridge.nativeSetDataRoot(getFilesDir().getAbsolutePath())", activity)
        self.assertIn("The game frame/CL_CreateCmd does not consume this adapter yet.", bridge)
        self.assertIn("actual IW3 fastfile parsing is pending", bridge)


if __name__ == "__main__":
    unittest.main()
