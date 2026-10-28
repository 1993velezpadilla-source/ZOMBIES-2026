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
grep -F 'IW3_JNI_IWD_FS_READ_PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'JNI_NATIVE_ENGINE_PROBE_PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'IW3_JNI_ACTIVITY_STARTED PASS' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"

# Select an actual visible app view, instead of assuming a fixed coordinate
# falls inside it after landscape rotation, density or emulator changes.
# The hosted emulator occasionally shows a Quickstep launcher ANR dialog over
# the still-running app. Recover only that named system dialog by tapping its
# actual Wait-button bounds; never dismiss an app ANR or invent touch coordinates.
touch_x=""
touch_y=""
max_ui_attempts=5
for attempt in $(seq 1 "$max_ui_attempts"); do
    rm -f "$proof_dir/touch-window.xml"
    adb shell rm -f /sdcard/iw3-touch-window.xml
    adb shell uiautomator dump /sdcard/iw3-touch-window.xml >/dev/null 2>&1 || true
    adb pull /sdcard/iw3-touch-window.xml "$proof_dir/touch-window.xml" >/dev/null 2>&1 || true
    if [[ ! -s "$proof_dir/touch-window.xml" ]]; then
        sleep 1
        continue
    fi
    read -r ui_state ui_x ui_y < <(python3 - "$proof_dir/touch-window.xml" "$proof_dir/screen-before-touch.png" <<'PY'
import re
import struct
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
nodes = list(root.iter('node'))
with open(sys.argv[2], "rb") as f:
    header = f.read(24)
if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("Cannot scale UIAutomator bounds without the real screenshot")
screen_w, screen_h = struct.unpack(">II", header[16:24])
bounds_re = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")

def parsed_bounds(node):
    match = bounds_re.fullmatch(node.get("bounds", ""))
    if not match:
        return None
    x0, y0, x1, y1 = map(int, match.groups())
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None

all_bounds = [parsed_bounds(node) for node in nodes]
all_bounds = [bounds for bounds in all_bounds if bounds]
if not all_bounds:
    print("retry 0 0")
    raise SystemExit(0)
# UIAutomator reports logical/display coordinates on some emulator images,
# while adb input consumes physical framebuffer pixels. Scale from the real
# screenshot instead of tapping the unscaled bounds.
ui_max_x = max(bounds[2] for bounds in all_bounds)
ui_max_y = max(bounds[3] for bounds in all_bounds)
scale_x = screen_w / ui_max_x
scale_y = screen_h / ui_max_y

def center(node):
    bounds = parsed_bounds(node)
    if not bounds:
        return None
    x0, y0, x1, y1 = bounds
    return (int(round(((x0 + x1) / 2) * scale_x)),
            int(round(((y0 + y1) / 2) * scale_y)))

# Handle a launcher ANR before selecting an app view that may still be present
# underneath the modal dialog in the accessibility tree.
if any(node.get("text") == "Quickstep isn't responding" for node in nodes):
    for node in nodes:
        if node.get("resource-id") == "android:id/aerr_wait":
            point = center(node)
            if point:
                print("quickstep_anr", *point)
                raise SystemExit(0)

for node in nodes:
    if (node.get("package") == "org.z2026.iw3nativeprobe"
            and (node.get("class") == "android.widget.TextView"
                 or node.get("content-desc") == "IW3 native diagnostic touch surface")):
        point = center(node)
        if point:
            print("target", *point)
            raise SystemExit(0)

print("retry 0 0")
PY)
    case "$ui_state" in
        target)
            touch_x="$ui_x"
            touch_y="$ui_y"
            break
            ;;
        quickstep_anr)
            printf 'ANDROID_SYSTEM_UI_RECOVERY attempt=%s action=wait x=%s y=%s\n' "$attempt" "$ui_x" "$ui_y"
            adb shell input tap "$ui_x" "$ui_y"
            sleep 3
            ;;
        *)
            sleep 1
            ;;
    esac
done
if [[ -z "$touch_x" || -z "$touch_y" ]]; then
    echo "Native diagnostic view did not become visible after bounded UI recovery" >&2
    exit 1
