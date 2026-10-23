#!/usr/bin/env bash
# Dynamic APK smoke test in a disposable Android emulator.
# No source-game asset import, no device credentials, no calls to private devices.
set -u
mkdir -p smoke-out
LOG=smoke-out/android-logcat-filtered.txt
: > "$LOG"
echo "Android emulator version: $(adb shell getprop ro.build.version.release | tr -d '\r')"
echo "Android SDK: $(adb shell getprop ro.build.version.sdk | tr -d '\r')"
echo "Emulator ABIs: $(adb shell getprop ro.product.cpu.abilist | tr -d '\r')"
echo "Emulator native bridge: $(adb shell getprop ro.dalvik.vm.native.bridge | tr -d '\r')"
echo "Disable network on disposable emulator to reduce unknown APK traffic."
adb shell svc wifi disable || true
adb shell svc data disable || true
echo "Installing original unmodified APK..."
set +e
adb install -r "_release_assets/cod4/COD4.apk" > smoke-out/install-result.txt 2>&1
install_rc=$?
cat smoke-out/install-result.txt
if [[ "$install_rc" -eq 0 ]]; then
  echo "Starting COD4's declared MainActivity..."
  adb shell am start -W -n com.cod4.firstmission/.MainActivity > smoke-out/launch-result.txt 2>&1
  start_rc=$?
  cat smoke-out/launch-result.txt
  sleep 7
  adb exec-out screencap -p > smoke-out/first-screen.png
  # Fresh Android emulators show a system full-screen onboarding dialog.
  # Dismiss by tapping its "Got it" button relative to current display size.
  python3 - <<'PY'
import struct,subprocess
b=open("smoke-out/first-screen.png","rb").read(24)
if b[:8]==bytes([137,80,78,71,13,10,26,10]) and len(b)>=24:
    width,height=struct.unpack(">II",b[16:24])
    x,y=int(width*0.725),int(height*0.48)
    print("Dismissing Android full-screen hint",width,height,x,y,flush=True)
    subprocess.run(["adb","shell","input","tap",str(x),str(y)],check=False)
PY
  sleep 10
  adb shell dumpsys activity activities > smoke-out/activity-dumpsys.txt 2>&1
  adb exec-out screencap -p > smoke-out/screenshot.png
else
  start_rc=90
  echo "Skipping launch because APK installation failed." > smoke-out/launch-result.txt
fi
adb logcat -d -t 2000 > smoke-out/full-logcat.txt 2>&1 || true
grep -Ei "FATAL EXCEPTION|AndroidRuntime|ActivityTaskManager|cod4|ClassNotFound|UnsatisfiedLinkError|Unable to start|linker|Fatal signal|crash_dump" smoke-out/full-logcat.txt | tail -n 240 > "$LOG" || true
python3 - "$install_rc" "$start_rc" <<'PY'
import json, pathlib, sys
root=pathlib.Path("smoke-out")
install=int(sys.argv[1])
start=int(sys.argv[2])
raw=(root/"launch-result.txt").read_text(errors="replace")
log=(root/"android-logcat-filtered.txt").read_text(errors="replace")
activities=(root/"activity-dumpsys.txt").read_text(errors="replace") if (root/"activity-dumpsys.txt").exists() else ""
has_runtime_fatal=any(x in log for x in ("FATAL EXCEPTION","UnsatisfiedLinkError","Fatal signal","Unable to start activity"))
report={
    "test":"disposable Android API 35 Google APIs x86_64 emulator",
    "apk":"COD4.apk", "apk_installed":install==0,"launch_command_succeeded":start==0,
    "main_activity_visible_in_dumpsys":"com.cod4.firstmission" in activities,
    "filtered_runtime_fatal_detected":has_runtime_fatal,
    "screenshot_captured":(root/"screenshot.png").exists(),
    "game_assets_imported":False,"campaign_loaded":False,
    "note":"This ARM64 APK may run under x86_64 ARM translation; behavior may differ from a physical ARM64 phone. No full PC data imported."
}
(root/"smoke-report.json").write_text(json.dumps(report,indent=2)+"\n")
print("SMOKE_REPORT",json.dumps(report))
PY
echo "Relevant log lines (last 50):"
tail -n 50 "$LOG"
# Do not block storing diagnostics on failure; workflow remains red if install fails.
if [[ "$install_rc" -ne 0 ]]; then
  exit 1
fi
if [[ "$start_rc" -ne 0 ]]; then
  exit 2
fi
exit 0
