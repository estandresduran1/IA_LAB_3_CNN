"""
Prueba directa de movimiento en CoppeliaSim.
Corre este script con CoppeliaSim abierto y en PLAY para ver si el robot se mueve.
"""
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import time

client = RemoteAPIClient()
sim = client.getObject('sim')
print(f"Conectado. Estado simulacion: {sim.getSimulationState()}")

# Buscar los joints
try:
    j1 = sim.getObject('/Joint1')
    j2 = sim.getObject('/Joint2')
    j3 = sim.getObject('/Joint3')
    print(f"Joints encontrados: J1={j1}, J2={j2}, J3={j3}")
except Exception as e:
    print(f"ERROR buscando joints: {e}")
    print("Asegurate de haber corrido create_scene.py primero")
    exit()

# Ver posicion actual
print(f"Posicion actual J1: {sim.getJointPosition(j1):.3f} rad")
print(f"Posicion actual J2: {sim.getJointPosition(j2):.3f} rad")
print(f"Posicion actual J3: {sim.getJointPosition(j3):.3f} rad")

print("\nMoviendo Joint1 a 0.5 rad...")
sim.setJointPosition(j1, 0.5)
time.sleep(1.0)
print(f"Nueva posicion J1: {sim.getJointPosition(j1):.3f} rad")

print("Moviendo Joint1 a -0.5 rad...")
sim.setJointPosition(j1, -0.5)
time.sleep(1.0)

print("Moviendo Joint2 a 0.4 rad...")
sim.setJointPosition(j2, 0.4)
time.sleep(1.0)

print("Volviendo a cero...")
sim.setJointPosition(j1, 0.0)
sim.setJointPosition(j2, 0.0)
sim.setJointPosition(j3, 0.0)
time.sleep(0.5)

print("Prueba completada. Si el brazo se movio en CoppeliaSim, todo funciona bien.")
