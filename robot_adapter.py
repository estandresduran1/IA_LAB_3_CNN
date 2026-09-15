"""
Adaptador de control para el brazo robotico de 3 GDL + Pinza en CoppeliaSim.
Usa la API directa de CoppeliaSim (setJointPosition) con soporte de auto-inicio de simulacion.
"""
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

class RobotAdapter:
    STEP = 0.35  # Paso de rotacion en radianes (~20 grados)
    
    # Limites articulares (min, max) en radianes
    LIMITS = [
        (-1.4, 1.4),  # Joint1 (Base)
        (-0.8, 0.8),  # Joint2 (Hombro)
        (-1.2, 1.2),  # Joint3 (Codo)
    ]

    def __init__(self):
        self.client = RemoteAPIClient()
        self.sim = self.client.getObject('sim')
        
        # Auto-iniciar simulacion si esta en Stop
        state = self.sim.getSimulationState()
        if state == 0:
            print("[RobotAdapter] Simulacion en Stop -> Iniciando automaticamente...")
            self.sim.startSimulation()
            time.sleep(0.5)

        # Obtener handles de articulaciones y pinza
        self.j1 = self.sim.getObject('/Joint1')
        self.j2 = self.sim.getObject('/Joint2')
        self.j3 = self.sim.getObject('/Joint3')
        
        # Desbloquear limites de rotacion en CoppeliaSim (por si quedaron restringidos)
        for j in [self.j1, self.j2, self.j3]:
            try:
                self.sim.setJointInterval(j, True, [-3.14159, 6.28318])
            except Exception:
                pass
        
        try:
            self.gripper_body = self.sim.getObject('/GripperBody')
            self.finger_l = self.sim.getObject('/FingerL')
            self.finger_r = self.sim.getObject('/FingerR')
            # Asegurar posicion inicial correcta de los dedos relativa a la pinza
            self.sim.setObjectPosition(self.finger_l, self.gripper_body, [0.025, 0.028, 0.0])
            self.sim.setObjectPosition(self.finger_r, self.gripper_body, [0.025, -0.028, 0.0])
            self.sim.setObjectOrientation(self.finger_l, self.gripper_body, [0.0, 0.0, 0.0])
            self.sim.setObjectOrientation(self.finger_r, self.gripper_body, [0.0, 0.0, 0.0])
        except Exception:
            self.gripper_body = None
            self.finger_l = None
            self.finger_r = None

        # Posiciones internas actuales
        self.pos = [0.0, 0.0, 0.0]
        self.dirs = [1, 1, 1]  # Direccion de avance (+1 o -1 al llegar a limites)
        self.gripper_closed = False
        self.busy = False
        
        print(f"[RobotAdapter] Conectado exitosamente. Handles: J1={self.j1}, J2={self.j2}, J3={self.j3}")

    def _step_joint(self, joint_idx, handle):
        """Avanza una articulacion y rebota si llega al limite."""
        lo, hi = self.LIMITS[joint_idx]
        new_val = self.pos[joint_idx] + (self.dirs[joint_idx] * self.STEP)
        
        # Invertir direccion si se sobrepasan los limites
        if new_val > hi:
            new_val = hi
            self.dirs[joint_idx] = -1
        elif new_val < lo:
            new_val = lo
            self.dirs[joint_idx] = 1
            
        self.pos[joint_idx] = new_val
        self.sim.setJointPosition(handle, new_val)
        return new_val

    def move(self, command: str):
        """
        Ejecuta el comando traducido del gesto de la mano:
          '0': Parada logica (mantener posicion)
          '1': Rotar base (Joint1)
          '2': Mover hombro (Joint2)
          '3': Mover codo (Joint3)
          '4': Toggle pinza (abrir / cerrar)
        """
        if self.busy:
            return

        self.busy = True
        cmd = str(command).strip()

        try:
            # Asegurar que la simulacion este corriendo
            if self.sim.getSimulationState() == 0:
                self.sim.startSimulation()
                time.sleep(0.3)

            if cmd == '0':
                print("[Robot] >> GESTO 0: PARADA LOGICA (Robot quieto)")

            elif cmd == '1':
                pos = self._step_joint(0, self.j1)
                print(f"[Robot] >> GESTO 1: Base (Joint1) rotando a {pos:.2f} rad")

            elif cmd == '2':
                pos = self._step_joint(1, self.j2)
                print(f"[Robot] >> GESTO 2: Hombro (Joint2) moviendo a {pos:.2f} rad")

            elif cmd == '3':
                pos = self._step_joint(2, self.j3)
                print(f"[Robot] >> GESTO 3: Codo (Joint3) extendiendo a {pos:.2f} rad")

            elif cmd == '4':
                self.gripper_closed = not self.gripper_closed
                estado_str = "CERRADA" if self.gripper_closed else "ABIERTA"
                print(f"[Robot] >> GESTO 4: Pinza {estado_str}")
                self._toggle_gripper()

        except Exception as e:
            print(f"[Robot] Error al ejecutar comando {cmd}: {e}")
        finally:
            self.busy = False

    def _toggle_gripper(self):
        """Abre o cierra los dedos de la pinza relativo al marco local del GripperBody."""
        if self.finger_l and self.finger_r and self.gripper_body:
            try:
                offset = 0.010 if self.gripper_closed else 0.028
                self.sim.setObjectPosition(self.finger_l, self.gripper_body, [0.025, offset, 0.0])
                self.sim.setObjectPosition(self.finger_r, self.gripper_body, [0.025, -offset, 0.0])
                self.sim.setObjectOrientation(self.finger_l, self.gripper_body, [0.0, 0.0, 0.0])
                self.sim.setObjectOrientation(self.finger_r, self.gripper_body, [0.0, 0.0, 0.0])
            except Exception as e:
                print(f"[Robot] Error en pinza: {e}")

    def home(self):
        """Regresa el robot a posicion inicial de referencia."""
        print("[Robot] Regresando a posicion HOME (0, 0, 0)...")
        self.pos = [0.0, 0.0, 0.0]
        self.dirs = [1, 1, 1]
        self.sim.setJointPosition(self.j1, 0.0)
        self.sim.setJointPosition(self.j2, 0.0)
        self.sim.setJointPosition(self.j3, 0.0)
        self.gripper_closed = False
        self._toggle_gripper()
        print("[Robot] Robot en posicion HOME")


# Bloque de prueba ejecutable directamente
if __name__ == '__main__':
    print("=== INICIANDO PRUEBA DE ROBOT ADAPTER ===")
    robot = RobotAdapter()
    
    print("\n1. Probando comando '1' (Girar Base)...")
    for _ in range(3):
        robot.move('1')
        time.sleep(0.5)
        
    print("\n2. Probando comando '2' (Mover Hombro)...")
    for _ in range(2):
        robot.move('2')
        time.sleep(0.5)

    print("\n3. Probando comando '3' (Mover Codo)...")
    for _ in range(2):
        robot.move('3')
        time.sleep(0.5)

    print("\n4. Probando comando '4' (Pinza)...")
    robot.move('4')
    time.sleep(0.8)
    robot.move('4')
    time.sleep(0.8)

    print("\n5. Probando comando '0' (Parada)...")
    robot.move('0')
    time.sleep(0.5)

    print("\n6. Volviendo a HOME...")
    robot.home()
    print("\n=== PRUEBA DE MOVIMIENTO COMPLETADA CON EXITO ===")
