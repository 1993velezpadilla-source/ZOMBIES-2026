-- FIX62 Android flow regression: world USE applies paint/erase without empty hand.
local mod=assert(arg[1],'pass generated CC0 Fort mod path')
local real=assert(loadfile(mod..'/polyhaven_fort_manifest.lua'))()
local gate
for _,e in ipairs(real) do if (e.label or ''):lower():find('gate',1,true) then gate=e;break end end
assert(gate,'Poly Haven pack must contain a real fort gate')
local defs,nodes,world,metas,store,forms,objects={}, {}, {}, {}, {}, {}, {}
local received,closed
local tick=0
local last_object
local function key(p)return p.x..','..p.y..','..p.z end
local function deep(v)
 if type(v)~='table' then return v end
 local a={}
 for k,x in pairs(v) do a[k]=deep(x) end
 return a
end
local M
M={
 registered_nodes=nodes,
 is_singleplayer=function()return true end,
 is_creative_enabled=function()return true end,
 is_protected=function()return false end,
 check_player_privs=function()return true end,
 get_us_time=function()tick=tick+1;return tick end,
 serialize=function(d)
  tick=tick+1
  local id='data:'..tick
  store[id]=deep(d)
  return id
 end,
 deserialize=function(s)return deep(store[s])end,
 get_player_window_information=function()return {max_formspec_size={x=5.35,y=4.8}}end,
 formspec_escape=function(s)return tostring(s):gsub(']','\\]'):gsub(';','\\;')end,
 register_entity=function(n,d)defs[n:sub(2)]=d end,
 register_node=function(n,d)nodes[n:sub(2)]=d end,
 register_globalstep=function()end,
 register_on_leaveplayer=function()end,
 register_on_player_receive_fields=function(f)received=f end,
 show_formspec=function(name,f,data)forms[name]={id=f,s=data}end,
 close_formspec=function(name,f)closed={name=name,id=f}end,
 chat_send_player=function()end,
 log=function()end,
 get_node_or_nil=function(p)return world[key(p)] or {name='air'} end,
 get_meta=function(p)
  local k=key(p)
  metas[k]=metas[k] or {}
  return {
   set_string=function(_,n,v)metas[k][n]=v end,
   get_string=function(_,n)return metas[k][n] or '' end
  }
 end,
 set_node=function(p,n)world[key(p)]={name=n.name};metas[key(p)]={}end,
 remove_node=function(p)world[key(p)]={name='air'}end,
}
function M.add_entity(pos,ename,data)
 local def=assert(defs[ename])
 local obj={at=deep(pos),properties=deep(def.initial_properties or {}),name=ename}
 function obj:get_pos()return self.at end
 function obj:set_pos(p)self.at=deep(p)end
 function obj:remove()self.at=nil end
 function obj:set_properties(p)for k,v in pairs(p)do self.properties[k]=deep(v)end end
 function obj:get_luaentity()return self.lua end
 function obj:set_rotation(p)self.rotation=deep(p)end
 function obj:set_yaw(y)self.yaw=y end
 function obj:set_armor_groups(t)self.armor=t end
 local lua=setmetatable({name=ename,object=obj},{__index=def})
 obj.lua=lua
 objects[#objects+1]=obj
 if lua.on_activate then lua:on_activate(data or '') end
 if ename=='xz_zombies_classic:fort_architecture' then last_object=obj end
 return obj
end
local ray
M.raycast=function(from,to,objects,liquids)
 local once=false
 return function()
  if once then return nil end
  once=true
  return ray
 end
end
local held='ak47dev:ak47'
local p={
 get_player_name=function()return 'android' end,
 is_player=function()return true end,
 get_wielded_item=function()return {get_name=function()return held end}end,
 get_pos=function()return {x=0,y=1,z=0} end,
 get_look_dir=function()return {x=0,y=0,z=1}end,
 get_properties=function()return {eye_height=1.47}end,
}
local editor=assert(loadfile(mod..'/fort_editor_v2.lua'))()(M,mod,function()return true end)
local total=assert(loadfile(mod..'/polyhaven_fort.lua'))()(M,mod,editor)
assert(total==#real)
assert(nodes['xz_zombies_classic:collision_paint_8'].walkable==true)
assert(defs['xz_zombies_classic:fort_collision_part']==nil,'must not rely on old fragile entity proxies')
local item={
 get_name=function()return 'xz_zombies:'..gate.id end,
 take_item=function()error('creative mode should never consume item')end
}
local pt={type='node',under={x=1,y=-1,z=3},above={x=1,y=0,z=3},
 intersection_point={x=.12,y=0,z=3.08}}
assert(editor.place_new(item,p,pt)==item)
local obj=assert(last_object)
local l=obj.lua
assert(math.abs(l.scale-gate.natural_scale)<.001)
assert(forms.android.s:find('tab_5',1,true),'Paint tab is not on Android panel')
local function send(f)
 assert(received(p,'xz_zombies:fort_transform',f))
end
send({tab_5=true})
local fs=forms.android.s
for _,control in ipairs({'tool_brush','tool_erase','tool_bucket','brush_minus','brush_plus','paint_start','paint_stop'}) do
 assert(fs:find(control,1,true),'Touch missing '..control)
end
send({tool_brush=true})
send({brush_plus=true})
send({paint_start=true})
assert(closed and closed.id=='xz_zombies:fort_transform')
assert(l.paint_visible==true)
assert(l.collider_uid)
ray={type='object',ref=obj,intersection_point={
 x=math.floor(obj.at.x+.5),y=math.floor(obj.at.y+.5),z=math.floor(obj.at.z+.5)
}}
local hit=ray.intersection_point
local before=M.get_node_or_nil(hit).name
-- Must be an open gate center to test painting through the doorway.
assert(before=='air','baseline gate opening blocked before painting')
assert(editor.use_target(p),'equipped gun USE did not invoke painting')
assert(M.get_node_or_nil(hit).name~='air','paint brush made no physical node')
assert(#l.paint_deltas>0 and #l._paint_nodes>0)
assert(editor.paint_panel(p),'editor menu cannot re-open active painting session')
send({tool_erase=true})
send({paint_start=true})
assert(editor.use_target(p))
assert(M.get_node_or_nil(hit).name=='air','eraser failed to clear collision')
assert(editor.paint_panel(p))
send({paint_stop=true})
assert(l.paint_visible==false)
for _,ghost in ipairs(l._collision_visuals or {}) do
 assert(not ghost:get_pos(),'cyan collision paint remained in game after leaving editor')
end
local file=l:get_staticdata()
local saved=assert(store[file])
assert(saved.collider_uid and type(saved.paint_deltas)=='table')
assert(type(saved.collision_cells)=='table')
print('PASS FIX62 UI: 5-tab mobile no-scroll Paint panel, button-driven brush/eraser, USE with gun, world closes/reopens, persisted invisible physical collision and edit preview cleanup')
