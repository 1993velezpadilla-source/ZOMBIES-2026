package org.z2026.iw3nativeprobe;

import android.content.ContentResolver;
import android.content.Context;
import android.system.ErrnoException;
import android.system.Os;
import android.util.Log;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Imports only a user's own original IW3 data files into the app-private root.
 *
 * This does not decrypt, patch, redistribute, mount FastFiles, load a map, or
 * start gameplay. The original engine filesystem integration remains pending.
 */
public final class GameDataImporter {
    private static final String[] COLUMNS = {
        DocumentsContract.Document.COLUMN_DOCUMENT_ID,
        DocumentsContract.Document.COLUMN_DISPLAY_NAME,
        DocumentsContract.Document.COLUMN_MIME_TYPE
    };

    // A SAF provider is external input: bound traversal even if it exposes a
    // cyclic or adversarial document tree.
    private static final int MAX_DIRECTORY_DEPTH = 16;
    private static final int MAX_DOCUMENT_NODES = 32768;
    private static final int MAX_SOURCE_FILES = 16384;

    private GameDataImporter() {}

    public static final class Summary {
        public final int iwdFiles;
        public final int fastFiles;
        public final long bytesCopied;

        private Summary(int iwdFiles, int fastFiles, long bytesCopied) {
            this.iwdFiles = iwdFiles;
            this.fastFiles = fastFiles;
            this.bytesCopied = bytesCopied;
        }
    }

    private static final class SourceFile {
        final Uri uri;
        final String relativePath;
        final boolean iwd;

        SourceFile(Uri uri, String relativePath, boolean iwd) {
            this.uri = uri;
            this.relativePath = relativePath;
            this.iwd = iwd;
        }
    }

    /**
     * Reads a selected COD4 game root (containing main/ and zone/) through
     * Android's Storage Access Framework and copies only .iwd/.ff files.
     * Relative paths are preserved for the original filesystem's search paths.
     */
    public static Summary importTree(Context context, Uri treeUri, File destinationRoot)
            throws IOException {
        if (context == null || treeUri == null || destinationRoot == null) {
            throw new IOException("Missing source tree or destination");
        }

        ContentResolver resolver = context.getContentResolver();
        final String rootDocumentId;
        try {
            rootDocumentId = DocumentsContract.getTreeDocumentId(treeUri);
        } catch (RuntimeException invalidTree) {
            throw new IOException("Selected URI is not a readable document tree", invalidTree);
        }

        List<SourceFile> sourceFiles = new ArrayList<>();
        Set<String> visitedDocumentIds = new HashSet<>();
        Set<String> topLevelDirectories = new HashSet<>();
        Set<String> normalizedDestinationPaths = new HashSet<>();
        collect(resolver, treeUri, rootDocumentId, "", 0, visitedDocumentIds,
                topLevelDirectories, normalizedDestinationPaths, sourceFiles);

        if (!topLevelDirectories.contains("main") || !topLevelDirectories.contains("zone")) {
            throw new IOException("Select the game root containing both main/ and zone/");
        }

        int expectedIwd = 0;
        int expectedFast = 0;
        for (SourceFile file : sourceFiles) {
            if (file.iwd) expectedIwd++;
            else expectedFast++;
        }
        if (expectedIwd == 0 || expectedFast == 0) {
            throw new IOException("Game root must contain at least one .iwd and one .ff file");
        }

        File root = destinationRoot.getCanonicalFile();
        if (!root.isDirectory() && !root.mkdirs()) {
            throw new IOException("Cannot create app-private game-data directory");
        }
        final String rootPath = root.getCanonicalPath();
        int copiedIwd = 0;
        int copiedFast = 0;
        long bytesCopied = 0;

        for (SourceFile source : sourceFiles) {
            File target = new File(root, source.relativePath);
            File parent = target.getParentFile();
            if (parent == null || (!parent.isDirectory() && !parent.mkdirs())) {
                throw new IOException("Cannot create game-data subdirectory");
            }

            // Resolve existing parent/target components before opening anything.
            // A symlink that escapes filesDir must never become an import target.
            String parentPath = parent.getCanonicalPath();
            if (!parentPath.startsWith(rootPath + File.separator)) {
                throw new IOException("Refusing parent outside app-private root");
            }
            String targetPath = target.getCanonicalPath();
            if (!targetPath.startsWith(rootPath + File.separator)) {
                throw new IOException("Refusing path outside app-private root");
            }

            // Create a unique file exclusively in the destination directory.
            // Unlike a fixed ".part" name, this cannot follow a stale/dangling
            // symlink left at a predictable temporary path.
            File partial = File.createTempFile(target.getName() + ".iw3-import-", ".part", parent);
            boolean finalized = false;
            long fileBytes = 0;
            try {
                try (InputStream input = resolver.openInputStream(source.uri);
                     FileOutputStream output = new FileOutputStream(partial, false)) {
                    if (input == null) throw new IOException("Document provider returned no stream");
                    byte[] buffer = new byte[64 * 1024];
                    int read;
                    while ((read = input.read(buffer)) != -1) {
                        output.write(buffer, 0, read);
                        fileBytes += read;
                    }
                    output.getFD().sync();
                }

                // POSIX rename on the same private filesystem atomically replaces
                // an older file. If rename fails, the old target remains intact.
                try {
                    Os.rename(partial.getAbsolutePath(), target.getAbsolutePath());
                    finalized = true;
                } catch (ErrnoException renameFailure) {
                    throw new IOException("Cannot atomically finalize imported game-data file",
                            renameFailure);
                }
            } finally {
                if (!finalized && partial.exists() && !partial.delete()) {
                    Log.w("IW3NativeGate", "Could not remove failed import temporary file: "
                            + partial.getName());
                }
            }
            bytesCopied += fileBytes;
            if (source.iwd) copiedIwd++;
            else copiedFast++;
        }

        return new Summary(copiedIwd, copiedFast, bytesCopied);
    }

