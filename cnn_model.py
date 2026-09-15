import torch
import torch.nn as nn
from torchvision import models

def build_model(num_classes=5, freeze_backbone=False):
    """
    Usa MobileNetV2 pre-entrenado en ImageNet como base.
    Solo reemplazamos el clasificador final para nuestras 5 clases.
    Esto se llama Transfer Learning y funciona MUY bien con datasets pequenos.
    """
    # Cargar MobileNetV2 pre-entrenado
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    
    # Opcionalmente congelar el backbone (solo entrenar el clasificador)
    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False
    
    # Reemplazar el clasificador final:
    # MobileNetV2 termina con (1280,) features -> nosotros queremos 5 clases
    in_features = model.classifier[1].in_features  # 1280
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, num_classes)
    )
    
    return model

# Para probar si las dimensiones cuadran:
if __name__ == '__main__':
    model = build_model()
    dummy_input = torch.randn(1, 3, 128, 128)
    output = model(dummy_input)
    print(f'Salida de prueba: {output.shape}')  # Debe ser [1, 5]
    
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f'Total de parametros entrenables: {total_params:,}')

