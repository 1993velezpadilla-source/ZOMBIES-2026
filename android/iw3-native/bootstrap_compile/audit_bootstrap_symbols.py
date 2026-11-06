#!/usr/bin/env python3
"""Audit unresolved symbols from genuine KisakCOD ARM64 object files.

This is an object-level dependency inventory, NOT a successful link or APK.
Usage: python3 audit_bootstrap_symbols.py undefined.txt defined.txt report.txt
llvm-nm inputs must use --format=posix.
"""
import pathlib
import sys


def read_symbols(path):
    result = set()
    for line in pathlib.Path(path).read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] in {"U", "T", "t", "W", "w", "D", "d", "B", "b", "R", "r", "V", "v"}:
            result.add(parts[0])
    return result


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: audit_bootstrap_symbols.py UNDEFINED DEFINED REPORT")
    undefined = read_symbols(argv[1])
    defined = read_symbols(argv[2])
    unresolved = sorted(undefined - defined)
    report = pathlib.Path(argv[3])
    report.write_text(
        "IW3 ORIGINAL ARM64 OBJECT-ONLY LINK GAP; NOT A LINKED ENGINE OR APK\n"
        + f"Unresolved unique symbols: {len(unresolved)}\n"
        + "\n".join(unresolved) + "\n"
    )
    print(f"IW3_BOOTSTRAP_UNRESOLVED_UNIQUE={len(unresolved)}")
    print("IW3_PLAYABLE_APK=false")


if __name__ == "__main__":
    main(sys.argv)