    private static void collect(ContentResolver resolver, Uri treeUri, String parentId,
            String parentPath, int depth, Set<String> visitedDocumentIds,
            Set<String> topLevelDirectories, Set<String> normalizedDestinationPaths,
            List<SourceFile> files) throws IOException {
        if (depth > MAX_DIRECTORY_DEPTH) {
            throw new IOException("Selected game-data tree exceeds safe directory depth");
        }
        if (!visitedDocumentIds.add(parentId)) return;
        if (visitedDocumentIds.size() > MAX_DOCUMENT_NODES) {
            throw new IOException("Selected game-data tree exceeds safe document count");
        }

        Uri childrenUri = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, parentId);
        try (Cursor cursor = resolver.query(childrenUri, COLUMNS, null, null, null)) {
            if (cursor == null) throw new IOException("Document provider could not enumerate game data");
            while (cursor.moveToNext()) {
                String documentId = cursor.getString(0);
                String displayName = cursor.getString(1);
                String mimeType = cursor.getString(2);
                if (!safeSegment(displayName) || documentId == null || documentId.isEmpty()) {
                    throw new IOException("Unsafe or unnamed document in selected game root");
                }

                boolean directory = DocumentsContract.Document.MIME_TYPE_DIR.equals(mimeType);
                if (depth == 0 && directory) {
                    String normalizedDirectory = displayName.toLowerCase(Locale.ROOT);
                    topLevelDirectories.add(normalizedDirectory);
                    // COD4 assets needed by the original SP filesystem live in
                    // main/ and zone/. Avoid walking unrelated user directories.
                    if (!"main".equals(normalizedDirectory) && !"zone".equals(normalizedDirectory)) continue;
                }

                // POSIX lookup is case-sensitive. Normalize directory
                // components (main/zone/english) to the paths used by IW3,
                // while preserving each original asset filename.
                String pathSegment = directory ? displayName.toLowerCase(Locale.ROOT) : displayName;
                String relativePath = parentPath.isEmpty()
                        ? pathSegment : parentPath + "/" + pathSegment;
                if (directory) {
                    // Only main/ and zone/ are imported. Reject directory names
                    // that normalize onto an already-seen destination directory.
                    if ("main".equals(relativePath) || "zone".equals(relativePath)
                            || relativePath.startsWith("main/") || relativePath.startsWith("zone/")) {
                        if (!normalizedDestinationPaths.add(relativePath)) {
                            throw new IOException("Duplicate normalized game-data path: " + relativePath);
                        }
                    }
                    collect(resolver, treeUri, documentId, relativePath, depth + 1,
                            visitedDocumentIds, topLevelDirectories,
                            normalizedDestinationPaths, files);
                    continue;
                }

                String lower = displayName.toLowerCase(Locale.ROOT);
                boolean iwd = lower.endsWith(".iwd");
                boolean fastFile = lower.endsWith(".ff");
                if ((iwd || fastFile) && (relativePath.startsWith("main/")
                        || relativePath.startsWith("zone/"))) {
                    if (files.size() >= MAX_SOURCE_FILES) {
                        throw new IOException("Selected game-data tree contains too many IWD/FastFile files");
                    }
                    if (!normalizedDestinationPaths.add(relativePath)) {
                        throw new IOException("Duplicate normalized game-data path: " + relativePath);
                    }
                    Uri documentUri = DocumentsContract.buildDocumentUriUsingTree(treeUri, documentId);
                    files.add(new SourceFile(documentUri, relativePath, iwd));
                }
            }
        } catch (SecurityException denied) {
            throw new IOException("Permission denied while reading selected game data", denied);
        }
    }

    private static boolean safeSegment(String name) {
        return name != null && !name.isEmpty() && !".".equals(name) && !"..".equals(name)
                && name.indexOf('/') < 0 && name.indexOf('\\') < 0 && name.indexOf(0) < 0;
    }
}
