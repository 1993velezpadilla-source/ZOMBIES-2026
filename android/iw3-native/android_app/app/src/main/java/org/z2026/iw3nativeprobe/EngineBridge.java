package org.z2026.iw3nativeprobe;

/**
 * JNI contract for actual KisakCOD source routines, via libiw3_sp_math.
 * This is not a second game engine. Native library is compiled from the
 * repo's original KisakCOD C++ translation units and Android platform glue.
 */
public final class EngineBridge {
    static {
        System.loadLibrary("iw3_sp_math");
    }

    private EngineBridge() {}

    // Open an app-owned directory as the native IW3 file-data root.
    // This is a platform boundary only; actual IW3 fastfile parsing is pending.
    public static native int nativeSetDataRoot(String absolutePath);
    public static native String nativeReport(String writableDirectory);
    // Validate user-imported main/*.iwd and zone/*.iwd with original FS_LoadZipFile,
    // then temporarily mount each archive and read one member through the original
    // FS_FOpenFileReadForThread/FS_Read/FS_FCloseFile path. This does not initialize
    // the persistent game searchpath, run FS_Startup, load FastFiles/maps, or start gameplay.
    public static native String nativeValidateImportedIwds(String appPrivateRoot);
    public static native int nativeTouch(int pointerId, float x, float y, boolean pressed);
    // Original usercmd_s fields: time, buttons, packed angles, movement bytes.
    // The game frame/CL_CreateCmd does not consume this adapter yet.
    public static native int nativeUsercmdSnapshot(int serverTime, int[] fields);
    public static native int nativeTouchSnapshot(int pointerId, float[] coordinates);
    public static native void nativeTouchReset();
    public static native void nativeLifecycle(int event);
    public static native int nativeLifecycleState();
}
