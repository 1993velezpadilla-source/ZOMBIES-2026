#pragma once
// Real Android Surface + Display -> original IW3 renderer display-mode dvars.
// NOT a graphics backend and NOT proof of an Android renderer frame.
#if defined(__ANDROID__)
#include <jni.h>
// JNI references are borrowed; caller retains ownership of Surface/Display.
// Must be invoked on a thread with a valid JNIEnv and live Android objects.
bool R_AndroidPopulateDisplayMode(JNIEnv *env, jobject surface, jobject display);
#endif
