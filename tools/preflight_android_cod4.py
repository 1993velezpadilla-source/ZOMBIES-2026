#!/usr/bin/env python3
"""COD4 Android + desktop-asset compatibility preflight (static, no APK execution).

Reads auditable inventories, compares required paths and packed-file signatures,
and distinguishes verified facts from runtime unknowns.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"docs/audit"
OUT=AUDIT/"ANDROID_PC_COMPATIBILITY.md"
JSON_OUT=AUDIT/"android-pc-compatibility.json"
EXPECTED_APK_SHA="40386503d564b0985423339b5ccd5611dc60ce08ebe1b4ae494d4de22a62473c"
SOURCE_ROOT="Call of Duty 4 Modern Warfare/"
TARGET_ARCH="arm64-v8a"

def load(p):
    return json.loads((AUDIT/p).read_text(encoding="utf8"))

def check(id,condition,detail,impact,kind="static"):
    return {"id":id,"status":"PASS" if condition else "FAIL","evidence":detail,"impact":impact,"verification":kind}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--apk",type=Path,help="Optional original COD4.apk for FF-header check")
    args=parser.parse_args()
    pc=load("c4-mocs-file-inventory.json")
    android=load("cod4-apk-file-inventory.json")
    refs=load("apk-runtime-strings.json")
    nested=load("nested-audit-data.json")
    outer={r["path"][len(SOURCE_ROOT):]:r for r in pc if r["path"].startswith(SOURCE_ROOT)}
    apk_names={r["path"]:r for r in android}
    main_iwd=sorted(x for x in outer if x.startswith("main/iw_") and x.endswith(".iwd"))
    zones=sorted({x.split("/")[1] for x in outer if x.startswith("zone/") and x.endswith(".ff")})
    languages=sorted({x.split("_")[1] for x in outer if x.startswith("main/localized_") and "_iw" in x})
    required_campaign=("main/iw_00.iwd","zone/spanish/code_post_gfx.ff",
                       "zone/spanish/common.ff","zone/spanish/ui.ff")
    required_mp=("main/iw_00.iwd","zone/spanish/code_post_gfx_mp.ff",
                 "zone/spanish/common_mp.ff","zone/spanish/ui_mp.ff")
    app_strings=sum((v.get("samples",{}).get("game_data",[]) for v in refs.values()),[])
    dex_strings=refs.get("classes.dex",{}).get("samples",{}).get("game_data",[])
    native_strings=sum((v.get("samples",{}).get("game_data",[]) for k,v in refs.items() if "/libcod4" in k or "libcod4" in k),[])
    total_refs="\n".join(dex_strings+native_strings).lower()
    native_libs=sorted(x for x in apk_names if x.startswith("lib/"+TARGET_ARCH+"/"))
    ffs=[x for x in outer if x.startswith("zone/") and x.endswith(".ff")]
    subpacks=nested["c4"]["containers"]
    checks=[
        check("original-zip-structure",bool(outer) and len(outer)>=210,
              f"PC package recognized, {len(outer)} files directly in outer ZIP",
              "Correct game-data root located"),
        check("main-directory",bool(main_iwd),
              f"{len(main_iwd)} numbered IW package(s) found",
              "Basic content archive present"),
        check("campaign-critical-paths",all(x in outer for x in required_campaign),
              ", ".join(f"{x}={x in outer}" for x in required_campaign),
              "English and Spanish localization are not interchangeable assumptions"),
        check("multiplayer-critical-paths",all(x in outer for x in required_mp),
              ", ".join(f"{x}={x in outer}" for x in required_mp),
              "Only static file presence checked"),
        check("spanish-zone-coverage","spanish" in zones,
              f"Fastfile localization folders: {zones}; main language variants: {languages}",
              "Android engine language selection has NOT been tested"),
        check("android-native-abi",bool(native_libs) and "lib/arm64-v8a/libcod4first.so" in apk_names and "lib/arm64-v8a/libcod4mp.so" in apk_names,
              f"Native Android libraries: {len(native_libs)} under {TARGET_ARCH}",
              "Physical device ABI/GPU compatibility remains untested"),
        check("apk-import-references","import the complete campaign" in total_refs and "main/iw_00.iwd" in total_refs,
              "Compiled Android app references 'Import the complete campaign files' and 'main/iw_00.iwd'",
              "Literal strings support an import workflow, but do not verify that it works"),
        check("asset-folders-preserved",all(x in outer for x in ("zone/spanish/common.ff","main/iw_00.iwd")),
              "Source root folder 'Call of Duty 4 Modern Warfare/' contains main/ and zone/spanish/",
              "Import must preserve relative main/ and zone/ folder hierarchy"),
        check("iwd-catalog",len(subpacks)>=22 and nested["c4"]["total_nested_files"]>=24104 and not nested["c4"]["errors"],
              f"{len(subpacks)} nested IWDs, {nested['c4']['total_nested_files']:,} entries, {len(nested['c4']['errors'])} errors",
              "Indexes read, but not full CRC on individual entries"),
    ]
    pc_fastfile_headers=nested["c4"]["fastfile_headers"]
    pc_magics={x["header_hex"][:16] for x in pc_fastfile_headers}
    apk_fastfile_headers={}
    if args.apk is not None:
        if not args.apk.is_file():
            raise SystemExit(f"APK missing: {args.apk}")
        digest=hashlib.file_digest(open(args.apk,"rb"),"sha256").hexdigest()
        if digest!=EXPECTED_APK_SHA:
            raise SystemExit("APK SHA-256 DOES NOT MATCH original release")
        with zipfile.ZipFile(args.apk) as z:
            for path in sorted(x for x in apk_names if x.startswith("assets/cod4x/") and x.endswith(".ff")):
                with z.open(path) as stream:
                    header=stream.read(16)
                apk_fastfile_headers[path]={"header_hex":header.hex(),"ascii":repr(header[:8]),"bytes":apk_names[path]["bytes"]}
        checks.append(check("apk-fastfile-headers-available",bool(apk_fastfile_headers),
            f"Inspected {len(apk_fastfile_headers)} APK bundled COD4X .ff headers",
            "A matching magic is not sufficient for game build/version compatibility"))
    else:
        checks.append({"id":"apk-fastfile-headers-available","status":"NOT_CHECKED",
                       "evidence":"APK bytes not provided","impact":"No file signature comparison","verification":"static"})
    issues=[
        {
            "status":"UNVERIFIED",
            "topic":"Android app imports and loads this Spanish game installation",
            "detail":"Requires installing APK on authorized ARM64 Android device and testing file import and campaign launch."
        },
        {
            "status":"UNVERIFIED",
            "topic":"Game rendering, crashes, frame rate, audio, touchscreen and GPU driver",
            "detail":"No device execution was performed; those properties cannot be confirmed by archive inspection."
        },
        {
            "status":"RISK",
            "topic":"Spanish localization while APK mentions zone/english",
            "detail":"Source has zone/spanish/ but no zone/english/. Runtime engine may support Spanish via setting; this was not tested."
        },
        {
            "status":"LEGAL",
            "topic":"Public redistribution",
            "detail":"Do not assume rights to publicly distribute proprietary Call of Duty files or third-party APKs."
        }
    ]
    result={
        "source":"ZOMBIES-2026 release assets and static audit",
        "test_type":"Static Android ↔ PC asset-path compatibility preflight",
        "apk_executed":False,
        "pc_files":len(outer),
        "iwd_banks":len(main_iwd),
        "pc_ff_count":len(ffs),
        "localization_folders":zones,
        "localized_iwd_languages":languages,
        "checks":checks,
        "runtime_blockers_or_unknowns":issues,
        "pc_ff_magic_examples":sorted(pc_magics)[:5],
        "apk_bundled_ff_headers":apk_fastfile_headers,
    }
    JSON_OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    lines=[
        "# COD4 Android vs PC C4 — compatibility preflight",
        "",
        "**Scope:** directory structure, required asset names, APK architecture and compiled import strings. **NOT** an Android runtime or gameplay test.",
        "",
        "## Static checks",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for c in checks:
        lines.append(f"| {c['id']} | **{c['status']}** | {c['evidence'].replace('|','/')} |")
    lines += [
        "",
        f"PC installation: **{len(outer)}** files, **{len(main_iwd)}** main IWD banks, **{len(ffs)}** zone fastfiles.",
        f"Language zone directories: {', '.join(zones) or 'none'}; localized main IWDs: {', '.join(languages) or 'none'}.",
        "",
        "## What's NOT proved",
    ]
    for i in issues:
        lines.append(f"- **{i['status']} — {i['topic']}:** {i['detail']}")
    lines += [
        "",
        "## Next real-world test requirements",
        "",
        "On an ARM64 Android test device that you control, install the APK only after evaluating its provenance and security. "
        "Use a legally obtained compatible copy of the PC game and the app's supported in-app import flow. "
        "Preserve the **main/** and **zone/** subdirectories, and verify that Spanish content is accepted. "
        "Capture the app's import result, any errors, and a launch/frame-rate log. "
        "Don't publish or copy licensed assets into new public repos for this test.",
        "",
        "**Machine-readable report:** [android-pc-compatibility.json](android-pc-compatibility.json).",
    ]
    OUT.write_text("\n".join(lines)+"\n",encoding="utf8")
    print("SUMMARY:",json.dumps({
        "pass":sum(x["status"]=="PASS" for x in checks),
        "fail":sum(x["status"]=="FAIL" for x in checks),
        "not_checked":sum(x["status"]=="NOT_CHECKED" for x in checks),
        "zone_languages":zones,
        "runtime_tested":False,
        "apk_ff_magic":apk_fastfile_headers,
    },ensure_ascii=False),flush=True)
    if any(c["status"]=="FAIL" for c in checks):
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
