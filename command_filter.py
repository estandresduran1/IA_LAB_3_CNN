import time
import collections

class CommandFilter:
    def __init__(self, window_size=8, consistency_threshold=5, cooldown_seconds=1.2):
        self.window_size = window_size
        self.consistency_threshold = consistency_threshold
        self.cooldown_seconds = cooldown_seconds
        
        self.history = collections.deque(maxlen=window_size)
        self.last_command_time = 0
        self.last_accepted_command = None
        
    def process(self, prediction, confidence, threshold):
        # 1. Si la confianza es menor al umbral, se considera 'NONE' (no reconocido)
        if confidence < threshold:
            current_pred = "NONE"
        else:
            current_pred = str(prediction)
            
        self.history.append(current_pred)
        
        # 2. Respetar el Cooldown
        current_time = time.time()
        if current_time - self.last_command_time < self.cooldown_seconds:
            return None, "En Cooldown"
            
        # 3. Evaluar consistencia en la ventana
        if len(self.history) >= self.consistency_threshold:
            counter = collections.Counter(self.history)
            most_common_class, count = counter.most_common(1)[0]
            
            # Solo aceptar si NO es NONE y supera el umbral de consistencia
            if most_common_class != "NONE" and count >= self.consistency_threshold:
                self.last_accepted_command = most_common_class
                self.last_command_time = current_time
                self.history.clear()
                return most_common_class, f"ACEPTADO: {most_common_class}"
        
        return None, "Detectando..."
