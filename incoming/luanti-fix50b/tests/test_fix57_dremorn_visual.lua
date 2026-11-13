-- FIX57: Original zombie must remain unchanged unless BOTH legal media are present.
local mod='incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/dremorn_visual.lua'
local files={}
local M={get_dir_list=function(dir)
 if dir:find('/models$') then return files.models or {} end
 if dir:find('/textures$') then return files.textures or {} end
 return {}
end}
local A=assert(loadfile(mod))()(M,'some_mod')
assert(not A.enabled,'Without an authentic model the original zombie must remain intact')
local n=0
local mock={set_properties=function()n=n+1 end,play_animation=function()n=n+1 end,
 stop_animation=function()n=n+1 end}
local e={mesh='native.b3d',textures={'native.png'},set_animation=function()n=n+100 end}
assert(not A.apply(e,mock) and n==0)
files.models={'xz_dremorn_zombie.glb'}
A=assert(loadfile(mod))()(M,'some_mod')
assert(not A.enabled,'Missing texture must not render white zombie')
files.textures={'xz_dremorn_body.png'}
A=assert(loadfile(mod))()(M,'some_mod')
assert(A.enabled)
local messages={}
local obj={}
function obj:set_properties(p) messages[#messages+1]={'props',p} end
function obj:play_animation(track,spec) messages[#messages+1]={'play',track,spec} end
function obj:stop_animation(track) messages[#messages+1]={'stop',track} end
local entity={set_animation=function()error('old frame-based animation must not be used') end,
 mesh='native.b3d',textures={'native.png'},head_swivel='head.control'}
assert(A.apply(entity,obj))
assert(entity._dremorn_original_mesh=='native.b3d')
assert(entity.head_swivel==nil)
assert(messages[1][1]=='props' and messages[1][2].mesh=='xz_dremorn_zombie.glb')
assert(messages[2][1]=='play' and messages[2][2]=='idle1')
entity:set_animation('stand')
assert(#messages==2,'Do not restart same track every engine frame')
entity:set_animation('walk')
assert(messages[3][1]=='stop' and messages[3][2]=='idle1')
assert(messages[4][1]=='play' and messages[4][2]=='walk')
entity:set_animation('run')
assert(messages[6][1]=='play' and messages[6][2]=='run')
entity:set_animation('punch')
assert(messages[8][1]=='play' and messages[8][2]=='atack1' and messages[8][3].loop==false)
entity:set_animation('die')
assert(messages[10][1]=='play' and messages[10][2]=='death1' and messages[10][3].loop==false)
assert(entity._current_animation=='die')
assert(entity.mesh=='native.b3d' and entity.textures[1]=='native.png',
 'Never replace VoxeLibre registration or original state')
print('PASS FIX57 optional legal Dremorn mesh, native fallback, named animations and death')
