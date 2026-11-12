-- Exact NZ:P v0.26 gameplay values and state transitions, translated from
-- original QuakeC; NOT a newly designed scoring or barricade system.
-- Source: 1993velezpadilla-source/config-old-3,
-- third_party/viril-iw3-v026/quakec/source/server/{damage.qc,rounds.qc,
-- ai/zombie_core.qc,ai/ai_core.qc,entities/window.qc}
-- Copyright NZ:P Team 2021-2024, GPL-2.0-or-later.
local V = {}

V.max_planks=6
V.repair_delay=0.75 -- window.qc window_touch
V.repair_points=10 -- window.qc Window_repaired
V.attack_damage=50 -- zombie_core.qc zombie_attack2
V.attack_through_damage=60 -- zombie_core.qc ZOMBIE_DAMAGE_THROUGH_WINDOW
V.attack_range_quake=64 -- zombie_core.qc zombie_attack2
V.attack_trigger_range_quake=60 -- ai_core.qc Inside_Walk
V.attack_retarget_delay=5 -- ai_core.qc Inside_Walk
V.attack_min_cooldown=1 -- ai_core.qc Inside_Walk
V.attack_random_cooldown=1 -- ai_core.qc Inside_Walk
V.window_frames={ [6]=0,[5]=6,[4]=13,[3]=20,[2]=27,[1]=34,[0]=41 }
V.damage={headshot=100,melee=130,uppertorso=60,lowertorso=50,
 grenade=50,flamethrower=50,tesla=50,explosive=60,flopper=50}
V.standard_hit_score=10 -- damage.qc

function V.barricade_frame(planks)
 assert(type(planks)=="number" and planks>=0 and planks<=6 and planks%1==0)
 return V.window_frames[planks]
end

function V.damage_score(lethal,style)
 -- damage.qc: nonlethal regular hits 10, final blow 50/60/100/130
 if lethal then return V.damage[style] or 50 end
 return V.standard_hit_score
end

function V.repair_cap(round)
 -- rounds.qc NewRound; 50*round per player, 500 max.
 return math.min(50*math.max(1,round),500)
end

function V.repair(state, now, current_round, granted_so_far, speedcola)
 -- window.qc Window_repaired + window_touch; repair exactly one board.
 -- The speedcola flag changes animation frames; it does NOT change .75 timer.
 if now < (state.next_repair or 0) or state.planks>=state.max then
  return false,0
 end
 state.planks=state.planks+1
 state.next_repair=now+V.repair_delay
 local reward=0
 if granted_so_far < V.repair_cap(current_round) then reward=V.repair_points end
 return true,reward
end

function V.damage_barrier(state)
 -- window.qc Window_Damage; never remove all planks in one strike.
 if state.planks<=0 then return false end
 state.planks=state.planks-1
 return true
end

function V.zombie_hp(round)
 -- zombie_core.qc set_z_health: raw NZ:P round HP, game modifier defaults.
 if round<=10 then return 50+round*100 end
 return 1040 * (1.1^(round-10))
end

local function qc_round(x)
 -- QuakeC rint() rounds halves away from zero for positive values.
 return math.floor(x+0.5)
end

function V.round_quota(round, player_count, difficulty)
 -- rounds.qc getZombieTotal, normal zombie waves, default gamemode.
 local players=math.max(1,player_count)
 local multiplier=math.max(round/5,1)
 if round>=10 then multiplier=multiplier*round*0.15 end
 local count=24
 if players==1 then
  count=count+qc_round(3*multiplier)
 else
  count=count+qc_round((players-1)*6*multiplier)
 end
 if round<2 then count=math.floor(count*0.25)
 elseif round<3 then count=math.floor(count*0.30)
 elseif round<4 then count=math.floor(count*0.50)
 elseif round<5 then count=math.floor(count*0.70)
 elseif round<6 then count=math.floor(count*0.90) end
 if difficulty==1 then count=math.floor(count*0.9)
 elseif difficulty==2 or difficulty==3 then count=math.floor(count*1.25) end
 return count
end

function V.next_spawn_delay(previous, reduction_multiplier)
 -- rounds.qc NewRound: spawn delay starts at 2s in round1, then
 -- decreases 5% per round, minimum 0.08 s.
 if previous>0.08 then
  return math.max(0.08, previous*math.max(0,math.min(1,1-0.05*(reduction_multiplier or 1))))
 end
 return 0.08
end

return V
