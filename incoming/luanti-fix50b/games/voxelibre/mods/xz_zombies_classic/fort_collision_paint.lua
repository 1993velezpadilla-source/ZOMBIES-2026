-- FIX62 collision paint: reliable physical voxel NODES, never fragile invisible
-- entity-vs-player collision. Poly Haven art stays untouched and visible.
return function(M,entries)
 local base='xz_zombies_classic:collision_paint_'
 local preview_name='xz_zombies_classic:collision_preview'
 local limits={max_nodes=2400,max_overlay=60,max_paint=800}
 local step=1/8
 local serial=0
 local preview={}
 local function round(x)return math.floor(x+0.5)end
 local function key(x,y,z)return x..','..y..','..z end
 local function cp(p)return {x=p.x,y=p.y,z=p.z}end
 local function rot(p,r,inv)
  local t=inv and -(r and r.y or 0) or (r and r.y or 0)
  local c,s=math.cos(t),math.sin(t)
  return {x=c*p.x+s*p.z,y=p.y,z=-s*p.x+c*p.z}
 end
 local function point(p)return {x=round(p.x),y=round(p.y),z=round(p.z)}end
 local function size_box(e,scale)
  local b=e.box or {-.48,-.48,-.48,.48,.48,.48}
  return math.max(.08,math.max(math.abs(b[1]),math.abs(b[4]))*scale),
    math.max(.08,math.max(math.abs(b[2]),math.abs(b[5]))*scale),
    math.max(.08,math.max(math.abs(b[3]),math.abs(b[6]))*scale)
 end
 local function kind(e)
  local t=(e.label or ''):lower()
  if t:find('stair',1,true) or t:find('ramp',1,true) then return 'stairs' end
  if t:find('arch',1,true) or t:find('gate',1,true) or t:find('doorway',1,true)
     or t:find('door frame',1,true) then return 'arch' end
  return 'solid'
 end
 local function owner_id(owner)
  if not owner.collider_uid then
   serial=serial+1
   local time=M.get_us_time and M.get_us_time() or (M.get_gametime and M.get_gametime()*1000000 or 0)
   owner.collider_uid=('xzpaint:%d:%d'):format(time,serial)
  end
  return owner.collider_uid
 end
 local function is_collision(n)
  return n and type(n.name)=='string' and n.name:sub(1,#base)==base
 end
 for level=1,8 do
  local top=-.5+level*step
  M.register_node(':'..base..level,{
   description='Invisible 3D Builder Collision '..level,
   drawtype='airlike',tiles={},paramtype='light',
   sunlight_propagates=true,walkable=true,pointable=false,
   diggable=false,buildable_to=false,is_ground_content=false,drop='',
   groups={not_in_creative_inventory=1},
   collision_box={type='fixed',fixed={-.5,-.5,-.5,.5,top,.5}},
   selection_box={type='fixed',fixed={0,0,0,0,0,0}},
  })
 end
 M.register_entity(':'..preview_name,{
  initial_properties={
   visual='cube',
   textures={
    'xz_fort_atlas.png^[colorize:#00C9FF:195',
    'xz_fort_atlas.png^[colorize:#00C9FF:195',
    'xz_fort_atlas.png^[colorize:#00C9FF:195',
    'xz_fort_atlas.png^[colorize:#00C9FF:195',
    'xz_fort_atlas.png^[colorize:#00C9FF:195',
    'xz_fort_atlas.png^[colorize:#00C9FF:195',
   },
   visual_size={x=1.01,y=1.01,z=1.01},
   glow=8,shaded=false,physical=false,collide_with_objects=false,
   pointable=false,static_save=false,
   collisionbox={0,0,0,0,0,0},selectionbox={0,0,0,0,0,0},
  }
 })
 local function clear_preview(owner)
  for _,o in ipairs(owner._collision_visuals or {}) do
   if o and o.get_pos and o:get_pos() then o:remove() end
  end
  owner._collision_visuals={}
 end
 local function current_node(p)
  return M.get_node_or_nil and M.get_node_or_nil(p) or (M.get_node and M.get_node(p))
 end
 local function owns(p,uid)
  local n=current_node(p)
  if not is_collision(n) then return false end
  if not M.get_meta then return false end
  return M.get_meta(p):get_string('xz_collision_owner')==uid
 end
 local function clear(owner)
  clear_preview(owner)
  local uid=owner.collider_uid
  if not uid then owner._paint_nodes={};return end
  for _,p in ipairs(owner._paint_nodes or {}) do
   if owns(p,uid) then M.set_node(p,{name='air'}) end
  end
  owner._paint_nodes={}
 end
 local function desired(owner,e,scale,rotation,mode)
  local center=owner.object and owner.object.get_pos and owner.object:get_pos()
  if not center then return {} end
  local hx,hy,hz=size_box(e,scale)
  local kind_mode=(mode==nil or mode=='auto') and kind(e) or mode
  if kind_mode=='auto' then kind_mode=kind(e) end
  if kind_mode=='stairs_reverse' then kind_mode='stairs_reverse' end
  local output,count={},0
  local function mark_world(p,level)
   local q=point(p)
   local k=key(q.x,q.y,q.z)
   if not output[k] then
    if count>=limits.max_nodes then return end
    count=count+1
   end
   output[k]={pos=q,level=level or 8}
  end
  local function sample(lx,ly,lz,level)
   local v=rot({x=lx,y=ly,z=lz},rotation)
   mark_world({x=center.x+v.x,y=center.y+v.y,z=center.z+v.z},level)
  end
  -- Keep two axis-aligned proxy lanes across thick walls, not a monolithic
  -- unrotatable entity AABB. The source architecture may extend 16+ blocks.
  local function loop(lo,hi,fn)
   if hi<lo then return end
   if hi-lo<1 then fn((lo+hi)/2);return end
   local k=math.floor(lo)
   while k<=hi+.50 do
    fn(k+.5)
    k=k+1
   end
  end
  if kind_mode=='none' or kind_mode=='off' or kind_mode=='paint' then return output end
  if kind_mode=='stairs' or kind_mode=='stairs_reverse' then
   local along_x=hx>hz
   local major=along_x and hx or hz
   local minor=along_x and hz or hx
   loop(-major,major,function(dist)
    local t=(dist+major)/(2*major)
    if kind_mode=='stairs_reverse' then t=1-t end
    t=math.max(0,math.min(1,t))
    local surface=-hy+2*hy*t
    local center_y=math.floor(center.y+surface+.5)
    local frac=(center.y+surface)-(center_y-.5)
    local level=math.max(1,math.min(8,math.ceil(frac/step)))
    loop(-minor,minor,function(width)
     local lx,lz=along_x and dist or width,along_x and width or dist
     local v=rot({x=lx,y=0,z=lz},rotation)
     mark_world({x=center.x+v.x,y=center_y,z=center.z+v.z},level)
     -- A stair has a FULL wedge underneath each tread. Supporting the
     -- entire lower volume (not only side rails) prevents the player from
     -- walking through its front faces and getting half-buried.
     loop(-hy,surface-1.05,function(wall_y)
      sample(lx,wall_y,lz,8)
     end)
    end)
   end)
  else
   -- Open gate: side supports + overhead lintel. Center of the door is EMPTY.
   local major=math.max(hx,hz)
   local minor=math.min(hx,hz)
   local span_z=hz>=hx
   local pillar=math.max(.6,major*.19)
   local beam=math.max(.55,hy*.18)
   local function filled(x,y,z)
    if kind_mode=='arch' then
     local span=span_z and math.abs(z) or math.abs(x)
     return span>=major-2*pillar or y>=hy-2*beam
    end
    -- 'solid' is a shell; interiors of round towers stay usable.
    local shell=math.min(hx,hy,hz)
    return math.abs(x)>=hx-1 or math.abs(z)>=hz-1
      or y>=hy-.8 or y<=-hy+.8 or shell<1
   end
   loop(-hx,hx,function(x)
    loop(-hz,hz,function(z)
     loop(-hy,hy,function(y)
      if filled(x,y,z) then sample(x,y,z,8) end
     end)
    end)
   end)
  end
  return output
 end
 local function map_relative(owner,p)
  local pos=owner.object:get_pos()
  local d={x=p.x-pos.x,y=p.y-pos.y,z=p.z-pos.z}
  local v=rot(d,owner.rotation,true)
  local scale=owner.scale or 1
  return {x=math.floor(v.x/scale*10000+.5)/10000,
          y=math.floor(v.y/scale*10000+.5)/10000,
          z=math.floor(v.z/scale*10000+.5)/10000}
 end
 local function map_world(owner,p)
  local pos=owner.object:get_pos()
  local scale=owner.scale or 1
  local v=rot({x=p.x*scale,y=p.y*scale,z=p.z*scale},owner.rotation)
  return point({x=pos.x+v.x,y=pos.y+v.y,z=pos.z+v.z})
 end
 local function mapped_mask(owner)
  local mask={}
  for _,e in ipairs(owner.paint_deltas or {}) do
   if type(e)=='table' and type(e.x)=='number' and type(e.y)=='number'
      and type(e.z)=='number' and (e.op=='add' or e.op=='erase') then
    local p=map_world(owner,e)
    mask[key(p.x,p.y,p.z)]={pos=p,op=e.op}
   end
  end
  return mask
 end
 local function update(owner,e,scale,rotation,manual)
  if not owner or not owner.object or not owner.object.get_pos or not owner.object:get_pos() then return end
  owner.scale=scale
  owner.rotation=rotation
  local mode=manual or 'auto'
  owner.collider_uid=owner_id(owner)
  clear_preview(owner)
  local planned=desired(owner,e,scale,rotation,mode)
  for k,v in pairs(mapped_mask(owner)) do
   if v.op=='erase' then planned[k]=nil
   else planned[k]={pos=v.pos,level=8} end
  end
  local accepted={}
  local before={}
  for _,p in ipairs(owner._paint_nodes or {}) do
   before[key(p.x,p.y,p.z)]=p
  end
  for k,p in pairs(before) do
   if not planned[k] and owns(p,owner.collider_uid) then
    M.set_node(p,{name='air'})
   end
  end
  for k,v in pairs(planned) do
   local p=v.pos
   local old=current_node(p)
   if old and (old.name=='air' or owns(p,owner.collider_uid)) then
    local level=math.max(1,math.min(8,math.floor(v.level+.5)))
    local wanted=base..level
    if old.name~=wanted then
     M.set_node(p,{name=wanted})
     M.get_meta(p):set_string('xz_collision_owner',owner.collider_uid)
    end
    accepted[#accepted+1]=cp(p)
   end
  end
  owner._paint_nodes=accepted
  owner.object:set_properties({
   physical=false,collide_with_objects=false,
   collisionbox={0,0,0,0,0,0},
   pointable=true,
  })
  if owner.paint_visible then
   local seen=0
   for _,p in ipairs(accepted) do
    if seen>=limits.max_overlay then break end
    local obj=M.add_entity and M.add_entity(p,preview_name)
    if obj then
     owner._collision_visuals=owner._collision_visuals or {}
     owner._collision_visuals[#owner._collision_visuals+1]=obj
     seen=seen+1
    end
   end
  end
  return #accepted
 end
 local function apply_brush(owner,e,mode,at,action,radius)
  if not owner or not owner.object or not owner.object:get_pos() then return 0 end
  local center=point(at)
  local n=0
  local list=owner.paint_deltas or {}
  local r=math.max(0,math.min(3,math.floor(radius or 0)))
  local edits={}
  for dx=-r,r do for dy=-r,r do for dz=-r,r do
   if dx*dx+dy*dy+dz*dz<=r*r then
    edits[#edits+1]={x=center.x+dx,y=center.y+dy,z=center.z+dz}
   end
  end end end
  if #edits==0 then edits={{x=center.x,y=center.y,z=center.z}} end
  local mask={}
  for i,x in ipairs(list) do
   local p=map_world(owner,x)
   mask[key(p.x,p.y,p.z)]=i
  end
  for _,p in ipairs(edits) do
   local k=key(p.x,p.y,p.z)
   local entry=map_relative(owner,p)
   entry.op=action=='erase' and 'erase' or 'add'
   if mask[k] then
    if list[mask[k]].op~=entry.op then n=n+1 end
    list[mask[k]]=entry
   elseif #list<limits.max_paint then
    list[#list+1]=entry;n=n+1;mask[k]=#list
   end
  end
  owner.paint_deltas=list
  return n
 end
 local function bucket(owner,e,mode,at,plane)
  -- Bounded two-dimensional flood fill in a user's drawn outline.
  -- Never flood the entire world when the outline is open.
  local c=point(at)
  local horizontal=plane or 'xz'
  local axes=horizontal=='xy' and {'x','y'} or
             horizontal=='yz' and {'y','z'} or {'x','z'}
  local a,b=axes[1],axes[2]
  local map={}
  for _,p in ipairs(owner._paint_nodes or {}) do map[key(p.x,p.y,p.z)]=true end
  local queue={c}
  local seen={[key(c.x,c.y,c.z)]=true}
  local list,escaped={},false
  local h=1
  local maxdist=16
  while queue[h] and #list<=limits.max_paint do
   local p=queue[h];h=h+1
   local k=key(p.x,p.y,p.z)
   if not map[k] then
    if math.abs(p[a]-c[a])>=maxdist or math.abs(p[b]-c[b])>=maxdist then
     escaped=true;break
    end
    list[#list+1]=p
    for _,step2 in ipairs({{1,0},{-1,0},{0,1},{0,-1}}) do
     local v=cp(p)
     v[a]=v[a]+step2[1];v[b]=v[b]+step2[2]
     local nk=key(v.x,v.y,v.z)
     if not seen[nk] and not map[nk] then seen[nk]=true;queue[#queue+1]=v end
    end
   end
  end
  if escaped or #list>limits.max_paint then return 0,'open' end
  local count=0
  for _,p in ipairs(list) do count=count+apply_brush(owner,e,mode,p,'add',0) end
  return count,'filled'
 end
 local function paint(owner,e,mode,position,action,radius,plane)
  if not owner or not position or not owner.object or not owner.object:get_pos() then return 0,'invalid' end
  local n,tag
  if action=='bucket' then n,tag=bucket(owner,e,mode,position,plane)
  else n=apply_brush(owner,e,mode,position,action,radius);tag=action end
  if n>0 then update(owner,e,owner.scale,owner.rotation,mode) end
  return n,tag
 end
 return {update=update,clear=clear,paint=paint,clear_preview=clear_preview,kind=kind,
   registered_prefix=base,visible_name=preview_name}
end
