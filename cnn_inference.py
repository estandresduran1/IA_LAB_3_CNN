import cv2
import torch
import yaml
import time
from torchvision import transforms
from PIL import Image
from cnn_model import build_model
from command_filter import CommandFilter

# 1. Cargar configuracion
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

CONF_THRESH = config['inference']['confidence_threshold']

# Inicializar Filtro
cmd_filter = CommandFilter(
    window_size=config['filter']['window_size'],
    consistency_threshold=config['filter']['consistency_threshold'],
    cooldown_seconds=config['filter']['cooldown_seconds']
)

# 2. Cargar modelo MobileNetV2
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = build_model(num_classes=5).to(device)
model.load_state_dict(torch.load('models/best_model.pth', map_location=device))
model.eval()

# Transformaciones para inferencia (mismas que val/test)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

CLASSES = ['0', '1', '2', '3', '4']

# 3. Inicializar Camara
cap = cv2.VideoCapture(0)
ROI_TOP, ROI_BOTTOM, ROI_RIGHT, ROI_LEFT = 100, 400, 300, 600

print("=== INFERENCIA EN TIEMPO REAL ===")
print("Presiona 'q' para salir.")

last_accepted = "Ninguno"
status_msg = "Iniciando..."

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    roi = frame[ROI_TOP:ROI_BOTTOM, ROI_RIGHT:ROI_LEFT]
    cv2.rectangle(frame, (ROI_RIGHT, ROI_TOP), (ROI_LEFT, ROI_BOTTOM), (0, 255, 0), 2)

    # 4. Preprocesar ROI
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(roi_rgb)
    input_tensor = transform(pil_img).unsqueeze(0).to(device)

    # 5. Inferencia con medicion de latencia
    t_start = time.time()
    with torch.no_grad():
        output = model(input_tensor)
        probabilities = torch.nn.functional.softmax(output, dim=1)[0]
        confidence, predicted_idx = torch.max(probabilities, 0)
    latency_ms = (time.time() - t_start) * 1000

    pred_class = CLASSES[predicted_idx.item()]
    conf_val = confidence.item()

    # 6. Filtrado Temporal
    accepted_cmd, filter_status = cmd_filter.process(pred_class, conf_val, CONF_THRESH)
    if accepted_cmd is not None:
        last_accepted = accepted_cmd
        status_msg = f"EJECUTANDO: {last_accepted}"
        # Aqui se llamaria: robot.move(last_accepted)
    elif filter_status != "En Cooldown":
        status_msg = filter_status

    # 7. Interfaz en pantalla
    cv2.putText(frame, f"Crudo: Clase {pred_class} (Conf: {conf_val*100:.1f}%)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, f"Latencia: {latency_ms:.1f} ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 100), 2)
    cv2.putText(frame, f"Comando Aceptado: {last_accepted}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.putText(frame, f"Estado Filtro: {status_msg}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Barra de probabilidades por clase
    for i, p in enumerate(probabilities):
        bar_w = int(p.item() * 150)
        cv2.rectangle(frame, (10, 150 + i*22), (10 + bar_w, 168 + i*22), (0, 200, 100), -1)
        cv2.putText(frame, f"{i}: {p.item()*100:.1f}%", (165, 165 + i*22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    cv2.imshow('CNN Inference & Control', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
