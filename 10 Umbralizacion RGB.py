import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import imutils
import cv2

# Crea ventana, define tamaño y título
ventana = tk.Tk()
ventana.geometry("1070x470")
ventana.resizable(0, 0)
ventana.title("Umbralización RGB")

# Variables globales
capture = None
Captura = None          # Imagen original (RGB sin redimensionar)
CapturaActual = None    # Imagen mostrada centrada y limpia
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
    
    # Redimensionar manteniendo proporciones naturales
    img_rgb = imutils.resize(img_rgb, width=300)
    if img_rgb.shape[0] > 240:
        img_rgb = imutils.resize(img_rgb, height=240)
        
    CapturaActual = img_rgb.copy()
    
    h_img, w_img = img_rgb.shape[:2]
    
    # Offsets para centrar en el Canvas (300x240)
    offset_x = (300 - w_img) // 2
    offset_y = (240 - h_img) // 2
    
    im = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(image=im)
    
    canvas_roi.delete("all")
    canvas_roi.create_image(offset_x, offset_y, anchor=tk.NW, image=img_tk)
    canvas_roi.image = img_tk
    
    rgb()

# Tomar foto
def Capturar():
    global Captura
    if capture is not None:
        return_value, image = capture.read()
        if return_value:
            Captura = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mostrar_imagen_roi(Captura)

# Subir foto desde archivos
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

# Función para umbralización RGB
def rgb(val=None):
    global CapturaActual
    if CapturaActual is not None:
        minimos = (int(SRedI.get()), int(SGreenI.get()), int(SBlueI.get()))
        maximos = (int(SRedD.get()), int(SGreenD.get()), int(SBlueD.get()))
        
        # Generar máscara según el rango RGB sobre la imagen no deformada
        img_mask = cv2.inRange(CapturaActual, minimos, maximos)
        
        im = Image.fromarray(img_mask)
        img_tk = ImageTk.PhotoImage(image=im)
        
        canvas_umbra.delete("all")
        canvas_umbra.create_image(offset_x, offset_y, anchor=tk.NW, image=img_tk)
        canvas_umbra.image = img_tk

# Control y navegación de las barritas por teclado/mouse
escálas = []
indice_escala_actual = 0

def enfocar_escala(index):
    global indice_escala_actual
    indice_escala_actual = index % len(escálas)
    scale = escálas[indice_escala_actual]
    scale.focus_set()

def seleccionar_al_hacer_clic(event):
    widget = event.widget
    if widget in escálas:
        global indice_escala_actual
        indice_escala_actual = escálas.index(widget)
        widget.focus_set()

def cambiar_valor_escala(delta):
    widget_enfocado = ventana.focus_get()
    
    if widget_enfocado not in escálas:
        scale = escálas[indice_escala_actual]
        scale.focus_set()
    else:
        scale = widget_enfocado
        
    nuevo_val = scale.get() + delta
    nuevo_val = max(1, min(255, nuevo_val))
    scale.set(nuevo_val)
    rgb()

def tecla_presionada(event):
    key = event.keysym
    widget_enfocado = ventana.focus_get()
    
    if widget_enfocado in escálas:
        idx = escálas.index(widget_enfocado)
    else:
        idx = indice_escala_actual

    if key in ["Down", "Tab"]:
        enfocar_escala(idx + 1)
        return "break"
    elif key in ["Up", "ISO_Left_Tab"]:
        enfocar_escala(idx - 1)
        return "break"
    elif key == "Left":
        cambiar_valor_escala(-1)
        return "break"
    elif key == "Right":
        cambiar_valor_escala(1)
        return "break"

# Creación de Deslizadores (RGB)
SRedI = tk.Scale(ventana, from_=1, to=255, orient='horizontal', command=rgb)
SRedI.place(x=760, y=300)

SGreenI = tk.Scale(ventana, from_=1, to=255, orient='horizontal', command=rgb)
SGreenI.place(x=760, y=340)

SBlueI = tk.Scale(ventana, from_=1, to=255, orient='horizontal', command=rgb)
SBlueI.place(x=760, y=380)

SRedD = tk.Scale(ventana, from_=1, to=255, orient='horizontal', command=rgb)
SRedD.set(255)
SRedD.place(x=900, y=300)

SGreenD = tk.Scale(ventana, from_=1, to=255, orient='horizontal', command=rgb)
SGreenD.set(255)
SGreenD.place(x=900, y=340)

SBlueD = tk.Scale(ventana, from_=1, to=255, orient='horizontal', command=rgb)
SBlueD.set(255)
SBlueD.place(x=900, y=380)

escálas = [SRedI, SRedD, SGreenI, SGreenD, SBlueI, SBlueD]

# Bloquear el comportamiento nativo de Up/Down en los Scale y vincular clic
for scale in escálas:
    scale.bind("<Button-1>", seleccionar_al_hacer_clic)
    scale.bind("<Up>", tecla_presionada)
    scale.bind("<Down>", tecla_presionada)

# Etiquetas
LRed = tk.Label(ventana, text="R")
LRed.place(x=870, y=320, width=21, height=16)

LGreen = tk.Label(ventana, text="G")
LGreen.place(x=870, y=360, width=21, height=16)

LBlue = tk.Label(ventana, text="B")
LBlue.place(x=870, y=400, width=21, height=16)

# Botones
BCamara = tk.Button(ventana, text="Iniciar cámara", command=camara)
BCamara.place(x=50, y=330, width=90, height=23)

BCapturar = tk.Button(ventana, text="Tomar foto", command=Capturar)
BCapturar.place(x=150, y=330, width=91, height=23)

BSubir = tk.Button(ventana, text="Subir foto", command=SubirFoto)
BSubir.place(x=250, y=330, width=90, height=23)

# Contenedores de imagen
LImagen = tk.Label(ventana, background="gray")
LImagen.place(x=50, y=50, width=300, height=240)

canvas_roi = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_roi.place(x=390, y=50, width=300, height=240)

canvas_umbra = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_umbra.place(x=730, y=50, width=300, height=240)

# Eventos globales de teclado
ventana.bind("<Key>", tecla_presionada)

# Foco inicial  
SRedI.focus_set()

ventana.mainloop()