-- FIX61: compound physical colliders for real mesh structures.
-- Unlike one giant entity AABB, archways have an open center and stairs
-- have individual step surfaces. Invisible proxies contain no duplicate art.
return function(M, entries)
 local by_id={}
 for _,v in ipairs(entries) do by_id[v.id]=v end
 local name='xz_zombies_classic:fort_collision_part'
 local function abs(x) return math.abs(x) end
 local function available(obj)
  return obj and obj.get_pos and obj:get_pos()
 end
 local function clear(owner)
  for _,obj in ipairs(owner._collision_parts or {}) do
   if available(obj) then obj:remove() end
  end
  owner._collision_parts={}
 end
 M.register_entity(':'..name,{
  initial_properties={
   physical=true,collide_with_objects=true,pointable=false,is_visible=false,
   visual='sprite',textures={'xz_fort_atlas.png'},static_save=false,
   collisionbox={-.1,-.1,-.1,.1,.1,.1},selectionbox={0,0,0,0,0,0},
  },
  on_activate=function(self)
   if self.object and self.object.set_armor_groups then
    self.object:set_armor_groups({immortal=1})
   end
  end,
  on_punch=function() return true end,
 })
 local function kind(entry)
  if not entry then return 'solid' end
  local label=(entry.label or ''):lower()
  if label:find('stair',1,true) or label:find('ramp',1,true)
   or label:find('steps',1,true) then return 'stairs' end
  if label:find('arch',1,true) or label:find('doorway',1,true)
   or label:find('gateway',1,true) or label:find('door frame',1,true) then return 'arch' end
  return 'solid'
 end
 local function bounds(entry,scale)
  local b=entry and entry.box or {-.48,-.48,-.48,.48,.48,.48}
  local hx=math.max(abs(b[1]),abs(b[4]))*scale
  local hy=math.max(abs(b[2]),abs(b[5]))*scale
  local hz=math.max(abs(b[3]),abs(b[6]))*scale
  return math.max(.02,hx),math.max(.02,hy),math.max(.02,hz)
 end
 local function add(owner,pos,yaw,cx,cy,cz,hx,hy,hz)
  local obj=M.add_entity(pos,name)
  if not obj then return end
  local c,s=math.cos(yaw),math.sin(yaw)
  local dx=c*cx+s*cz
  local dz=-s*cx+c*cz
  if obj.set_pos then obj:set_pos({x=pos.x+dx,y=pos.y+cy,z=pos.z+dz}) end
  local ax=abs(c)*hx+abs(s)*hz
  local az=abs(s)*hx+abs(c)*hz
  -- Give each separate step/post a real surface rather than the hollow
  -- full-architecture bounding box.
  if obj.set_properties then obj:set_properties({
   physical=true,collide_with_objects=true,is_visible=false,pointable=false,
   static_save=false,collisionbox={-ax,-hy,-az,ax,hy,az},
   selectionbox={0,0,0,0,0,0},
  }) end
  owner._collision_parts[#owner._collision_parts+1]=obj
 end
 local function update(owner,entry,scale,rotation,manual)
  clear(owner)
  local pos=owner.object and owner.object.get_pos and owner.object:get_pos()
  if not pos then return end
  local choice=manual
  if choice==nil or choice=='auto' then choice=kind(entry) end
  local hx,hy,hz=bounds(entry,scale)
  local yaw=rotation and rotation.y or 0
  local c,s=abs(math.cos(yaw)),abs(math.sin(yaw))
  local ax=c*hx+s*hz
  local az=s*hx+c*hz
  local large={-ax,-hy,-az,ax,hy,az}
  if choice=='none' or choice=='off' then
   owner.object:set_properties({physical=false,collide_with_objects=false,
    selectionbox=large,collisionbox={0,0,0,0,0,0}})
   return choice
  end
  if choice=='solid' then
   owner.object:set_properties({physical=true,collide_with_objects=true,
    selectionbox=large,collisionbox=large})
   return choice
  end
  -- The visual owner must NOT have a full physics box in compound modes.
  owner.object:set_properties({physical=false,collide_with_objects=false,
   pointable=true,selectionbox=large,collisionbox={0,0,0,0,0,0}})
  if choice=='arch' then
   local width=hx*2
   local pillar=math.max(.045,hx*.22)
   local top=math.max(.045,hy*.20)
   add(owner,pos,yaw,-hx+pillar,0,0,pillar,hy,hz)
   add(owner,pos,yaw, hx-pillar,0,0,pillar,hy,hz)
   add(owner,pos,yaw,0,hy-top,0,hx,top,hz)
  elseif choice=='stairs' or choice=='stairs_reverse' then
   local along_x=hx>hz
   local length=along_x and hx or hz
   local width=along_x and hz or hx
   local count=10
   for i=1,count do
    local progress=i/count
    local px=-length+(2*i-1)*length/count
    if choice=='stairs_reverse' then px=-px end
    local top=-hy+2*hy*progress
    local tall=math.max(.02,(top+hy)/2)
    local mid=-hy+tall
    if along_x then
     add(owner,pos,yaw,px,mid,0,length/count,tall,width)
    else
     add(owner,pos,yaw,0,mid,px,width,tall,length/count)
    end
   end
  else
   owner.object:set_properties({physical=true,collide_with_objects=true,
    selectionbox=large,collisionbox=large})
  end
  return choice
 end
 return {update=update,clear=clear,kind=kind,bounds=bounds}
end
