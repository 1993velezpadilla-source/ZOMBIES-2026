#!/usr/bin/env python3
"""Isolated Android UI compatibility probe with a small original source-data subset.

The test emulates the UI import flow. It never claims to install a playable
game: only selected original archive entries are present. Do not persist or
upload original game bytes in CI artifacts.
"""
import json
from pathlib import Path
import subprocess
import time
from test_android_folder_picker import OUT as UNUSED, adb, shot, node_summary, tap_label

SOURCE=Path("_runtime_temp/original-pc-sample")
OUT=Path("smoke-out/real-data-test")
OUT.mkdir(parents=True,exist_ok=True)
FOLDER="COD4-SOURCE-CHECK"
APK="com.cod4.firstmission"

def checked(*args, timeout=180):
    print("+ adb", " ".join(args[:6]),flush=True)
    p=subprocess.run(["adb",*args],capture_output=True,text=True,timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"ADB {args[:4]} failed: {p.stdout[:300]} {p.stderr[:300]}")
    return p.stdout

def capture(name):
    path=OUT/(name+".png")
    with path.open("wb") as fh:
        subprocess.run(["adb","exec-out","screencap","-p"],stdout=fh,timeout=50,check=True)
    return str(path)

def labels():
    return [x.get("text","") for x in node_summary() if x.get("text","")]

def stage_android():
    files=sorted(x for x in SOURCE.rglob("*") if x.is_file())
    if len(files)<5:
        raise RuntimeError("Expected at least 5 core source asset files, found "+str(len(files)))
    checked("shell","mkdir","-p",f"/sdcard/Download/{FOLDER}/main",f"/sdcard/Download/{FOLDER}/zone/spanish")
    for item in files:
        relative=item.relative_to(SOURCE).as_posix()
        checked("push",str(item),f"/sdcard/Download/{FOLDER}/{relative}",timeout=240)
        print("Android staged",relative,item.stat().st_size,flush=True)
    print("DISK_AFTER_STAGING",adb("shell","df","-h","/data"),flush=True)
    return [{"path":x.relative_to(SOURCE).as_posix(),"bytes":x.stat().st_size} for x in files]

def main():
    records=stage_android()
    checked("shell","am","force-stop",APK)
    out=checked("shell","am","start","-W","-n",APK+"/.MainActivity")
    print("APP_LAUNCH",out,flush=True)
    time.sleep(5)
    capture("00-start")
    tap_label(["Got it","Entendido"],True)
    time.sleep(2)
    if not tap_label(["导入游戏资源文件夹"],False):
        raise RuntimeError("App import button not visible in accessibility view")
    time.sleep(3)
    capture("01-android-picker")
    if not tap_label(["Download"],True):
        raise RuntimeError("Android Download folder not found")
    time.sleep(2)
    if not tap_label([FOLDER],True):
        raise RuntimeError("Staged original source test folder not found")
    time.sleep(2)
    capture("02-selected-original-source-directory")
    if not tap_label(["Use this folder"],True):
        raise RuntimeError("Use this folder button absent")
    time.sleep(2)
    capture("03-system-grant")
    if not tap_label(["Allow"],True):
        raise RuntimeError("SAF permission grant missing")
    last=[]
    imported=False
    for attempt in range(48):
        time.sleep(5)
        current=labels()
        last=current
        match=any("导入完成" in x for x in current)
        if match:
            imported=True
            break
        if attempt in (1,5,11,20,35):
            print("IMPORT_POLL",attempt,current[:20],flush=True)
    capture("04-post-import")
    print("IMPORT_UI_LABELS",last,flush=True)
    has_error=any(any(term in x for term in ["失败","错误","无法"]) for x in last)
    did_main=any("尚未导入完整 main" in x for x in last)
    campaign_clicked=tap_label(["原版战役菜单"],False)
    if campaign_clicked:
        time.sleep(8)
    after_campaign=labels()
    capture("05-campaign-probe")
    log=adb("logcat","-d","-t","2200",timeout=50)
    relevant=[x for x in log.splitlines() if any(t in x.lower() for t in
        ["cod4","fatal exception","androidruntime","avc: denied","permission denied","outofmemory","SIGSEGV".lower()])]
    (OUT/"runtime-filtered-logcat.txt").write_text("\n".join(relevant[-350:])+"\n")
    report={
        "test":"Original source-data subset import into isolated Android emulator",
        "environment":"Android 15 emulator x86_64 with ARM64 translation, offline",
        "original_assets_staged":records,
        "source_game_data_complete":False,
        "import_banner_observed":imported,
        "incomplete_main_warning":did_main,
        "error_banner_observed":has_error,
        "campaign_button_clicked":campaign_clicked,
        "campaign_ui_labels_after_click":after_campaign[:60],
        "gameplay_confirmed":False,
        "emulator_session_only":True,
        "source_files_uploaded_as_ci_artifacts":False,
        "screenshots":sorted(x.name for x in OUT.glob("*.png"))
    }
    (OUT/"result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("REAL_SOURCE_IMPORT_RESULT",json.dumps(report,ensure_ascii=False),flush=True)
    # Recording a negative test is still a successful audit execution, not a
    # successful game compatibility claim. Fail if we cannot reach the picker.
    if not imported:
        print("GATE: source content import not confirmed",flush=True)

if __name__=="__main__":
    main()
