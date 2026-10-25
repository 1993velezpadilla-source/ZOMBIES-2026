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
    public static native String nativeReport();
    public static native int nativeTouch(int pointerId, float x, float y, boolean pressed);
    public static native int nativeTouchSnapshot(int pointerId, float[] coordinates);
    public static native void nativeTouchReset();
    public static native void nativeLifecycle(int event);
    public static native int nativeLifecycleState();
}
