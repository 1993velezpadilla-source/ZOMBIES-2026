#pragma once

// ABI-only declarations used to compile original shared IW3 data structures
// on Android. These declarations do not implement D3D9 or a renderer.
// Windows builds continue to include the real Direct3D 9 SDK headers.
#include <type_traits>

struct IDirect3DVertexBuffer9;
struct IDirect3DIndexBuffer9;
struct IDirect3DBaseTexture9;
struct IDirect3DTexture9;
struct IDirect3DVolumeTexture9;
struct IDirect3DCubeTexture9;
struct IDirect3DQuery9;
struct IDirect3DSurface9;
struct IDirect3DVertexDeclaration9;
struct IDirect3DVertexShader9;
struct IDirect3DPixelShader9;

// D3D9 defines _D3DFORMAT as an int-sized enum. The original GfxImageLoadDef
// stores this enum by value, so its underlying width must remain explicit.
enum _D3DFORMAT : int;
static_assert(sizeof(_D3DFORMAT) == sizeof(int),
              "D3D9 format field must retain the original 32-bit ABI");
