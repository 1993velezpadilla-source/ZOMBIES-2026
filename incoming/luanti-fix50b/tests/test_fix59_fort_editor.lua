-- FIX59: cyan selection FX, polished narrow-device editor, safe node rotation.
local mod=assert(arg[1], 'expected generated Fort mod directory')
local manifest=assert(loadfile(mod..'/polyhaven_fort_manifest.lua'))()
assert(#manifest>0)
local entry=manifest[1]
local location={x=3,y=4,z=5}
local node={name='xz_zombies:'..entry.id,param1=0,param2=0}
local captures={}
local forms={}
local fx={}
local onfields,onleave
local active=false
local blocked=false
local M
M={
 registered_nodes={},
 is_singleplayer=function() return true end,
 is_protected=function() return blocked end,
 formspec_escape=function(s) return tostring(s):gsub('\\','\\\\'):gsub(']', '\\]'):gsub(';', '\\;') end,
 register_entity=function(name,def)
  assert(name==':xz_zombies_classic:fort_select_fx' or name==':xz_zombies_classic:fort_architecture')
  if name==':xz_zombies_classic:fort_select_fx' then
   assert(def.initial_properties.static_save==false)
   captures.entity_def=def
  else
   assert(def.initial_properties.static_save==true)
   captures.architecture_def=def
  end
 end,
 register_node=function(name,def)
  M.registered_nodes[name:sub(2)]=def
 end,
 register_on_player_receive_fields=function(callback) onfields=callback end,
 register_on_leaveplayer=function(callback) onleave=callback end,
 get_node_or_nil=function() return node end,
 swap_node=function(pos,new) 
  assert(pos.x==location.x and pos.y==location.y and pos.z==location.z)
  node=new
 end,
 add_entity=function(pos,name)
  assert(name=='xz_zombies_classic:fort_select_fx')
  local obj={position={x=pos.x,y=pos.y,z=pos.z}}
  function obj:set_properties(p) self.props=p end
  function obj:get_pos() return self.position end
  function obj:remove() self.position=nil end
  function obj:set_yaw(y) self.yaw=y end
  fx[#fx+1]=obj
  return obj
 end,
 get_player_window_information=function() return {max_formspec_size={x=5.35,y=4.8}} end,
 show_formspec=function(p,form,text)
  forms[p]={name=form,text=text}
 end,
 log=function() end,
}
-- The callback closes over M; all calls happen after this declaration.
local p={
 is_player=function() return true end,
 get_player_name=function() return 'pixel_fold' end,
 get_wielded_item=function()
  return {get_name=function() return captures.held or '' end}
 end,
}
local adapter=assert(loadfile(mod..'/fort_editor.lua'))()(M,mod,function() return not active end)
assert(adapter.try_select)
local num=assert(loadfile(mod..'/polyhaven_fort.lua'))()(M,mod,adapter)
assert(num==#manifest)
assert(type(M.registered_nodes[node.name].on_rightclick)=='function')
-- Empty-hand touch selects the piece and opens a compact styled panel.
M.registered_nodes[node.name].on_rightclick(location,node,p)
assert(forms.pixel_fold.name=='xz_zombies:fort_transform')
local text=forms.pixel_fold.text
assert(text:find('ZOMBIES  /  3D EDITOR',1,true))
assert(text:find('#20C9FF',1,true))
assert(text:find('GIRAR %-90'))
assert(text:find('GIRAR %+90'))
assert(text:find('size%[5%.15,4%.50%]'))
assert(text:find('scale_plus',1,true) and text:find('scale_minus',1,true))
assert(captures.architecture_def and captures.architecture_def.get_staticdata)
assert(#fx==1 and fx[1].props.mesh==entry.mesh)
assert(fx[1].props.pointable==false and fx[1].props.physical==false)
-- Rotate the ORIGINAL node, preserving mesh, metadata and node scale.
onfields(p,'xz_zombies:fort_transform',{right=true})
assert(node.name=='xz_zombies:'..entry.id and node.param2==1)
assert(fx[1].yaw)
onfields(p,'xz_zombies:fort_transform',{left=true})
assert(node.param2==0)
onfields(p,'xz_zombies:fort_transform',{close=true})
assert(fx[1]:get_pos()==nil)
-- Don't hijack taps while holding a building block.
captures.held='mcl_core:stone'
assert(adapter.try_select(p,location,false)==false)
assert(adapter.try_select(p,location,true)==true)
onleave(p)
-- Stop editing during zombie rounds, and respect protected maps.
active=true
assert(adapter.try_select(p,location,true)==false)
active=false
blocked=true
assert(adapter.try_select(p,location,true)==false)
blocked=false
assert(adapter.try_select(p,location,true)==true)
-- Undo form closure leaves no lingering hologram entity.
onfields(p,'xz_zombies:fort_transform',{quit=true})
assert(fx[#fx]:get_pos()==nil)
print('PASS FIX59 backwards compatibility: original 90-degree node rotation, premium selection, protected maps, and no unintended conversion')
