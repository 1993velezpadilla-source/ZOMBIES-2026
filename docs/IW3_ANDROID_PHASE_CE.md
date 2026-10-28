# IW3 Android ARM64 portability follow-up — Phase CE

Date: 2026-10-28

## Failure reviewed before this change

At PR #4 head `1e04d2c7ac2ddeec292cc3fca27117fcf65bf0b8`, Actions run [40741944199](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40741944199) failed while compiling the original sentient/path-node trigger service for Android ARM64:

- `pathnode_tree_nodes_t` was hard-asserted to 8 bytes, but its runtime pointer member makes it 16 bytes under LP64.
- `actor_animapi.h` still used MSVC-only `__declspec(align(4))`, which Clang rejects.
- The Windows SP compile and Killhouse workflow also failed because `g_local.h` declared `G_RunFrame(ServerFrameExtent, ...)` without directly including the header that defines `ServerFrameExtent`.

## Changes

1. In the original `pathnode.h`, document Win32 and LP64 runtime layouts and assert pointer-width-specific sizes for `pathnode_tree_nodes_t`, `pathnode_tree_info_t`, and `pathnode_tree_t`. The native pointer remains a native pointer; no serialized game data is rewritten.
2. In the original `actor_animapi.h`, replace the MSVC-only alignment spelling with standard C++ `alignas(4)` and assert the unchanged `scr_animscript_t` size/alignment (8/4).
3. In the original `g_local.h`, include `server/server_frame.h` directly so the public `G_RunFrame` declaration does not depend on accidental include order.
4. Extend the existing sentient-trigger regression to guard these ABI/header contracts.

## Validation status

The code changes are committed together so Actions can test one coherent revision. The new regression assertions are source-level guards; the native ARM64 workflow must still prove the actual compiler accepts the extracted original trigger services. The Windows SP build must also be rerun to verify the include-order failure is gone.

## Scope boundary — no gameplay claim

This phase fixes compile/ABI blockers only. It does not link or execute the complete Android runtime, load a licensed FastFile or map, render a real scene, connect touch input to the original game loop, or prove weapons/actors on a physical ARM64 device. The JNI diagnostic APK remains diagnostic, not a game. PR #4 must remain open and unmerged.
