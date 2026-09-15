-- Script de control del brazo - pegar en CoppeliaSim (ArmBase > child script)
-- Lee senales enteras enviadas desde Python y mueve los joints

function sysCall_init()
    j1 = sim.getObject('/Joint1')
    j2 = sim.getObject('/Joint2')
    j3 = sim.getObject('/Joint3')
    fl = sim.getObject('/FingerL')
    fr = sim.getObject('/FingerR')
    
    step = 0.3
    pos = {0.0, 0.0, 0.0}
    gripper_closed = false
    lims = {{-1.5,1.5},{-1.2,1.2},{-1.5,1.5}}
end

function clamp(v, lo, hi)
    return math.max(lo, math.min(hi, v))
end

function sysCall_actuation()
    local cmd = sim.getIntegerSignal('gesture_cmd')
    if cmd == nil then return end
    sim.clearIntegerSignal('gesture_cmd')
    
    print('Comando recibido: ' .. cmd)
    
    if cmd == 1 then
        pos[1] = clamp(pos[1] + step, lims[1][1], lims[1][2])
        sim.setJointPosition(j1, pos[1])
        print('Joint1 -> ' .. pos[1])
        
    elseif cmd == 2 then
        pos[2] = clamp(pos[2] + step, lims[2][1], lims[2][2])
        sim.setJointPosition(j2, pos[2])
        print('Joint2 -> ' .. pos[2])
        
    elseif cmd == 3 then
        pos[3] = clamp(pos[3] + step, lims[3][1], lims[3][2])
        sim.setJointPosition(j3, pos[3])
        print('Joint3 -> ' .. pos[3])
        
    elseif cmd == 4 then
        gripper_closed = not gripper_closed
        local gb = sim.getObject('/GripperBody')
        local offset = gripper_closed and 0.010 or 0.028
        sim.setObjectPosition(fl, gb, {0.025, offset, 0.0})
        sim.setObjectPosition(fr, gb, {0.025, -offset, 0.0})
        sim.setObjectOrientation(fl, gb, {0.0, 0.0, 0.0})
        sim.setObjectOrientation(fr, gb, {0.0, 0.0, 0.0})
        
    elseif cmd == 99 then
        pos = {0.0, 0.0, 0.0}
        sim.setJointPosition(j1, 0.0)
        sim.setJointPosition(j2, 0.0)
        sim.setJointPosition(j3, 0.0)
        gripper_closed = false
        print('HOME')
    end
end
