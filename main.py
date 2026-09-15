"""
Script principal: CNN en vivo + control del robot en CoppeliaSim.
Une cnn_inference + command_filter + robot_adapter.

ORDEN DE EJECUCION:
1. Abre CoppeliaSim y carga tu escena (o corre create_scene.py primero)
2. Presiona PLAY (triangulo) en CoppeliaSim para iniciar la simulacion
3. Corre este script: python main.py
"""

import cv2
import torch
import yaml
import time
from torchvision import transforms
from PIL import Image

from cnn_model import build_model
from command_filter import CommandFilter
from robot_adapter import RobotAdapter

# ============ CONFIGURACION ============
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

CONF_THRESH = config['inference']['confidence_threshold']
CLASSES = ['0', '1', '2', '3', '4']
CLASS_NAMES = {
    '0': 'PARADA',
    '1': 'Rotar Base',
    '2': 'Hombro',
    '3': 'Codo',
    '4': 'Pinza ON/OFF'
}

# ============ CARGAR MODELO ============
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = build_model(num_classes=5).to(device)
model.load_state_dict(torch.load('models/best_model.pth', map_location=device))
model.eval()
print(f"Modelo cargado en {device}")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ============ FILTRO Y ROBOT ============
cmd_filter = CommandFilter(
    window_size=config['filter']['window_size'],
    consistency_threshold=config['filter']['consistency_threshold'],
    cooldown_seconds=config['filter']['cooldown_seconds']
)

robot = RobotAdapter()

# ============ CAMARA ============
cap = cv2.VideoCapture(0)
ROI_TOP, ROI_BOTTOM, ROI_LEFT, ROI_RIGHT = 50, 430, 250, 650

last_accepted = 'Ninguno'
status_msg = 'Esperando gesto estable...'
latencies = []  # Para calcular p50/p95 al final

print("\n=== SISTEMA ACTIVO ===")
print("Pon tu mano en el cuadro verde.")
print("Presiona 'h' para volver al HOME | 'q' para salir")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    roi = frame[ROI_TOP:ROI_BOTTOM, ROI_LEFT:ROI_RIGHT]
    cv2.rectangle(frame, (ROI_LEFT, ROI_TOP), (ROI_RIGHT, ROI_BOTTOM), (0, 255, 0), 2)
    cv2.putText(frame, "Pon tu mano aqui", (ROI_LEFT+5, ROI_TOP-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    # ---- INFERENCIA ----
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    tensor  = transform(Image.fromarray(roi_rgb)).unsqueeze(0).to(device)

    t0 = time.time()
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0]
        conf, idx = torch.max(probs, 0)
    lat = (time.time() - t0) * 1000
    latencies.append(lat)

    pred_cls = CLASSES[idx.item()]
    conf_val = conf.item()

    # ---- FILTRO ----
    accepted, fstatus = cmd_filter.process(pred_cls, conf_val, CONF_THRESH)
    if accepted is not None:
        last_accepted = accepted
        status_msg = f">> {CLASS_NAMES.get(accepted, accepted)} <<"
        print(f"\n[COMANDO DETECTADO] Gesto {accepted} ({CLASS_NAMES.get(accepted, '')}) -> Moviendo robot en CoppeliaSim!")
        robot.move(accepted)
    elif fstatus != "En Cooldown":
        status_msg = fstatus

    # ---- INTERFAZ ----
    # Panel izquierdo (info de percepcion)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (250, 200), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    cv2.putText(frame, f"Pred: {pred_cls}  Conf: {conf_val*100:.0f}%",
                (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255,255,0), 2)
    cv2.putText(frame, f"Lat: {lat:.1f} ms",
                (8, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,180,255), 1)
    cv2.putText(frame, f"Ultimo: {last_accepted} ({CLASS_NAMES.get(last_accepted,'')})",
                (8, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,0), 2)
    cv2.putText(frame, status_msg,
                (8, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,220,220), 2)

    # Barras de probabilidad
    for i, p in enumerate(probs.cpu().numpy()):
        y = 135 + i * 20
        bw = int(p * 220)
        color = (0, 200, 100) if str(i) == pred_cls else (80, 80, 80)
        cv2.rectangle(frame, (8, y), (8+bw, y+14), color, -1)
        cv2.putText(frame, f"{i}:{p*100:.0f}%", (235, y+12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255,255,255), 1)

    # Estado del robot (esquina inferior)
    r = robot
    robot_info = f"J1:{r.pos[0]:.1f} J2:{r.pos[1]:.1f} J3:{r.pos[2]:.1f} Pinza:{'CERRADA' if r.gripper_closed else 'ABIERTA'}"
    cv2.putText(frame, robot_info,
                (8, frame.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,200,100), 1)

    cv2.imshow('CNN + CoppeliaSim Control', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('h'):
        robot.home()
        last_accepted = 'HOME'
        status_msg = 'Volviendo a HOME...'

cap.release()
cv2.destroyAllWindows()

# Reporte de latencia al salir
if latencies:
    import numpy as np
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    print(f"\nEstadisticas de latencia ({len(latencies)} frames):")
    print(f"  Mediana (p50): {p50:.1f} ms")
    print(f"  Percentil 95 (p95): {p95:.1f} ms")
