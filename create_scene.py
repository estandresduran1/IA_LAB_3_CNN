"""
Recrea la escena e inyecta un script Lua en el robot que
lee senales de Python para mover los joints.
"""
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import time

LUA_SCRIPT = """
-- Script de control del brazo
-- Lee senales enviadas desde Python y mueve los joints

function sysCall_init()
    j1 = sim.getObject('/Joint1')
    j2 = sim.getObject('/Joint2')
    j3 = sim.getObject('/Joint3')
    fl = sim.getObject('/FingerL')
    fr = sim.getObject('/FingerR')
    
    step = 0.3  -- radianes por comando
    pos = {0.0, 0.0, 0.0}
    gripper_closed = false
    lims = {{-1.5,1.5},{-1.2,1.2},{-1.5,1.5}}
    last_cmd = -1
end

function clamp(v, lo, hi)
    return math.max(lo, math.min(hi, v))
end

function sysCall_actuation()
    local cmd = sim.getIntegerSignal('gesture_cmd')
    if cmd == nil or cmd == last_cmd then return end
    last_cmd = cmd
    sim.clearIntegerSignal('gesture_cmd')
    
    if cmd == 0 then
        -- PARADA: no hace nada
        
    elseif cmd == 1 then
        pos[1] = clamp(pos[1] + step, lims[1][1], lims[1][2])
        sim.setJointPosition(j1, pos[1])
        
    elseif cmd == 2 then
        pos[2] = clamp(pos[2] + step, lims[2][1], lims[2][2])
        sim.setJointPosition(j2, pos[2])
        
    elseif cmd == 3 then
        pos[3] = clamp(pos[3] + step, lims[3][1], lims[3][2])
        sim.setJointPosition(j3, pos[3])
        
    elseif cmd == 4 then
        gripper_closed = not gripper_closed
        local gb = sim.getObject('/GripperBody')
        local offset = gripper_closed and 0.010 or 0.028
        sim.setObjectPosition(fl, gb, {0.025, offset, 0.0})
        sim.setObjectPosition(fr, gb, {0.025, -offset, 0.0})
        sim.setObjectOrientation(fl, gb, {0.0, 0.0, 0.0})
        sim.setObjectOrientation(fr, gb, {0.0, 0.0, 0.0})
        
    elseif cmd == 99 then
        -- HOME
        pos = {0.0, 0.0, 0.0}
        sim.setJointPosition(j1, 0.0)
        sim.setJointPosition(j2, 0.0)
        sim.setJointPosition(j3, 0.0)
        gripper_closed = false
    end
end
"""

