# Laboratorio 3: CNN para Reconocimiento de Gestos

Este repositorio contiene todo el código necesario para cumplir con las Fases 1 a 4 del Laboratorio de Inteligencia Artificial (Reconocimiento de 0 a 4 dedos y control robótico).

## Estructura de Archivos

1. **`dataset_collector.py`**: Script con interfaz gráfica usando OpenCV para recolectar tus propias fotos de forma ágil y organizarlas en carpetas de `Train`, `Val` y `Test`.
2. **`cnn_model.py`**: Define la arquitectura de la Red Neuronal Convolucional (PyTorch). Usamos 4 bloques convolucionales para alcanzar la nota máxima (N5).
3. **`train.py`**: Carga el dataset, aplica *Data Augmentation*, entrena el modelo, y genera las gráficas de pérdida y la matriz de confusión.
4. **`config.yaml`**: Archivo para configurar fácilmente los umbrales de confianza y las ventanas de tiempo del filtro.
5. **`command_filter.py`**: Implementa la lógica para evitar que el robot reciba comandos erráticos. Solo aprueba comandos si son estables en el tiempo.
6. **`cnn_inference.py`**: El script principal que abre la cámara, pasa la imagen por la CNN entrenada, la filtra y te dice qué comando se enviaría al robot.
7. **`robot_adapter.py`**: Se conecta con **CoppeliaSim** mediante la API `zmqRemoteApi` para mover las articulaciones del robot dependiendo del comando estable detectado.

## Instrucciones de Uso

### Paso 1: Recolectar Datos
Ejecuta `python dataset_collector.py`.
Aparecerá tu cámara. Pon la mano en el cuadro verde y presiona las teclas del `0` al `4` para guardar fotos. Usa la `t`, `v`, `e` para cambiar entre Entrenamiento, Validación y Prueba. **Mínimo recomendado:** 300 fotos por clase en Train, 50 en Val, 50 en Test.

### Paso 2: Entrenar el Modelo
Ejecuta `python train.py`.
Este proceso puede tardar dependiendo de tu PC. Al finalizar, guardará tu mejor modelo en la carpeta `models/best_model.pth` y te generará dos imágenes (`matriz_confusion.png` y `curva_aprendizaje.png`) que **debes adjuntar en tu informe IEEE**.

### Paso 3: Probar en Vivo (Inferencia)
Ejecuta `python cnn_inference.py`.
Aquí podrás ver en tiempo real cómo la red predice los números que haces con la mano y cómo el filtro decide si manda o no el comando.

### Paso 4: Conectar al Simulador
1. Abre CoppeliaSim.
2. Carga tu escena con el brazo robótico (asegúrate de que los objetos se llamen `/Joint1`, `/Joint2`, etc., o cámbialos en el archivo `robot_adapter.py`).
3. Modifica la línea 81 de `cnn_inference.py` para llamar a `robot_adapter.py`.
