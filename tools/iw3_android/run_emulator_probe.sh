#!/usr/bin/env bash
# Actual ADB input -> Activity -> JNI -> native state. Never inject fake events.
set -euo pipefail

proof_dir="$RUNNER_TEMP/iw3-android-runtime-proof"
mkdir -p "$proof_dir"
capture_final() {
    adb logcat -d -s IW3NativeGate:I AndroidRuntime:E DEBUG:E '*:S' \
        > "$RUNNER_TEMP/iw3-emulator-native-logcat.txt" || true
    adb shell dumpsys window > "$proof_dir/window-final.txt" || true
    adb exec-out screencap -p > "$proof_dir/screen-final.png" || true
}
trap capture_final EXIT

adb wait-for-device
adb shell dumpsys window > "$proof_dir/window-before-wake.txt"
adb shell input keyevent KEYCODE_WAKEUP
adb shell wm dismiss-keyguard
adb shell settings put system screen_off_timeout 1800000
adb install -r android/iw3-native/android_app/app/build/outputs/apk/debug/app-debug.apk
adb shell am force-stop org.z2026.iw3nativeprobe
adb logcat -c
adb shell am start -W -n org.z2026.iw3nativeprobe/.MainActivity
sleep 7
adb shell dumpsys window > "$proof_dir/window-before-touch.txt"
adb exec-out screencap -p > "$proof_dir/screen-before-touch.png"
adb logcat -d -s IW3NativeGate:I AndroidRuntime:E DEBUG:E '*:S' \
    > "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'IW3_JNI_UNZIP_PARSER_PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'IW3_JNI_IWD_SEARCHPATH_PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'IW3_JNI_IWD_GAME_DIRECTORY_PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'JNI_NATIVE_ENGINE_PROBE_PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'IW3_JNI_ACTIVITY_STARTED PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"

# Select an actual visible app view, instead of assuming a fixed coordinate
# falls inside it after landscape rotation, density or emulator changes.
adb shell uiautomator dump /sdcard/iw3-touch-window.xml
adb pull /sdcard/iw3-touch-window.xml "$proof_dir/touch-window.xml"
read -r touch_x touch_y < <(python3 - "$proof_dir/touch-window.xml" <<'PY'
import re
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
for node in root.iter('node'):
    if (node.get('package') == 'org.z2026.iw3nativeprobe'
            and node.get('class') == 'android.widget.TextView'):
        match = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.get('bounds', ''))
        if match:
            x0, y0, x1, y1 = map(int, match.groups())
            if x1 > x0 and y1 > y0:
                print((x0 + x1) // 2, (y0 + y1) // 2)
                break
else:
    raise SystemExit('Native diagnostic view is not visible in the actual Android hierarchy')
PY
)
printf 'ADB_REAL_TOUCH_TARGET x=%s y=%s\n' "$touch_x" "$touch_y"
adb shell input touchscreen tap "$touch_x" "$touch_y"
sleep 1
# Determine the rotated framebuffer from the real screenshot, not device assumptions.
read -r screen_w screen_h < <(python3 - "$proof_dir/screen-before-touch.png" <<'PY'
import struct
import sys
with open(sys.argv[1], "rb") as f:
    header = f.read(24)
if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("Cannot determine actual Android screenshot dimensions")
width, height = struct.unpack(">II", header[16:24])
print(width, height)
PY
)
attack_x=$((screen_w * 90 / 100))
attack_y=$((screen_h * 85 / 100))
printf 'ADB_REAL_ATTACK_TOUCH x=%s y=%s framebuffer=%sx%s\n' "$attack_x" "$attack_y" "$screen_w" "$screen_h"
adb shell input touchscreen tap "$attack_x" "$attack_y"
sleep 1
adb logcat -d -s IW3NativeGate:I AndroidRuntime:E DEBUG:E '*:S' \
    > "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'IW3_JNI_USERCMD attack=1' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
adb exec-out screencap -p > "$proof_dir/screen-after-touch.png"
adb shell input keyevent KEYCODE_HOME
sleep 2
adb shell am start -W -n org.z2026.iw3nativeprobe/.MainActivity
sleep 2
capture_final
cat "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
python3 tools/iw3_android/verify_runtime_evidence.py \
    "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
echo 'IW3_ORIGINAL_CPP_EXECUTED_INSIDE_ANDROID_EMULATOR_GREEN'
# Component execution only. No ARM64 physical-device or gameplay claim.