def create_scene():
    print("Conectando a CoppeliaSim...")
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    print(f"Conectado! Version: {sim.getInt32Param(sim.intparam_program_version)}")

    sim.stopSimulation()
    time.sleep(1.5)

    # Limpiar objetos anteriores de la escena
    try:
        for nm in ['/Joint1','/Joint2','/Joint3','/ArmBase','/Table',
                   '/ObjetoRojo','/ObjetoVerde','/ObjetoAzul','/ZonaDeposito']:
            h = sim.getObject(nm)
            sim.removeObject(h)
    except Exception:
        pass
    time.sleep(0.5)

    def nm(handle, n):
        try:
            sim.setObjectAlias(handle, n)
        except Exception:
            sim.setObjectName(handle, n)

    def col(handle, rgb):
        sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, rgb)

    print("Creando mesa...")
    table = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.8, 0.8, 0.04], 1)
    sim.setObjectPosition(table, -1, [0.0, 0.0, 0.40])
    nm(table, 'Table')
    col(table, [0.55, 0.37, 0.18])
    for dx, dy in [(-0.36,-0.36),(0.36,-0.36),(-0.36,0.36),(0.36,0.36)]:
        leg = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.04, 0.04, 0.40], 1)
        sim.setObjectPosition(leg, -1, [dx, dy, 0.20])
        col(leg, [0.40, 0.26, 0.12])

    print("Creando brazo...")
    base = sim.createPrimitiveShape(sim.primitiveshape_cylinder, [0.07, 0.07, 0.05], 1)
    sim.setObjectPosition(base, -1, [0.0, 0.0, 0.445])
    nm(base, 'ArmBase')
    col(base, [0.2, 0.2, 0.8])

    j1 = sim.createJoint(sim.joint_revolute_subtype, sim.jointmode_kinematic, 0)
    sim.setObjectPosition(j1, -1, [0.0, 0.0, 0.475])
    nm(j1, 'Joint1')
    sim.setJointInterval(j1, True, [-3.14159, 6.28318])
    sim.setObjectParent(j1, base, True)

    link1 = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.04, 0.04, 0.20], 1)
    sim.setObjectPosition(link1, -1, [0.0, 0.0, 0.575])
    nm(link1, 'Link1'); col(link1, [0.3, 0.3, 0.9])
    sim.setObjectParent(link1, j1, True)

    j2 = sim.createJoint(sim.joint_revolute_subtype, sim.jointmode_kinematic, 0)
    sim.setObjectPosition(j2, -1, [0.0, 0.0, 0.675])
    sim.setObjectOrientation(j2, -1, [0.0, 1.5708, 0.0])
    nm(j2, 'Joint2')
    sim.setJointInterval(j2, True, [-3.14159, 6.28318])
    sim.setObjectParent(j2, link1, True)

    link2 = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.04, 0.04, 0.18], 1)
    sim.setObjectPosition(link2, -1, [0.09, 0.0, 0.675])
    nm(link2, 'Link2'); col(link2, [0.1, 0.6, 0.9])
    sim.setObjectParent(link2, j2, True)

    j3 = sim.createJoint(sim.joint_revolute_subtype, sim.jointmode_kinematic, 0)
    sim.setObjectPosition(j3, -1, [0.18, 0.0, 0.675])
    sim.setObjectOrientation(j3, -1, [0.0, 1.5708, 0.0])
    nm(j3, 'Joint3')
    sim.setJointInterval(j3, True, [-3.14159, 6.28318])
    sim.setObjectParent(j3, link2, True)

    link3 = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.04, 0.04, 0.15], 1)
    sim.setObjectPosition(link3, -1, [0.255, 0.0, 0.675])
    nm(link3, 'Link3'); col(link3, [0.1, 0.8, 0.8])
    sim.setObjectParent(link3, j3, True)

    gbody = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.04, 0.05, 0.04], 1)
    sim.setObjectPosition(gbody, -1, [0.33, 0.0, 0.675])
    nm(gbody, 'GripperBody'); col(gbody, [0.9, 0.6, 0.1])
    sim.setObjectParent(gbody, link3, True)

    fl = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.012, 0.04, 0.04], 1)
    sim.setObjectPosition(fl, -1, [0.35, 0.028, 0.675])
    nm(fl, 'FingerL'); col(fl, [1.0, 0.8, 0.0])
    sim.setObjectParent(fl, gbody, True)

    fr = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.012, 0.04, 0.04], 1)
    sim.setObjectPosition(fr, -1, [0.35, -0.028, 0.675])
    nm(fr, 'FingerR'); col(fr, [1.0, 0.8, 0.0])
    sim.setObjectParent(fr, gbody, True)

    print("Creando objetos y zona...")
    for name_obj, pos, clr in [
        ('ObjetoRojo',  [-0.20,  0.12, 0.445], [0.9, 0.1, 0.1]),
        ('ObjetoVerde', [-0.20, -0.12, 0.445], [0.1, 0.8, 0.1]),
        ('ObjetoAzul',  [-0.10,  0.22, 0.445], [0.1, 0.2, 0.9]),
    ]:
        h = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.04, 0.04, 0.04], 1)
        sim.setObjectPosition(h, -1, pos)
        nm(h, name_obj); col(h, clr)

    dep = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [0.15, 0.15, 0.005], 1)
    sim.setObjectPosition(dep, -1, [0.20, 0.0, 0.425])
    nm(dep, 'ZonaDeposito'); col(dep, [1.0, 1.0, 0.0])

    # INYECTAR SCRIPT LUA en la base del brazo
    print("Instalando script Lua de control...")
    try:
        script_handle = sim.addScript(sim.scripttype_childscript)
        sim.associateScriptWithObject(script_handle, base)
        sim.setScriptStringParam(script_handle, sim.scriptstringparam_text, LUA_SCRIPT)
        print("Script Lua instalado correctamente via associateScriptWithObject")
    except Exception as e:
        print(f"No se pudo instalar el script automaticamente: {e}")
        print("=> Sigue el paso manual (ver instrucciones abajo)")

    print("\n=== ESCENA LISTA ===")
    print("Si el script Lua NO se instalo automaticamente, hazlo manualmente:")
    print("  1. En CoppeliaSim, click derecho en 'ArmBase' en la jerarquia")
    print("  2. Add > Associated child script > Non-threaded child script")
    print("  3. Pega el contenido de robot_script.lua en el editor que se abre")
    print("  4. Guarda con Ctrl+S")
    print("\nLuego presiona PLAY en CoppeliaSim y corre: python main.py")


if __name__ == '__main__':
    create_scene()
