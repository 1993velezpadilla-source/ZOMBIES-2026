#!/usr/bin/env python3
"""Second-pass read-only audit of nested .iwd/.zip contents and native APK libraries."""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zipfile
from audit_releases import SplitReader, PARTS, APK, OUT

TERMS = ["zombie","nacht","mp40","weapon","animation","perk","scripts/","sound/","images/","xmodel","materials/","maps/","menu","ui/","hud","player"]
TEXTS = {"cfg","gsc","csc","csv","txt","menu","json","xml","ini","shader","md","hlsl","glsl"}
LIMIT_SIZE = 2*1024*1024
def extension(name):
    p=Path(name)
    return p.suffix.lower() or "[none]"
def sample_text(z):
    list_sample=[]
    for i in z.infolist():
        if len(list_sample)>25: break
        ext=Path(i.filename).suffix.lstrip(".").lower()
        if ext in TEXTS and i.file_size<8000 and re.search(r"^(?:[\w./ -]{1,200})$",i.filename):
            list_sample.append({"path":i.filename,"bytes":i.file_size})
    return list_sample
def overview(z,container):
    infos=[i for i in z.infolist() if not i.is_dir()]
    ext=Counter(extension(i.filename) for i in infos)
    term_counts=Counter(t for i in infos for t in TERMS if t in i.filename.lower())
    top_dirs=Counter("/".join(i.filename.replace("\\","/").split("/")[:2]) for i in infos)
    rows=[{"container":container,"path":i.filename,"bytes":i.file_size,
           "compressed_bytes":i.compress_size,"method":i.compress_type,
           "crc32":f"{i.CRC:08x}"} for i in infos]
    return {
        "files":len(infos),"uncompressed_bytes":sum(i.file_size for i in infos),
        "extensions":dict(ext.most_common()),"term_counts":dict(term_counts),
        "top_dirs":top_dirs.most_common(25),
        "examples": sample_text(z),
        "largest": [{"path":i.filename,"bytes":i.file_size} for i in sorted(infos,key=lambda x:x.file_size,reverse=True)[:12]],
    },rows
def file_signature(z,name,count=32):
    with z.open(name) as f:
        b=f.read(count)
    return b[:16].hex(), len(b)
def nested_c4():
    reader=SplitReader(PARTS)
    reports=[]
    all_entries=[]
    errors=[]
    ffs=[]
    bins=[]
    try:
        with zipfile.ZipFile(reader) as outer:
            for info in outer.infolist():
                if info.is_dir(): continue
                lname=info.filename.lower()
                if lname.endswith((".ff",".exe",".dll",".asi")):
                    try:
                        sig,length=file_signature(outer,info.filename,24)
                        obj={"path":info.filename,"bytes":info.file_size,"header_hex":sig}
                        if lname.endswith(".ff"):
                            ffs.append(obj)
                        else:
                            bins.append(obj)
                    except Exception as e:
                        errors.append({"path":info.filename,"error":str(e)[:150]})
                if not lname.endswith(".iwd"): continue
                print(f"Nested IWD: {info.filename} ({info.file_size:,} bytes)",flush=True)
                try:
                    with tempfile.TemporaryFile() as temp:
                        with outer.open(info) as src:
                            shutil.copyfileobj(src,temp,length=8*1024*1024)
                        temp.seek(0)
                        with zipfile.ZipFile(temp,"r") as sub:
                            desc,rows=overview(sub,info.filename)
                            desc["name"]=info.filename
                            reports.append(desc)
                            all_entries.extend(rows)
                except Exception as e:
                    errors.append({"path":info.filename,"error":type(e).__name__+": "+str(e)[:200]})
        results={"containers":reports,"errors":errors,
                 "total_nested_files":len(all_entries),
                 "extensions":dict(Counter(Path(x["path"]).suffix.lower() or "[none]" for x in all_entries).most_common()),
                 "matches":{term: [x["container"]+" :: "+x["path"] for x in all_entries
                                      if term in x["path"].lower()][:50] for term in TERMS},
                 "fastfile_headers":ffs,
                 "windows_binary_headers":bins}
        (OUT/"c4-iwd-file-inventory.json").write_text(json.dumps(all_entries,ensure_ascii=False,indent=2)+"\n")
        return results
    finally:
        reader.close()

