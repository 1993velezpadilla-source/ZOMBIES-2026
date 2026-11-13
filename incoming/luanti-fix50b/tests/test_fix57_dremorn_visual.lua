-- FIX57 rigorous Lua regression: only asset-authorized model is enabled.
local file='incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/dremorn_visual.lua'
local files,logs={},{ }
local M={
 get_dir_list=function(dir)
  if dir:find('/models$') then return files.models or {} end
  if dir:find('/textures$') then return files.textures or {} end
  return {}
 end,
 log=function(_,msg)logs[#logs+1]=msg end
}
local function new_adapter()return assert(loadfile(file))()(M,'some_mod') end
local A=new_adapter()
assert(not A.enabled,'No downloaded model: native zombie must be 100% unchanged')
local calls=0
local untouched={set_properties=function()calls=calls+1 end,
 play_animation=function()calls=calls+1 end,stop_animation=function()calls=calls+1 end}
assert(not A.apply({set_animation=function()end},untouched) and calls==0)
files.models={'xz_dremorn_zombie.glb'}
A=new_adapter()
assert(not A.enabled,'Texture missing must not produce a white zombie')
files.textures={'xz_dremorn_body.png'}
A=new_adapter()
assert(A.enabled)
local ops={}
local obj={velocity={x=0,y=0,z=0}}
function obj:get_properties()return {mesh='mobs_mc_zombie.b3d',textures={'mobs_mc_zombie.png'}}end
function obj:set_properties(p) ops[#ops+1]={'properties',p};return true end
function obj:play_animation(track,spec)
 ops[#ops+1]={'play',track,spec}
 return true
end
function obj:stop_animation(track) ops[#ops+1]={'stop',track};return true end
function obj:update_animation(track,options) ops[#ops+1]={'update',track,options};return true end
function obj:get_velocity()return self.velocity end
local common={stand_start=40,stand_end=49,walk_start=0,walk_end=39}
local original_speed=function()error('old animation speed must not be invoked') end
local entity={set_animation=function()error('legacy animation must not be used')end,
 set_animation_speed=original_speed,head_swivel='head.control',
 run_velocity=2.5,walk_velocity=.8,animation=common,state='stand'}
assert(A.apply(entity,obj))
assert(entity._dremorn_original_mesh=='mobs_mc_zombie.b3d')
assert(entity._dremorn_original_textures[1]=='mobs_mc_zombie.png')
assert(entity.head_swivel==nil)
assert(entity.animation~=common,'Never mutate shared mob registration animation')
assert(common.die_start==nil and common.die_end==nil)
assert(entity.animation.die_start==0 and entity.animation.die_end==1.6
 and entity.animation.die_speed==1,'Mob physics checks die frame ranges')
assert(ops[1][1]=='properties' and ops[1][2].mesh=='xz_dremorn_zombie.glb')
assert(ops[2][1]=='play' and ops[2][2]=='idle1')
entity:set_animation('stand')
assert(#ops==2,'Avoid restarting an unchanged idle')
entity:set_animation('walk')
assert(ops[3][1]=='stop' and ops[3][2]=='idle1')
assert(ops[4][1]=='play' and ops[4][2]=='walk')
obj.velocity.x=.8
entity:set_animation_speed()
assert(#ops==4,'Ignore speed differences below 0.2 for mobile')
obj.velocity.x=.45
entity:set_animation_speed()
assert(ops[5][1]=='update' and ops[5][2]=='walk'
  and ops[5][3].speed<1,'Use named glTF update, not legacy frame speed')
entity:set_animation('run')
assert(ops[6][1]=='stop' and ops[7][1]=='play' and ops[7][2]=='run')
obj.velocity.x=3.5
entity:set_animation_speed()
assert(ops[8][1]=='update' and ops[8][2]=='run'
 and ops[8][3].speed>1,'Run speed tracks live velocity')
entity:set_animation('punch')
assert(ops[10][1]=='play' and ops[10][2]=='atack1'
  and ops[10][3].loop==false)
entity:set_animation('punch2')
assert(ops[12][1]=='play' and ops[12][2]=='atack2')
entity.state='die'
entity:set_animation('run')
assert(#ops==12,'Do not override death with running state')
entity:set_animation('die')
assert(ops[14][1]=='play' and ops[14][2]=='death1'
 and ops[14][3].loop==false)
assert(entity._current_animation=='die')
assert(A.track_names.die=='death1' and A.track_names.punch=='atack1')
-- No-op unknown engine animation maps safely to idle, without invoking .b3d frames.
entity.state='stand'
entity:set_animation('unknown')
assert(ops[16][1]=='play' and ops[16][2]=='idle1')
-- First GLB animation failure must roll back object and original methods.
local broken={get_properties=obj.get_properties,set_properties=obj.set_properties,
 stop_animation=obj.stop_animation,
 play_animation=function() return false end}
local backup=function() return 'native' end
local b={set_animation=backup,set_animation_speed=original_speed,
 head_swivel='head.control',animation={stand_start=1}}
assert(not A.apply(b,broken))
assert(b.set_animation==backup and b.set_animation_speed==original_speed
 and b.head_swivel=='head.control','failed GLB application must restore behavior')
assert(ops[#ops][1]=='properties'
 and ops[#ops][2].mesh=='mobs_mc_zombie.b3d','Must restore original model')
print('PASS FIX57: optional asset gate, native fallback, full glTF named tracks, FPS-safe speed, death and rollback')
