package org.z2026.iw3nativeprobe;

import android.content.ContentResolver;
import android.content.Context;
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
        collect(resolver, treeUri, rootDocumentId, "", 0, visitedDocumentIds,
                topLevelDirectories, sourceFiles);

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
            String targetPath = target.getCanonicalPath();
            if (!targetPath.startsWith(rootPath + File.separator)) {
                throw new IOException("Refusing path outside app-private root");
            }
            File parent = target.getParentFile();
            if (parent == null || (!parent.isDirectory() && !parent.mkdirs())) {
                throw new IOException("Cannot create game-data subdirectory");
            }

            File partial = new File(parent, target.getName() + ".iw3-import-part");
            if (partial.exists() && !partial.delete()) {
                throw new IOException("Cannot clear stale partial import");
            }
            long fileBytes = 0;
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
            } catch (IOException failure) {
                partial.delete();
                throw failure;
            }

            if (target.exists() && !target.delete()) {
                partial.delete();
                throw new IOException("Cannot replace previously imported game-data file");
            }
            if (!partial.renameTo(target)) {
                partial.delete();
                throw new IOException("Cannot finalize imported game-data file");
            }
            bytesCopied += fileBytes;
            if (source.iwd) copiedIwd++;
            else copiedFast++;
        }

        return new Summary(copiedIwd, copiedFast, bytesCopied);
    }

    private static void collect(ContentResolver resolver, Uri treeUri, String parentId,
            String parentPath, int depth, Set<String> visitedDocumentIds,
            Set<String> topLevelDirectories, List<SourceFile> files) throws IOException {
        if (!visitedDocumentIds.add(parentId)) return;

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
                    topLevelDirectories.add(displayName);
                    // COD4 assets needed by the original SP filesystem live in
                    // main/ and zone/. Avoid walking unrelated user directories.
                    if (!"main".equals(displayName) && !"zone".equals(displayName)) continue;
                }

                String relativePath = parentPath.isEmpty()
                        ? displayName : parentPath + "/" + displayName;
                if (directory) {
                    collect(resolver, treeUri, documentId, relativePath, depth + 1,
                            visitedDocumentIds, topLevelDirectories, files);
                    continue;
                }

                String lower = displayName.toLowerCase(Locale.ROOT);
                boolean iwd = lower.endsWith(".iwd");
                boolean fastFile = lower.endsWith(".ff");
                if ((iwd || fastFile) && (relativePath.startsWith("main/")
                        || relativePath.startsWith("zone/"))) {
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
                && name.indexOf('/') < 0 && name.indexOf('\\\\') < 0
                && name.indexOf('\u0000') < 0;
    }
}