fi
ensure_app_ready() {
    local attempt ui_state ui_x ui_y
    for attempt in $(seq 1 5); do
        adb shell uiautomator dump /sdcard/iw3-touch-window.xml >/dev/null 2>&1 || true
        adb pull /sdcard/iw3-touch-window.xml "$proof_dir/touch-window.xml" >/dev/null 2>&1 || true
        if [[ ! -s "$proof_dir/touch-window.xml" ]]; then
            adb shell am start -W -n org.z2026.iw3nativeprobe/.MainActivity >/dev/null
            sleep 1
            continue
        fi
        read -r ui_state ui_x ui_y < <(python3 - "$proof_dir/touch-window.xml" "$proof_dir/screen-before-touch.png" <<'PY'
import re
import struct
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
nodes = list(root.iter("node"))
with open(sys.argv[2], "rb") as f:
    header = f.read(24)
if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("Cannot scale UI bounds from screenshot")
screen_w, screen_h = struct.unpack(">II", header[16:24])
bounds_re = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
def bounds(node):
    m = bounds_re.fullmatch(node.get("bounds", ""))
    if not m: return None
    x0, y0, x1, y1 = map(int, m.groups())
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None
all_bounds = [bounds(node) for node in nodes]
all_bounds = [b for b in all_bounds if b]
if not all_bounds:
    print("missing 0 0")
    raise SystemExit(0)
max_x = max(b[2] for b in all_bounds)
max_y = max(b[3] for b in all_bounds)
sx, sy = screen_w / max_x, screen_h / max_y
def center(node):
    b = bounds(node)
    if not b: return None
    x0, y0, x1, y1 = b
    return int(round((x0+x1)*0.5*sx)), int(round((y0+y1)*0.5*sy))
if any(node.get("text") == "Quickstep isn't responding" for node in nodes):
    for node in nodes:
        if node.get("resource-id") == "android:id/aerr_wait":
            point = center(node)
            if point:
                print("quickstep_anr", *point)
                raise SystemExit(0)
if any(node.get("package") == "org.z2026.iw3nativeprobe" and
       node.get("content-desc") == "IW3 native diagnostic touch surface" for node in nodes):
    print("app 0 0")
    raise SystemExit(0)
print("missing 0 0")
PY)
        case "$ui_state" in
            app) return 0 ;;
            quickstep_anr)
                printf 'ANDROID_SYSTEM_UI_RECOVERY_BEFORE_GESTURE attempt=%s action=wait x=%s y=%s\n' "$attempt" "$ui_x" "$ui_y"
                adb shell input tap "$ui_x" "$ui_y"
                sleep 2
                ;;
            *)
                adb shell am start -W -n org.z2026.iw3nativeprobe/.MainActivity >/dev/null
                sleep 1
                ;;
        esac
    done
    echo "Android diagnostic view lost foreground after bounded recovery" >&2
    return 1
}

ensure_app_ready
printf 'ADB_REAL_TOUCH_TARGET x=%s y=%s\n' "$touch_x" "$touch_y"
adb shell input touchscreen swipe "$touch_x" "$touch_y" "$touch_x" "$touch_y" 400
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
sprint_x=$((screen_w * 8 / 100))
sprint_y=$((screen_h * 88 / 100))
printf 'ADB_REAL_SPRINT_TOUCH x=%s y=%s framebuffer=%sx%s\n' "$sprint_x" "$sprint_y" "$screen_w" "$screen_h"
ensure_app_ready
adb shell input touchscreen swipe "$sprint_x" "$sprint_y" "$sprint_x" "$sprint_y" 600
sleep 0.5
slide_x=$((screen_w * 27 / 100))
slide_y=$((screen_h * 88 / 100))
printf 'ADB_REAL_SLIDE_TOUCH x=%s y=%s framebuffer=%sx%s\n' "$slide_x" "$slide_y" "$screen_w" "$screen_h"
ensure_app_ready
adb shell input touchscreen swipe "$slide_x" "$slide_y" "$slide_x" "$slide_y" 600
sleep 0.5
attack_x=$((screen_w * 90 / 100))
attack_y=$((screen_h * 85 / 100))
printf 'ADB_REAL_ATTACK_TOUCH x=%s y=%s framebuffer=%sx%s\n' "$attack_x" "$attack_y" "$screen_w" "$screen_h"
ensure_app_ready
adb shell input touchscreen swipe "$attack_x" "$attack_y" "$attack_x" "$attack_y" 600
sleep 1
adb logcat -d -s IW3NativeGate:I AndroidRuntime:E DEBUG:E '*:S' \
    > "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -F 'IW3_JNI_USERCMD attack=1' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
grep -E 'IW3_JNI_USERCMD attack=0 buttons=2 ' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
echo 'IW3_JNI_SPRINT_USERCMD_PASS'
grep -E 'IW3_JNI_USERCMD attack=0 buttons=514 ' "$RUNNER_TEMP/iw3-emulator-native-logcat.txt"
echo 'IW3_JNI_SLIDE_CHORD_USERCMD_PASS'
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
