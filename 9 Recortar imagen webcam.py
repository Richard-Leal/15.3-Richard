import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import imutils
import cv2

ventana = tk.Tk()
ventana.geometry("1070x450")
ventana.resizable(0, 0)
ventana.title("Recortar foto webcam o subida (Centrada, Proporcional y Coordenadas)")

# Variables globales
capture = None
Captura = None          # Imagen cargada original
CapturaActual = None    # Imagen mostrada/editada actualmente

# Variables para el recuadro de selección
start_x = None
start_y = None
end_x = None
end_y = None
rect_id = None

# Posición del offset de la imagen en el Canvas (para centrarla)
offset_x = 0
offset_y = 0

# Funciones cámara web
def camara():
    global capture
    capture = cv2.VideoCapture(0)
    iniciar()

def iniciar():
    global capture
    if capture is not None:
        ret, frame = capture.read()
        if ret == True:
            # Redimensionar manteniendo proporción (ancho máximo 300, alto máximo 240)
            frame = imutils.resize(frame, width=300)
            if frame.shape[0] > 240:
                frame = imutils.resize(frame, height=240)
            ImagenCamara = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(ImagenCamara)
            img = ImageTk.PhotoImage(image=im)
            LImagen.configure(image=img)
            LImagen.image = img
            LImagen.after(1, iniciar)
        else:
            LImagen.image = None
            capture.release()

def mostrar_imagen_roi(img_rgb):
    global CapturaActual, offset_x, offset_y
    
    # Redimensionar manteniendo aspectos naturales
    img_rgb = imutils.resize(img_rgb, width=300)
    if img_rgb.shape[0] > 240:
        img_rgb = imutils.resize(img_rgb, height=240)
        
    CapturaActual = img_rgb.copy()
    
    h_img, w_img = img_rgb.shape[:2]
    
    # Calcular offsets para centrar exactamente en el Canvas de 300x240
    offset_x = (300 - w_img) // 2
    offset_y = (240 - h_img) // 2
    
    im = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(image=im)
    
    # Limpiar canvas e insertar la imagen centrada
    canvas_roi.delete("all")
    canvas_roi.create_image(offset_x, offset_y, anchor=tk.NW, image=img_tk)
    canvas_roi.image = img_tk

def Capturar():
    global Captura, capture
    if capture is not None:
        return_value, image = capture.read()
        if return_value:
            Captura = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mostrar_imagen_roi(Captura)

def SubirFoto():
    global Captura
    filepath = filedialog.askopenfilename(
        title="Seleccionar imagen",
        filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")]
    )
    if filepath:
        image = cv2.imread(filepath)
        if image is not None:
            Captura = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mostrar_imagen_roi(Captura)

# Eventos del Mouse para el Recuadro Interactivo y Coordenadas
def al_presionar_click(event):
    global start_x, start_y, rect_id
    start_x = event.x
    start_y = event.y
    if rect_id is not None:
        canvas_roi.delete(rect_id)
    rect_id = canvas_roi.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2, dash=(4, 4))
    actualizar_coordenadas(start_x, start_y, start_x, start_y)

def al_arrastrar_mouse(event):
    global rect_id, end_x, end_y
    end_x = event.x
    end_y = event.y
    if rect_id is not None:
        canvas_roi.coords(rect_id, start_x, start_y, end_x, end_y)
    actualizar_coordenadas(start_x, start_y, end_x, end_y)

def al_soltar_click(event):
    global end_x, end_y
    end_x = event.x
    end_y = event.y
    actualizar_coordenadas(start_x, start_y, end_x, end_y)

def actualizar_coordenadas(sx, sy, ex, ey):
    if CapturaActual is not None and sx is not None and ex is not None:
        img_x1 = max(0, min(sx, ex) - offset_x)
        img_y1 = max(0, min(sy, ey) - offset_y)
        img_x2 = min(CapturaActual.shape[1], max(sx, ex) - offset_x)
        img_y2 = min(CapturaActual.shape[0], max(sy, ey) - offset_y)

        img_x1 = max(0, min(img_x1, CapturaActual.shape[1]))
        img_y1 = max(0, min(img_y1, CapturaActual.shape[0]))
        img_x2 = max(0, min(img_x2, CapturaActual.shape[1]))
        img_y2 = max(0, min(img_y2, CapturaActual.shape[0]))

        # Texto unificado completo:
        coordenadas['text'] = f"Coordenadas de selección: x1={img_x1}, y1={img_y1} | x2={img_x2}, y2={img_y2}"
def recortar(event=None):
    global ImgRec, CapturaActual
    if CapturaActual is not None and start_x is not None and end_x is not None:
        # Convertir coordenadas del Canvas a coordenadas de la Matriz de la Imagen
        x1 = max(0, min(start_x, end_x) - offset_x)
        y1 = max(0, min(start_y, end_y) - offset_y)
        x2 = min(CapturaActual.shape[1], max(start_x, end_x) - offset_x)
        y2 = min(CapturaActual.shape[0], max(start_y, end_y) - offset_y)

        if (x2 - x1) > 5 and (y2 - y1) > 5:
            ImgRec = CapturaActual[y1:y2, x1:x2]
            Im = Image.fromarray(ImgRec)
            ImRec = ImageTk.PhotoImage(image=Im)
            LImagenRecorte.configure(image=ImRec)
            LImagenRecorte.image = ImRec
            
            if rect_id is not None:
                canvas_roi.delete(rect_id)

def revertir(event=None):
    global Captura
    if Captura is not None:
        mostrar_imagen_roi(Captura)
        LImagenRecorte.configure(image="")
        LImagenRecorte.image = None
        coordenadas['text'] = "Coordenadas de selección: x1=0, y1=0 | x2=0, y2=0"

ventana.bind("<r>", recortar)
ventana.bind("<R>", recortar)
ventana.bind("<Return>", recortar)

ventana.bind("<z>", revertir)
ventana.bind("<Z>", revertir)
ventana.bind("<BackSpace>", revertir)

# Botones
BCamara = tk.Button(ventana, text="Iniciar cámara", command=camara)
BCamara.place(x=50, y=330, width=90, height=23)

BCapturar = tk.Button(ventana, text="Tomar foto", command=Capturar)
BCapturar.place(x=150, y=330, width=91, height=23)

BSubir = tk.Button(ventana, text="Subir foto", command=SubirFoto)
BSubir.place(x=250, y=330, width=90, height=23)

BRecortar = tk.Button(ventana, text="Recortar", command=recortar)
BRecortar.place(x=440, y=330, width=80, height=23)

BRevertir = tk.Button(ventana, text="Revertir", command=revertir)
BRevertir.place(x=550, y=330, width=80, height=23)

# Un solo Label con formato y fuente limpios
coordenadas = tk.Label(
    ventana, 
    text="Coordenadas de selección: x1=0, y1=0 | x2=0, y2=0", 
    font=("Consolas", 9, "bold"), 
    fg="#2e323a"
)
coordenadas.place(x=390, y=300)

# Cuadros de imagen gris / Canvas
LImagen = tk.Label(ventana, background="gray")
LImagen.place(x=50, y=50, width=300, height=240)

canvas_roi = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_roi.place(x=390, y=50, width=300, height=240)

# Eventos de ratón vinculados al Canvas
canvas_roi.bind("<ButtonPress-1>", al_presionar_click)
canvas_roi.bind("<B1-Motion>", al_arrastrar_mouse)
canvas_roi.bind("<ButtonRelease-1>", al_soltar_click)

LImagenRecorte = tk.Label(ventana, background="gray")
LImagenRecorte.place(x=730, y=50, width=300, height=240)

ventana.mainloop()