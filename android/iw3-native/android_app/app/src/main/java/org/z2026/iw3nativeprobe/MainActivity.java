package org.z2026.iw3nativeprobe;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.graphics.Color;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;

/**
 * Strict on-device native C++ integration diagnostic.
 * No map, gameplay, fake renderer, substituted game engine or COD assets.
 */
public final class MainActivity extends Activity {
    private static final String TAG = "IW3NativeGate";
    private static final int MAX_ANDROID_POINTER_ID_COUNT = 32;
    private static final int REQUEST_IMPORT_GAME_DATA = 7013;
    private TextView label;

    private static float clamp01(float value) {
        return Math.max(0.0f, Math.min(1.0f, value));
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        label = new TextView(this);
        label.setTextColor(Color.WHITE);
        label.setTextSize(17);
        label.setPadding(32, 25, 32, 25);
        label.setBackgroundColor(Color.rgb(10, 18, 28));
        // Keep the real touch surface discoverable to UIAutomator. A touch
        // listener alone does not guarantee that a TextView is exposed as an
        // accessibility node on every Android emulator image.
        label.setContentDescription("IW3 native diagnostic touch surface");
        label.setFocusable(true);
        label.setClickable(true);
        label.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
        // The TextView occupies the whole screen and can consume touches.
        // Bind touch directly on that actual view, rather than relying on
        // Activity.onTouchEvent to receive unhandled events.
        label.setOnTouchListener((view, motion) -> onTouchEvent(motion));

        // Import only data the user already owns. This prepares the original
        // filesystem's app-private root; it does not start or emulate gameplay.
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        Button importButton = new Button(this);
        importButton.setText("Import personal COD4 data");
        importButton.setContentDescription("Import personal Call of Duty 4 game data");
        importButton.setOnClickListener(view -> chooseGameDataDirectory());
        layout.addView(importButton, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));
        layout.addView(label, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.0f));
        setContentView(layout);
        try {
            EngineBridge.nativeLifecycle(1);
            // Diagnostic sentinel, NOT a fake COD asset. The actual JNI
            // module opens this through its sandboxed POSIX data-root bridge.
            File probe = new File(getFilesDir(), "iw3-native-io-probe.bin");
            try (FileOutputStream output = new FileOutputStream(probe, false)) {
                output.write("IW3_NATIVE_IO_2026".getBytes(StandardCharsets.US_ASCII));
                output.getFD().sync();
            }
            if (EngineBridge.nativeSetDataRoot(getFilesDir().getAbsolutePath()) != 0) {
                throw new IllegalStateException("Native IW3 data root initialization failed");
            }
            String report = EngineBridge.nativeReport(getFilesDir().getAbsolutePath());
            label.setText(report + "\n\nTOUCH TEST: TAP THIS SCREEN");
            Log.i(TAG, "IW3_JNI_ACTIVITY_STARTED " +
                    (report.contains("JNI: PASS") ? "PASS" : "FAIL"));
        } catch (Throwable failure) {
            label.setText("IW3 NATIVE CODE DIAGNOSTIC FAILED\n" +
                    failure.getClass().getSimpleName() + ": " + failure.getMessage());
            Log.e(TAG, "IW3_JNI_ACTIVITY_FAILED", failure);
        }
    }

    private void chooseGameDataDirectory() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        try {
            startActivityForResult(intent, REQUEST_IMPORT_GAME_DATA);
        } catch (Throwable failure) {
            Log.e(TAG, "IW3_GAME_DATA_PICKER_FAILED", failure);
            label.append("\n\nCannot open Android document picker: "
                    + failure.getClass().getSimpleName());
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_IMPORT_GAME_DATA) return;
        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            label.append("\n\nGame-data import cancelled.");
            return;
        }

        Uri treeUri = data.getData();
        int granted = data.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION;
        try {
            if (granted != 0) getContentResolver().takePersistableUriPermission(treeUri, granted);
        } catch (SecurityException failure) {
            Log.w(TAG, "Could not persist document-tree permission; importing this selection now", failure);
        }

        label.append("\n\nScanning selected COD4 game root...");
        new Thread(() -> {
            try {
                GameDataImporter.Summary summary =
                        GameDataImporter.importTree(this, treeUri, getFilesDir());
                String evidence = "IW3_GAME_DATA_IMPORT_PASS iwd=" + summary.iwdFiles
                        + " fastfiles=" + summary.fastFiles + " bytes=" + summary.bytesCopied;
                Log.i(TAG, evidence);
                runOnUiThread(() -> label.append("\n\n" + evidence
                        + "\nFiles staged in app-private main/ and zone/. "
                        + "Original FS/FastFile/map loading is still pending."));
            } catch (Throwable failure) {
                Log.e(TAG, "IW3_GAME_DATA_IMPORT_FAIL", failure);
                runOnUiThread(() -> label.append("\n\nGame-data import failed: "
                        + failure.getClass().getSimpleName() + ": " + failure.getMessage()));
            }
        }, "iw3-game-data-import").start();
    }

    @Override protected void onResume() {
        super.onResume();
        try { EngineBridge.nativeLifecycle(2); }
        catch (Throwable failure) { Log.e(TAG, "JNI_RESUME_FAILED", failure); }
    }

    @Override protected void onPause() {
        try {
            EngineBridge.nativeTouchReset();
            EngineBridge.nativeLifecycle(3);
        } catch (Throwable failure) { Log.e(TAG, "JNI_PAUSE_FAILED", failure); }
        super.onPause();
    }

    @Override protected void onDestroy() {
        try { EngineBridge.nativeLifecycle(4); }
        catch (Throwable failure) { Log.e(TAG, "JNI_DESTROY_FAILED", failure); }
        super.onDestroy();
    }

    private void forwardTouch(MotionEvent event, int pointerIndex, boolean down) {
        final int id = event.getPointerId(pointerIndex);
        // Android pointer IDs are sparse identifiers (0..31), not indexes
        // into the ten simultaneously active touch slots.
        if (id < 0 || id >= MAX_ANDROID_POINTER_ID_COUNT) return;
        float x = clamp01(event.getX(pointerIndex) / Math.max(1f, label.getWidth()));
        float y = clamp01(event.getY(pointerIndex) / Math.max(1f, label.getHeight()));
        int rc = EngineBridge.nativeTouch(id, x, y, down);
        if (rc != 0) Log.e(TAG, "TOUCH_NATIVE_REJECTED id=" + id);
        float[] observed = new float[2];
        int state = EngineBridge.nativeTouchSnapshot(id, observed);
        Log.i(TAG, "IW3_JNI_TOUCH id=" + id + " pressed=" + state
                + " coords=" + observed[0] + "," + observed[1]);
        int[] command = new int[10];
        int commandStatus = EngineBridge.nativeUsercmdSnapshot(
                (int)(SystemClock.uptimeMillis() & 0x7fffffff), command);
        if (commandStatus != 0) {
            Log.e(TAG, "IW3_JNI_USERCMD_SNAPSHOT_FAILED");
        } else {
            int buttons = command[1];
            Log.i(TAG, "IW3_JNI_USERCMD attack=" + ((buttons & 1) != 0 ? 1 : 0)
                    + " buttons=" + buttons + " forward=" + command[5]
                    + " right=" + command[6] + " pitch=" + command[2]
                    + " yaw=" + command[3]);
        }
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        try {
            final int masked = event.getActionMasked();
            switch (masked) {
                case MotionEvent.ACTION_DOWN:
                case MotionEvent.ACTION_POINTER_DOWN:
                    forwardTouch(event, event.getActionIndex(), true);
                    return true;
                case MotionEvent.ACTION_MOVE:
                    for (int i = 0; i < event.getPointerCount(); i++) {
                        forwardTouch(event, i, true);
                    }
                    return true;
                case MotionEvent.ACTION_POINTER_UP:
                case MotionEvent.ACTION_UP:
                    forwardTouch(event, event.getActionIndex(), false);
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    EngineBridge.nativeTouchReset();
                    return true;
                default:
                    return super.onTouchEvent(event);
            }
        } catch (Throwable failure) {
            Log.e(TAG, "IW3_JNI_TOUCH_FAILED", failure);
            return false;
        }
    }
}
