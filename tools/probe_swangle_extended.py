#!/usr/bin/env python3
"""Extend Android screenshot/memory observations after the baseline import test.

This script never calls the game engine's internal APIs and does not alter data.
"""
import json
import subprocess
import time
from pathlib import Path
from PIL import Image,ImageStat

OUT=Path("smoke-out/real-data-test")
PACKAGE="com.cod4.firstmission:sp"

def adb(*args,timeout=45):
    try:
        p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
        return p.stdout.strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"

def frame_stats(img):
    w,h=img.size
    area=img.crop((int(w*.23),int(h*.18),int(w*.77),int(h*.78))).resize((200,100)).convert("RGB")
    px=list(area.getdata())
    n=len(px)
    red=sum(1 for r,g,b in px if r>=35 and r>g*2 and r>b*2)
    rgb=[round(v,1) for v in ImageStat.Stat(area).mean]
    return {"center_mean_rgb":rgb,"red_dominant_pct":round(red*100/n,2),"black_pct":round(100*sum(max(t)<18 for t in px)/n,2)}
def main():
    rows=[]
    for secs in (60,120,180):
        time.sleep(60)
        label=f"swangle-extended-{secs:03d}"
        path=OUT/(label+".png")
        with path.open("wb") as output:
            subprocess.run(["adb","exec-out","screencap","-p"],stdout=output,
                           stderr=subprocess.DEVNULL,timeout=50,check=True)
        with Image.open(path) as im:
            color=frame_stats(im)
        pid=adb("shell","pidof",PACKAGE)
        mem=adb("shell","dumpsys","meminfo",PACKAGE,timeout=60)
        (OUT/(label+"-meminfo.txt")).write_text(mem[:11000]+"\n")
        line=next((x.strip() for x in mem.splitlines() if x.strip().startswith("TOTAL PSS:")),"")
        rows.append({"after_baseline_seconds":secs,"pid":pid,"screenshot":path.name,
                     "scene_color_metrics":color,"total_pss_report_line":line})
        print("SWANGLE_EXTENDED_STATE",json.dumps(rows[-1]),flush=True)
        if not pid:
            print("Game campaign process no longer exists; ending extended observations",flush=True)
            break
    report={"backend":"swangle","android_emulator_api":35,
            "max_total_post_level_start_seconds":"~280 seconds",
            "frames":rows,"physical_gpu_validated":False,
            "gameplay_verified":False,
            "caution":"No automatic color statistic establishes that a playable 3D mission loaded; inspect screenshots and engine logs."}
    (OUT/"swangle-extended-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SWANGLE_EXTENDED_REPORT",json.dumps(report),flush=True)
if __name__=="__main__":
    main()
