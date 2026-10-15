import cv2

print("Buscando cámaras disponibles...")
for idx in range(5):
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✅ ¡Cámara detectada en el Índice {idx}!")
        else:
            print(f"⚠️ Índice {idx} abre pero no entrega imagen.")
        cap.release()
    else:
        print(f"❌ No hay cámara en el Índice {idx}.")