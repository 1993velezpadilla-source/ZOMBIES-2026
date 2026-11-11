#pragma once

// The upstream build scripts generate this declaration header beside
// buildnumber.cpp. The Android common.cpp object-only audit needs the exact
// original signatures, but deliberately does not invent a build number or
// provide a replacement implementation. The real buildnumber.cpp remains
// the sole provider when it is integrated into the engine runtime.
char *getBuildNumber();
int getBuildNumberAsInt();
