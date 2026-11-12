-- FIX54 Viril v26 ORIGINAL Xziel combat HUD behavior, rendered through
-- Luanti's HUD primitive instead of Viril's C Draw_ColoredString().
-- Source (UNALTERED historical original):
-- 1993velezpadilla-source/config-old-3/scripts/patch_vril_combatfx.py
--   HUD_XzielDamageNumber, Xziel_DrawDamageNumbers
-- 1993velezpadilla-source/config-old-3/scripts/patch_quakec_combatfx.py
--   nzp_damage_number signal
-- This is a narrow C-renderer -> Lua-HUD API adapter, not new combat logic.
return function(M)
 local A={}
 local ACTIVE={}
 local MAX=24                       -- original XZIEL_DAMAGE_TEXT_MAX
 local LANES={-28,-16,-7,0,9,18,30} -- exact original C positions
 local DURATION=0.62                -- exact original lifetime, seconds
 local HOLD=0.34                    -- original opaque duration
 local FADE=0.28                    -- original fade duration
 local WHITE={245,245,245}         -- original body hit RGB
 local YELLOW={255,215,38}         -- original headshot RGB
 local function stamp()
  return M.get_us_time and M.get_us_time()/1000000 or M.get_gametime()
 end
 local function color(rgb,alpha)
  -- Luanti text HUD has RGB but no per-element alpha: composite original
  -- C alpha over dark ambience using RGB as best-supported approximation.
  local fac=math.max(0,math.min(1,alpha))
  return math.floor(rgb[1]*fac)*65536+math.floor(rgb[2]*fac)*256+math.floor(rgb[3]*fac)
 end
 function A.attach(player)
  local name=player:get_player_name()
  if ACTIVE[name] then return ACTIVE[name] end
  local state={slots={},next=1}
  ACTIVE[name]=state
  return state
 end
 function A.hit(player,damage,critical)
  damage=math.floor((tonumber(damage) or 0)+0.5)
  if damage<=0 then return false end
  local state=A.attach(player)
  local idx=state.next
  local slot=state.slots[idx]
  if not slot then
   local id=player:hud_add({
    hud_elem_type='text',text='',number=0xffffff,
    position={x=.5,y=.455},offset={x=0,y=0},
    alignment={x=0,y=0},z_index=225,
   })
   slot={id=id}
   state.slots[idx]=slot
  end
  slot.damage=damage
  slot.critical=not not critical
  slot.lane=(idx-1)%7+1
  slot.start=stamp()
  slot.active=true
  state.next=(idx%MAX)+1
  player:hud_change(slot.id,'text',tostring(damage))
  player:hud_change(slot.id,'number',color(critical and YELLOW or WHITE,1))
  player:hud_change(slot.id,'offset',{x=LANES[slot.lane],y=-8})
  return true
 end
 function A.step()
  local t=stamp()
  for name,state in pairs(ACTIVE) do
   local p=M.get_player_by_name(name)
   if p then
    for _,slot in ipairs(state.slots) do
     if slot.active then
      local elapsed=t-slot.start
      if elapsed>=DURATION then
       slot.active=false
       p:hud_change(slot.id,'text','')
      else
       local normalized=elapsed/DURATION
       local alpha=elapsed<HOLD and 1 or (1-(elapsed-HOLD)/FADE)
       local rgb=slot.critical and YELLOW or WHITE
       p:hud_change(slot.id,'offset',{
        x=LANES[slot.lane],y=-(8+25*normalized),
       })
       p:hud_change(slot.id,'number',color(rgb,alpha))
      end
     end
    end
   end
  end
 end
 function A.detach(player)
  local name=player:get_player_name()
  local state=ACTIVE[name]
  if not state then return end
  for _,slot in ipairs(state.slots) do player:hud_remove(slot.id) end
  ACTIVE[name]=nil
 end
 function A.stop(player)
  local s=ACTIVE[player:get_player_name()]
  if not s then return end
  for _,slot in ipairs(s.slots) do
   if slot.active then slot.active=false;player:hud_change(slot.id,'text','') end
  end
 end
 return A
end
