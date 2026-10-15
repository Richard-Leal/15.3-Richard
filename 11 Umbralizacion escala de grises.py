import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import imutils
import cv2

# Crea ventana, define tamaño y título
ventana = tk.Tk()
ventana.geometry("1070x430")
ventana.resizable(0, 0)
ventana.title("Umbralización escala de grises (En tiempo real y Teclado)")

# Variables globales
capture = None
CapturaG = None          # Imagen en escala de grises sin deformar
CapturaActual = None    # Imagen ajustada proporcionalmente
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

def mostrar_imagen_roi(img_gray):
    global CapturaActual, offset_x, offset_y
    
    # Redimensionar manteniendo la proporción natural (máx 300x240)
    img_gray = imutils.resize(img_gray, width=300)
    if img_gray.shape[0] > 240:
        img_gray = imutils.resize(img_gray, height=240)
        
    CapturaActual = img_gray.copy()
    
    h_img, w_img = img_gray.shape[:2]
    offset_x = (300 - w_img) // 2
    offset_y = (240 - h_img) // 2
    
    im = Image.fromarray(img_gray)
    img_tk = ImageTk.PhotoImage(image=im)
    
    canvas_roi.delete("all")
    canvas_roi.create_image(offset_x, offset_y, anchor=tk.NW, image=img_tk)
    canvas_roi.image = img_tk
    
    # Actualizar la umbralización inmediatamente con la nueva foto
    umbralizacion()

# Tomar foto
def Capturar():
    global capture
    if capture is not None:
        return_value, image = capture.read()
        if return_value:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mostrar_imagen_roi(img_gray)

# Subir foto desde archivos
def SubirFoto():
    filepath = filedialog.askopenfilename(
        title="Seleccionar imagen",
        filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")]
    )
    if filepath:
        image = cv2.imread(filepath)
        if image is not None:
            img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mostrar_imagen_roi(img_gray)

# Función de Umbralización en Tiempo Real
def umbralizacion(val=None):
    global CapturaActual
    if CapturaActual is not None:
        valor = int(sliderUmbra.get())
        ret, thresh1 = cv2.threshold(CapturaActual, valor, 255, cv2.THRESH_BINARY)
        
        im = Image.fromarray(thresh1)
        img_tk = ImageTk.PhotoImage(image=im)
        
        canvas_umbra.delete("all")
        canvas_umbra.create_image(offset_x, offset_y, anchor=tk.NW, image=img_tk)
        canvas_umbra.image = img_tk

# Control de teclado para el Deslizador
def cambiar_valor_deslizador(delta):
    sliderUmbra.focus_set()
    nuevo_val = sliderUmbra.get() + delta
    nuevo_val = max(0, min(255, nuevo_val))
    sliderUmbra.set(nuevo_val)
    umbralizacion()

def tecla_presionada(event):
    key = event.keysym
    if key in ["Left", "Down"]:
        cambiar_valor_deslizador(-1)
        return "break"
    elif key in ["Right", "Up"]:
        cambiar_valor_deslizador(1)
        return "break"

def seleccionar_al_hacer_clic(event):
    sliderUmbra.focus_set()

# Deslizador (Scale) en tiempo real
sliderUmbra = tk.Scale(ventana, from_=0, to=255, orient='horizontal', command=umbralizacion)
sliderUmbra.place(x=780, y=320, width=200)

sliderUmbra.bind("<Button-1>", seleccionar_al_hacer_clic)
sliderUmbra.bind("<Left>", tecla_presionada)
sliderUmbra.bind("<Right>", tecla_presionada)
sliderUmbra.bind("<Up>", tecla_presionada)
sliderUmbra.bind("<Down>", tecla_presionada)

# Etiqueta aclaratoria para el Deslizador
lblUmbra = tk.Label(ventana, text="Umbral:", font=("Arial", 9, "bold"))
lblUmbra.place(x=725, y=338)

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

# Vincular teclado global
ventana.bind("<Key>", tecla_presionada)

sliderUmbra.focus_set()

ventana.mainloop()