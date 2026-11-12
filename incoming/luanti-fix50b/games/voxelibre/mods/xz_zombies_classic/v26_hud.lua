-- FIX52B COD-style compact in-game HUD, no text in top chat/pause region.
-- Floating +10/+50/+100 score notifications cascade upward on ACTUAL hits.
-- A maximum of ten reused entries per player avoids allocation/performance spikes.
return function(M)
 local A={}
 local states={}
 local MAX=10
 local COLOR_GOLD=0xffc35a
 local COLOR_BRIGHT=0xffeea1
 local COLOR_ROUND=0xc84635
 local function now()
  return M.get_us_time and M.get_us_time()/1000000 or M.get_gametime()
 end
 function A.attach(p)
  local name=p:get_player_name()
  if states[name] then return end
  local s={active=false,slots={},clock=0,flash_until=0,points=0}
  s.round=p:hud_add({hud_elem_type='text',
   position={x=0.028,y=0.950},alignment={x=1,y=-1},
   number=COLOR_ROUND,text='',z_index=215})
  s.remaining=p:hud_add({hud_elem_type='text',
   position={x=0.028,y=0.906},alignment={x=1,y=-1},
   number=0xcac7c1,text='',z_index=215})
  s.score=p:hud_add({hud_elem_type='text',
   position={x=0.790,y=0.946},alignment={x=1,y=-1},
   number=COLOR_GOLD,text='',z_index=215})
  states[name]=s
 end
 function A.detach(p)
  local name=p:get_player_name()
  local s=states[name]
  if not s then return end
  for _,h in ipairs({s.round,s.remaining,s.score}) do p:hud_remove(h) end
  for _,slot in ipairs(s.slots) do p:hud_remove(slot.id) end
  states[name]=nil
 end
 function A.mode(p,playing)
  A.attach(p)
  local s=states[p:get_player_name()]
  s.active=playing
  if not playing then
   p:hud_change(s.round,'text','')
   p:hud_change(s.remaining,'text','')
   p:hud_change(s.score,'text','')
   for _,slot in ipairs(s.slots) do
    slot.expires=0
    p:hud_change(slot.id,'text','')
   end
  else
   p:hud_change(s.score,'text',('%d'):format(s.points))
  end
 end
 function A.wave(p,round,remaining,playing)
  A.attach(p)
  local s=states[p:get_player_name()]
  if not playing then return A.mode(p,false) end
  if not s.active then A.mode(p,true) end
  if round<=0 then
   p:hud_change(s.round,'text','ZOMBIES')
   p:hud_change(s.remaining,'text','PREPARAR')
  else
   p:hud_change(s.round,'text',('RONDA %02d'):format(math.max(0,round)))
   p:hud_change(s.remaining,'text',('%d RESTANTES'):format(math.max(0,remaining)))
  end
 end
 function A.points(p,total)
  A.attach(p)
  local s=states[p:get_player_name()]
  s.points=math.max(0,math.floor(total or 0))
  if s.active then p:hud_change(s.score,'text',('%d'):format(s.points)) end
 end
 function A.award(p,amount)
  local n=math.floor(tonumber(amount) or 0)
  if n<=0 then return end
  A.attach(p)
  local s=states[p:get_player_name()]
  if not s.active then return end
  local t=now()
  local slot
  for _,candidate in ipairs(s.slots) do
   if candidate.expires<=t then slot=candidate;break end
  end
  if not slot and #s.slots<MAX then
   local id=p:hud_add({hud_elem_type='text',position={x=0.793,y=0.862},
    alignment={x=1,y=0},number=COLOR_BRIGHT,text='',z_index=220})
   slot={id=id,expires=0}
   s.slots[#s.slots+1]=slot
  end
  if not slot then slot=s.slots[1] end
  slot.started=t
  slot.expires=t+0.92
  slot.value=n
  slot.jitter=(#s.slots%4)*0.012
  p:hud_change(slot.id,'position',{x=0.793+slot.jitter,y=0.862})
  p:hud_change(slot.id,'number',COLOR_BRIGHT)
  p:hud_change(slot.id,'text','+'..n)
  s.flash_until=t+0.18
  p:hud_change(s.score,'number',COLOR_BRIGHT)
 end
 function A.step(dt)
  local t=now()
  for name,s in pairs(states) do
   local p=M.get_player_by_name(name)
   if p then
    if s.flash_until>0 and t>s.flash_until then
     p:hud_change(s.score,'number',COLOR_GOLD)
     s.flash_until=0
    end
    if s.active then
     for _,slot in ipairs(s.slots) do
      if slot.expires>0 then
       if t>=slot.expires then
        p:hud_change(slot.id,'text','')
        slot.expires=0
       else
        local progress=math.max(0,math.min(1,(t-slot.started)/0.92))
        p:hud_change(slot.id,'position',{
          x=0.793+slot.jitter, y=0.862-progress*0.14})
        if progress>0.70 then p:hud_change(slot.id,'number',COLOR_GOLD) end
       end
      end
     end
    end
   end
  end
 end
 return A
end
