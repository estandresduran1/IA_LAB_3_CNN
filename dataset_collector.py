import cv2
import os
import time

# Configuración del dataset
BASE_DIR = 'dataset'
SPLITS = ['train', 'val', 'test']
CLASSES = ['0', '1', '2', '3', '4']

# Crear estructura de carpetas
for split in SPLITS:
    for cls in CLASSES:
        os.makedirs(os.path.join(BASE_DIR, split, cls), exist_ok=True)

# Parámetros de la cámara y de la región de interés (ROI)
cap = cv2.VideoCapture(0)
ROI_TOP, ROI_BOTTOM, ROI_RIGHT, ROI_LEFT = 100, 400, 300, 600

# Variables de estado
current_split = 'train'
person_id = 'P1' # Puedes cambiarlo a P2, P3 para diferentes integrantes del grupo

print("=== RECOLECTOR DE DATASET ===")
print("Instrucciones:")
print("- Pon tu mano dentro del cuadro verde.")
print("- Presiona '0', '1', '2', '3', o '4' para guardar una imagen de esa clase.")
print("- Presiona 't' para cambiar a Train (Entrenamiento)")
print("- Presiona 'v' para cambiar a Val (Validación)")
print("- Presiona 'e' para cambiar a Test (Prueba)")
print("- Presiona 'q' para salir.")
print(f"Actualmente guardando en: {current_split} | Persona: {person_id}")

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo acceder a la cámara.")
        break
    
    # Espejar la imagen para que sea más natural
    frame = cv2.flip(frame, 1)
    
    # Extraer la región de interés (ROI)
    roi = frame[ROI_TOP:ROI_BOTTOM, ROI_RIGHT:ROI_LEFT]
    
    # Dibujar el rectángulo verde en el frame original
    cv2.rectangle(frame, (ROI_RIGHT, ROI_TOP), (ROI_LEFT, ROI_BOTTOM), (0, 255, 0), 2)
    
    # Mostrar texto informativo en pantalla
    cv2.putText(frame, f"Modo: {current_split.upper()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "Presiona 0-4 para guardar, q para salir", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    cv2.imshow('Cámara - Dataset Collector', frame)
    # También puedes mostrar solo el recorte para ver qué guardará exactamente
    cv2.imshow('Recorte (ROI)', roi)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('t'):
        current_split = 'train'
        print("Cambiado a TRAIN")
    elif key == ord('v'):
        current_split = 'val'
        print("Cambiado a VAL")
    elif key == ord('e'):
        current_split = 'test'
        print("Cambiado a TEST")
    elif chr(key) in CLASSES:
        cls = chr(key)
        # Generar nombre de archivo único con timestamp
        filename = f"{cls}_{person_id}_{int(time.time()*1000)}.jpg"
        filepath = os.path.join(BASE_DIR, current_split, cls, filename)
        
        # Guardar solo la región de interés (ROI)
        cv2.imwrite(filepath, roi)
        print(f"Guardado: {filepath}")

cap.release()
cv2.destroyAllWindows()