def inspect_apk():
    with zipfile.ZipFile(APK) as z:
        packages=[]
        meta={}
        libraries=[]
        for i in z.infolist():
            if i.is_dir(): continue
            name=i.filename
            if name.lower().endswith((".zip",".iwd")):
                try:
                    with z.open(i) as f:
                        from io import BytesIO
                        raw=f.read()
                    with zipfile.ZipFile(BytesIO(raw)) as nested:
                        desc,rows=overview(nested,name)
                        desc["name"]=name
                        packages.append(desc)
                except Exception as e:
                    packages.append({"name":name,"error":type(e).__name__+": "+str(e)[:200]})
            if name.startswith("assets/") and name.lower().endswith((".json",".md")) and i.file_size<16000:
                data=z.read(i.filename).decode("utf-8",errors="replace")
                # Only non-secret keys and size metadata are placed in public report.
                item={"path":name,"bytes":i.file_size}
                try:
                    obj=json.loads(data)
                    if isinstance(obj,dict):
                        item["top_level_keys"]=sorted(obj)
                        for key in ["schema_version","schemaVersion","version","name","default","description"]:
                            if key in obj and isinstance(obj[key],(str,int,float,bool)) and len(str(obj[key]))<150:
                                item[key]=obj[key]
                except Exception:
                    item["text_headings"]=[x.strip()[:120] for x in data.splitlines() if x.strip().startswith("#")][:6]
                meta[name]=item
            if name.endswith(".so"):
                with z.open(i) as file:
                    header=file.read(64)
                arch="aarch64" if len(header)>20 and int.from_bytes(header[18:20],"little")==183 else "unknown"
                libraries.append({"path":name,"bytes":i.file_size,
                                  "elf_magic":header[:4].hex(),
                                  "architecture":arch})
        return {"nested_packages":packages,"asset_metadata":meta,"native_libraries":libraries}

def table(headers,rows):
    return "| "+" | ".join(headers)+" |\n| "+" | ".join(["---"]*len(headers))+" |\n"+"".join("| "+" | ".join(str(x).replace("|","/").replace("\n"," ") for x in row)+" |\n" for row in rows)
def main():
    c4=nested_c4()
    apk=inspect_apk()
    (OUT/"nested-audit-data.json").write_text(json.dumps({"c4":c4,"apk":apk},ensure_ascii=False,indent=2)+"\n")
    groups=Counter()
    for c in c4["containers"]:
        groups.update(c.get("extensions",{}))
    report=[
        "# Nested archive and native engine audit",
        "",
        "**Scope:** every nested COD4 `.iwd` in the 7.02 GB PC archive, every nested `.iwd` and `.zip` in the Android APK, and headers of packaged `.ff` and native binaries. Static only; no games were run.",
        "",
        "## Original PC Call of Duty 4 package",
        f"- IWD containers inspected: **{len(c4['containers'])}**.",
        f"- Files *inside* IWD archives: **{c4['total_nested_files']:,}**.",
        f"- Errors reading nested archives: **{len(c4['errors'])}**.",
        f"- Fastfiles identified (.ff): **{len(c4['fastfile_headers'])}**. These are engine-specific binary packages, not Godot-compatible scenes.",
        "### Most common internal file types",
        table(["Extension","Files"],groups.most_common(35)),
        "### Every IWD container",
        table(["Container","Files","Declared uncompressed bytes"],[(c["name"],c["files"],c["uncompressed_bytes"]) for c in c4["containers"]]),
        "### Potentially interesting names (filenames only; do not establish functionality)",
    ]
    for term in TERMS:
        found=c4["matches"][term]
        report.append(f"- `{term}`: {len(found)} displayed examples" + (": "+", ".join("`"+x[:110]+"`" for x in found[:8]) if found else "."))
    report += [
        "",
        "## Android package internal archives",
        table(["Package","Files","Declared uncompressed bytes"],[(p.get("name"),p.get("files","ERROR"),p.get("uncompressed_bytes","-")) for p in apk["nested_packages"]]),
        "### Native shared libraries",
        table(["Path","Bytes","CPU","ELF header"],[(x["path"],x["bytes"],x["architecture"],x["elf_magic"]) for x in apk["native_libraries"]]),
        "### Included metadata documents",
        table(["Document","Bytes","JSON keys"],[(v["path"],v["bytes"],", ".join(v.get("top_level_keys",[])[:30])) for v in apk["asset_metadata"].values()]),
        "",
        "## Compatibility assessment",
        "- The 7GB archive contains the packaged **PC Call of Duty 4: Modern Warfare game**, not editable Unreal or Godot project source.",
        "- The Android APK contains native ARM64 game libraries, graphics/driver packages and a small set of COD4X support files. It does **not** include the 7 GB PC asset archive internally.",
        "- `.iwd` files are themselves ZIP-like asset containers; the nested inventories reveal internal assets, but their proprietary formats may require a lawful conversion step.",
        "- `.ff` game fastfiles are compiled/packed engine assets; listing their names is not equivalent to extracting editable models, animations or maps.",
        "- No automatic coordinate conversion tool can turn those engine-specific packages directly into Godot scenes without intermediate decoders and reauthoring.",
        "- Do not redistribute proprietary assets without permission. This repository is public.",
        "",
        "## Machine-readable records",
        "- [C4 IWD file-by-file inventory](c4-iwd-file-inventory.json).",
        "- [Nested audit JSON, including APK driver packages](nested-audit-data.json).",
    ]
    if c4["errors"]:
        report.append("### Container errors")
        for e in c4["errors"][:20]:
            report.append(f"- {e['path']}: {e['error']}")
    (OUT/"NESTED_AUDIT.md").write_text("\n".join(report)+"\n")
    print("NESTED AUDIT:",json.dumps({"containers":len(c4["containers"]),"inner_files":c4["total_nested_files"],"iwd_exts":groups.most_common(16),"apk_nested":len(apk["nested_packages"]),"errors":c4["errors"][:5]}),flush=True)
if __name__=="__main__":
    main()
