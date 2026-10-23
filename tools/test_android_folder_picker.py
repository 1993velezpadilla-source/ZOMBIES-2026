#!/usr/bin/env python3
"""Test COD4 Android Storage Access Framework picker using synthetic data only.

Does not include or modify any commercial game content.
This tests the app's UI response to selecting a folder, not campaign gameplay.
"""
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

OUT=Path("smoke-out/import-picker")
OUT.mkdir(parents=True,exist_ok=True)
FIXTURE=Path("smoke-out/COD4-FIXTURE")

def adb(*args, timeout=40):
    r=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
    if r.returncode:
        print("ADB warning",args,r.returncode,r.stdout[:200],flush=True)
    return r.stdout

def shot(label):
    path=OUT/(label+".png")
    with path.open("wb") as f:
        subprocess.run(["adb","exec-out","screencap","-p"],stdout=f,timeout=30,check=True)
    return str(path)

def ui():
    adb("shell","uiautomator","dump","/sdcard/window.xml",timeout=60)
    source=adb("shell","cat","/sdcard/window.xml",timeout=30)
    ix=source.find("<?xml")
    if ix<0:
        return []
    try:
        xml=ET.fromstring(source[ix:])
    except ET.ParseError:
        return []
    return [n.attrib for n in xml.iter() if "bounds" in n.attrib]

def center(bounds):
    n=list(map(int,re.findall(r"\d+",bounds)))
    return (n[0]+n[2])//2,(n[1]+n[3])//2

def tap_label(words, prefer_exact=True):
    nodes=ui()
    for word in words:
        matches=[]
        for n in nodes:
            text=(n.get("text") or "").strip()
            description=(n.get("content-desc") or "").strip()
            values=[text.lower(),description.lower()]
            needle=word.lower().strip()
            if (needle in values if prefer_exact else any(needle in v for v in values)):
                matches.append(n)
        for n in matches:
            bounds=n.get("bounds")
            if bounds:
                x,y=center(bounds)
                print("TAP LABEL",word,repr(n.get("text")),repr(n.get("content-desc")),x,y,flush=True)
                adb("shell","input","tap",str(x),str(y))
                time.sleep(3)
                return True
    return False

def node_summary():
    return [{"text":n.get("text"),"desc":n.get("content-desc"),"bounds":n.get("bounds")}
            for n in ui() if n.get("text") or n.get("content-desc")][:65]

def prepare_fixture():
    files={
      "localization.txt":"SYNTHETIC FIXTURE — NOT A GAME FILE\n",
      "main/README.txt":"Synthetic UI import probe only\n",
      "zone/spanish/README.txt":"No game assets included\n"
    }
    for name,text in files.items():
        target=FIXTURE/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding="utf-8")
    adb("push",str(FIXTURE),"/sdcard/Download/",timeout=90)

def main():
    prepare_fixture()
    adb("shell","am","force-stop","com.cod4.firstmission")
    result=adb("shell","am","start","-W","-n","com.cod4.firstmission/.MainActivity",timeout=40)
    time.sleep(6)
    shot("00-launcher")
    if tap_label(["Got it","Entendido","Aceptar"],True):
        print("Dismissed system full-screen hint",flush=True)
        shot("00-hint-dismissed")
        time.sleep(3)
    size=adb("shell","wm","size")
    m=re.findall(r"(\d+)x(\d+)",size)
    if not m:
        raise RuntimeError("Missing wm size "+size)
    w,h=map(int,m[-1])
    # Chinese native Android launcher import button is the first wide row,
    # independently observed at about 61% screen height.
    if not tap_label(["导入游戏资源文件夹","导入游戏资料文件夹"],False):
        adb("shell","input","tap",str(int(w*0.50)),str(int(h*0.615)))
    time.sleep(6)
    shot("01-after-import-tap")
    steps=[{"name":"import_button","nodes":node_summary()}]
    # SAF folder picker may initially be on Recents, home or Download.
    entered_fixture=False
    permission_granted=False
    for step in range(12):
        nodes=node_summary()
        values="\n".join((x["text"] or "")+" "+(x["desc"] or "") for x in nodes)
        steps.append({"name":"picker_step_"+str(step),"nodes":nodes})
        if tap_label(["Allow","ALLOW","允许","允許"],True):
            shot("08-permission")
            permission_granted=True
            break
        if entered_fixture and tap_label(["Use this folder","USE THIS FOLDER","使用此文件夹","使用這個資料夾"],True):
            shot("07-folder-confirm")
            continue
        if not entered_fixture and tap_label(["COD4-FIXTURE"],True):
            entered_fixture=True
            shot("05-fixture-folder")
            continue
        if tap_label(["Download","Downloads","下载","下載"],True):
            shot("04-download-folder")
            continue
        if tap_label(["Show roots","Show navigation drawer","Navigate up"],False):
            shot("03-navigation")
            continue
        # Manual inspection output on unfamiliar system dialogs, no blind taps.
        print("No recognized picker controls; capturing UI",flush=True)
        break
    time.sleep(4)
    shot("09-final")
    adb("shell","dumpsys","activity","activities")
    log=adb("logcat","-d","-t","1800",timeout=45)
    safe_logs=[line for line in log.splitlines() if any(t in line.lower() for t in
       ["cod4","documentsui","saf","securityexception","fatal exception","androidruntime","permission denied"])]
    (OUT/"filtered-logcat.txt").write_text("\n".join(safe_logs[-240:])+"\n")
    report={
      "test":"Synthetic app import folder picker",
      "fixture_is_synthetic":True,
      "game_assets_imported":False,
      "campaign_tested":False,
      "fixture_selected_in_picker":entered_fixture,
      "saf_permission_granted":permission_granted,
      "apk_launcher_result":result[-500:],
      "screenshots":[str(x) for x in OUT.glob("*.png")],
      "last_ui_nodes":node_summary(),
      "steps":[{"name":s["name"],"labels":[n["text"] for n in s["nodes"] if n["text"]][:35]} for s in steps],
    }
    (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PICKER_RESULT",json.dumps(report,ensure_ascii=False)[:6000],flush=True)

if __name__=="__main__":
    main()
