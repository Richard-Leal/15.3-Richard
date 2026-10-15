import cv2
import numpy as np

def detector_tiempo_real():
    # Inicializar webcam
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
    
    if not cap.isOpened():
        print("Error: No se pudo acceder a la cámara.")
        return

    # Substractor de fondo para detectar movimiento en cámara estática
    substractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    # Variables para cálculo de movimiento/velocidad
    prev_cx, prev_cy = None, None

    print("Presiona 'q' o 'ESC' para salir del detector.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        
        # 1. Convertir a escala de grises y desenfocar para reducir ruido
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)

        # 2. Umbralización para mesa clara y objetos oscuros (MDF)
        # Puedes ajustar 130 según tu iluminación habitual
        _, binaria = cv2.threshold(blur, 130, 255, cv2.THRESH_BINARY_INV)

        # 3. Limpieza de imagen (operaciones morfológicas)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, kernel)

        # 4. Encontrar contornos de objetos presentes
        cnts, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in cnts:
            area = cv2.contourArea(cnt)
            
            # Filtrar por área mínima para ignorar ruido pequeño
            if area > 1000:
                # Calcular el centroide geométrico del objeto (Momentos)
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx, cy = 0, 0

                # Bounding Box (Caja delimitadora)
                x, y, bw, bh = cv2.boundingRect(cnt)

                # Determinar si se está moviendo comparando con la posición anterior
                estado = "Quieto"
                if prev_cx is not None and prev_cy is not None:
                    distancia_mov = np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
                    if distancia_mov > 3.0:  # Umbral de movimiento en píxeles
                        estado = "En Movimiento"

                prev_cx, prev_cy = cx, cy

                # Dibujar elementos gráficos en la ventana
                color = (0, 255, 0) if estado == "Quieto" else (0, 0, 255)
                
                # Caja delimitadora
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), color, 2)
                
                # Centro del objeto
                cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

                # Mostrar texto con Coordenadas (X, Y) y Estado
                texto_coords = f"Pos: ({cx}, {cy}) px"
                texto_estado = f"Estado: {estado}"
                
                cv2.putText(frame, texto_coords, (x, max(20, y - 25)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                cv2.putText(frame, texto_estado, (x, max(40, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1)

        # Cruz central de referencia del plano de la cámara
        cv2.line(frame, (w // 2, 0), (w // 2, h), (100, 100, 100), 1)
        cv2.line(frame, (0, h // 2), (w, h // 2), (100, 100, 100), 1)

        # Mostrar frames
        cv2.imshow("Detector de Objetos y Coordenadas en Tiempo Real", frame)
        cv2.imshow("Mascara Binaria", binaria)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' o ESC para salir
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detector_tiempo_real()