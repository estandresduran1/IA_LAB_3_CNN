import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from cnn_model import build_model

# Configuracion
DATASET_DIR = 'dataset'
MODEL_DIR = 'models'
BATCH_SIZE = 16
EPOCHS = 20
LR_BACKBONE = 0.0001   # Tasa de aprendizaje baja para el backbone pre-entrenado
LR_CLASSIFIER = 0.001  # Tasa mas alta para el clasificador nuevo
IMG_SIZE = 224  # MobileNetV2 fue entrenado con 224x224

os.makedirs(MODEL_DIR, exist_ok=True)

# Transformaciones (Data Augmentation para train, limpio para val/test)
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.RandomGrayscale(p=0.05),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_test_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Cargar Datasets
print("Cargando datasets...")
train_dataset = datasets.ImageFolder(os.path.join(DATASET_DIR, 'train'), transform=train_transform)
val_dataset   = datasets.ImageFolder(os.path.join(DATASET_DIR, 'val'),   transform=val_test_transform)
test_dataset  = datasets.ImageFolder(os.path.join(DATASET_DIR, 'test'),  transform=val_test_transform)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
test_loader  = DataLoader(test_dataset,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

print(f"Clases: {train_dataset.classes}")
print(f"Train: {len(train_dataset)} | Val: {len(val_dataset)} | Test: {len(test_dataset)}")

# Modelo MobileNetV2 con Transfer Learning
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Entrenando en: {device}")

model = build_model(num_classes=5, freeze_backbone=False).to(device)

# Optimizador diferenciado: backbone con LR pequeño, clasificador con LR grande
optimizer = optim.Adam([
    {'params': model.features.parameters(), 'lr': LR_BACKBONE},
    {'params': model.classifier.parameters(), 'lr': LR_CLASSIFIER}
])

# Scheduler: reduce LR cuando val_loss no mejora
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3, factor=0.5)
criterion = nn.CrossEntropyLoss()

train_losses, val_losses, val_accs = [], [], []
best_val_loss = float('inf')

print("\n--- INICIANDO ENTRENAMIENTO ---")
for epoch in range(EPOCHS):
    # Entrenamiento
    model.train()
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * images.size(0)

    epoch_train_loss = running_loss / len(train_dataset)
    train_losses.append(epoch_train_loss)

    # Validacion
    model.eval()
    val_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            val_loss += criterion(outputs, labels).item() * images.size(0)
            _, pred = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (pred == labels).sum().item()

    epoch_val_loss = val_loss / len(val_dataset)
    epoch_val_acc  = 100 * correct / total
    val_losses.append(epoch_val_loss)
    val_accs.append(epoch_val_acc)
    scheduler.step(epoch_val_loss)

    marker = ""
    if epoch_val_loss < best_val_loss:
        best_val_loss = epoch_val_loss
        torch.save(model.state_dict(), os.path.join(MODEL_DIR, 'best_model.pth'))
        marker = " --> MEJOR MODELO GUARDADO"

    print(f"Epoch [{epoch+1:2d}/{EPOCHS}] | Train Loss: {epoch_train_loss:.4f} | Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc:.1f}%{marker}")

# Evaluacion final en Test
print("\n--- EVALUACION EN TEST ---")
model.load_state_dict(torch.load(os.path.join(MODEL_DIR, 'best_model.pth'), map_location=device))
model.eval()

y_true, y_pred = [], []
with torch.no_grad():
    for images, labels in test_loader:
        outputs = model(images.to(device))
        _, pred = torch.max(outputs, 1)
        y_true.extend(labels.numpy())
        y_pred.extend(pred.cpu().numpy())

print(classification_report(y_true, y_pred, target_names=train_dataset.classes))

# Guardar graficas en la carpeta models/
# Matriz de confusion
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=train_dataset.classes,
            yticklabels=train_dataset.classes)
plt.xlabel('Prediccion')
plt.ylabel('Real')
plt.title('Matriz de Confusion')
plt.tight_layout()
plt.savefig(os.path.join(MODEL_DIR, 'matriz_confusion.png'))
plt.close()
print("Matriz de confusion guardada en models/")

# Curvas de aprendizaje
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(train_losses, label='Train Loss')
ax1.plot(val_losses, label='Val Loss')
ax1.set_title('Curvas de Perdida')
ax1.set_xlabel('Epoca')
ax1.legend()

ax2.plot(val_accs, label='Val Accuracy', color='green')
ax2.set_title('Exactitud en Validacion')
ax2.set_xlabel('Epoca')
ax2.set_ylabel('%')
ax2.legend()

plt.tight_layout()
plt.savefig(os.path.join(MODEL_DIR, 'curva_aprendizaje.png'))
plt.close()
print("Curvas de aprendizaje guardadas en models/")
print("\nEntrenamiento completado!")
