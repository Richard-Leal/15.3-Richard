import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import imutils
import cv2

# Configuración de la ventana principal
ventana = tk.Tk()
ventana.geometry("1350x480")
ventana.resizable(0, 0)
ventana.title("Optimización Programa Final - Procesamiento de Imágenes")

# Variables globales
capture = None
Captura = None           # Imagen original en color
CapturaG = None          # Imagen original en escala de grises
CapturaActual = None     # Imagen ROI activa/recortada
CapturaGrisesActual = None # Imagen ROI activa recortada en grises
thresh1 = None

# Variables para selección por arrastre (Rubberband)
start_x = None
start_y = None
end_x = None
end_y = None
rect_id = None
offset_x = 0
offset_y = 0

# Funciones de la Cámara Web
def camara():
    global capture
    capture = cv2.VideoCapture(0)
    iniciar()

def iniciar():
    global capture
    if capture is not None:
        ret, frame = capture.read()
        if ret:
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
    global CapturaActual, CapturaGrisesActual, offset_x, offset_y
    
    # Redimensionar proporcionalmente para ajustar al Canvas de 300x240
    img_rgb = imutils.resize(img_rgb, width=300)
    if img_rgb.shape[0] > 240:
        img_rgb = imutils.resize(img_rgb, height=240)
        
    CapturaActual = img_rgb.copy()
    CapturaGrisesActual = cv2.cvtColor(CapturaActual, cv2.COLOR_RGB2GRAY)
    
    h_img, w_img = img_rgb.shape[:2]
    offset_x = (300 - w_img) // 2
    offset_y = (240 - h_img) // 2
    
    im = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(image=im)
    
    canvas_roi.delete("all")
    canvas_roi.create_image(offset_x, offset_y, anchor=tk.NW, image=img_tk)
    canvas_roi.image = img_tk
    
    # Mostrar la versión en escala de grises en el paso 2
    im_g = Image.fromarray(CapturaGrisesActual)
    img_g_tk = ImageTk.PhotoImage(image=im_g)
    canvas_crop.delete("all")
    canvas_crop.create_image(offset_x, offset_y, anchor=tk.NW, image=img_g_tk)
    canvas_crop.image = img_g_tk
    
    # Ejecutar la umbralización inicial
    umbralizacion()

# Tomar foto desde la cámara
def Capturar():
    global Captura, CapturaG
    if capture is not None:
        return_value, image = capture.read()
        if return_value:
            Captura = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            CapturaG = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mostrar_imagen_roi(Captura)

# Subir foto local
def SubirFoto():
    global Captura, CapturaG
    filepath = filedialog.askopenfilename(
        title="Seleccionar imagen",
        filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")]
    )
    if filepath:
        image = cv2.imread(filepath)
        if image is not None:
            Captura = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            CapturaG = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mostrar_imagen_roi(Captura)

# Eventos del ratón para selección por arrastre (Rubberband)
def al_presionar_click(event):
    global start_x, start_y, rect_id
    start_x = event.x
    start_y = event.y
    if rect_id is not None:
        canvas_roi.delete(rect_id)
    rect_id = canvas_roi.create_rectangle(start_x, start_y, start_x, start_y, outline="yellow", width=2, dash=(4, 4))

def al_arrastrar_mouse(event):
    global rect_id, end_x, end_y
    end_x = event.x
    end_y = event.y
    if rect_id is not None:
        canvas_roi.coords(rect_id, start_x, start_y, end_x, end_y)

def al_soltar_click(event):
    global end_x, end_y
    end_x = event.x
    end_y = event.y

# Función para recortar el área seleccionada
def recortar(event=None):
    global CapturaActual, CapturaGrisesActual
    if CapturaActual is not None and start_x is not None and end_x is not None:
        x1 = max(0, min(start_x, end_x) - offset_x)
        y1 = max(0, min(start_y, end_y) - offset_y)
        x2 = min(CapturaActual.shape[1], max(start_x, end_x) - offset_x)
        y2 = min(CapturaActual.shape[0], max(start_y, end_y) - offset_y)

        if (x2 - x1) > 5 and (y2 - y1) > 5:
            recorte_rgb = CapturaActual[y1:y2, x1:x2]
            recorte_gray = CapturaGrisesActual[y1:y2, x1:x2]
            
            # Redimensionar el recorte para ajustarlo al Canvas del Paso 2
            recorte_gray_disp = imutils.resize(recorte_gray, width=300)
            if recorte_gray_disp.shape[0] > 240:
                recorte_gray_disp = imutils.resize(recorte_gray_disp, height=240)
                
            CapturaGrisesActual = recorte_gray_disp
            
            h_rec, w_rec = recorte_gray_disp.shape[:2]
            off_x = (300 - w_rec) // 2
            off_y = (240 - h_rec) // 2
            
            im_g = Image.fromarray(recorte_gray_disp)
            img_g_tk = ImageTk.PhotoImage(image=im_g)
            
            canvas_crop.delete("all")
            canvas_crop.create_image(off_x, off_y, anchor=tk.NW, image=img_g_tk)
            canvas_crop.image = img_g_tk
            
            if rect_id is not None:
                canvas_roi.delete(rect_id)
                
            umbralizacion()

# Función para revertir el recorte
def revertir(event=None):
    global Captura
    if Captura is not None:
        mostrar_imagen_roi(Captura)

# Función para la Umbralización en Tiempo Real
def umbralizacion(val=None):
    global thresh1, CapturaGrisesActual
    if CapturaGrisesActual is not None:
        valor = int(sliderUmbra.get())
        ret, thresh1 = cv2.threshold(CapturaGrisesActual, valor, 255, cv2.THRESH_BINARY)
        
        h_rec, w_rec = CapturaGrisesActual.shape[:2]
        off_x = (300 - w_rec) // 2
        off_y = (240 - h_rec) // 2
        
        im = Image.fromarray(thresh1)
        img_tk = ImageTk.PhotoImage(image=im)
        
        canvas_umbra.delete("all")
        canvas_umbra.create_image(off_x, off_y, anchor=tk.NW, image=img_tk)
        canvas_umbra.image = img_tk
        
        # Actualizar automáticamente el análisis de manchas
        manchasG()

# Función para el Análisis de Manchas
def manchasG():
    global thresh1
    if thresh1 is not None:
        num_pixels_con_manchas = cv2.countNonZero(thresh1)
        porcentaje_manchas = (num_pixels_con_manchas / thresh1.size) * 100
        porcentaje_sin_manchas = 100 - porcentaje_manchas
        
        contornos, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        manchas = len(contornos)
        
        manchas_negras = (porcentaje_manchas * manchas) / porcentaje_sin_manchas if porcentaje_sin_manchas > 0 else 0
        
        Cadena = f"Cantidad de manchas blancas: {manchas}\n"
        Cadena += f"Porcentaje área con manchas: {round(porcentaje_manchas, 2)}%\n"
        Cadena += f"Cantidad de manchas negras: {round(manchas_negras)}"
        
        CajaTexto.configure(state="normal")
        CajaTexto.delete(1.0, tk.END)
        CajaTexto.insert(1.0, Cadena)
        CajaTexto.configure(state="disabled")

# Control del Deslizador por teclado
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

# --- INTERFAZ GRÁFICA ---

# Títulos de Pasos
lbl_p1 = tk.Label(ventana, text="Paso 1: Cámara / Seleccionar foto", font=("Arial", 9, "bold"))
lbl_p1.place(x=50, y=25)

lbl_p2 = tk.Label(ventana, text="Paso 2: Recortar por arrastre (R / Z)", font=("Arial", 9, "bold"))
lbl_p2.place(x=370, y=25)

lbl_p3 = tk.Label(ventana, text="Paso 3: Umbralizar (0-255)", font=("Arial", 9, "bold"))
lbl_p3.place(x=690, y=25)

lbl_p4 = tk.Label(ventana, text="Paso 4: Análisis de Manchas", font=("Arial", 9, "bold"))
lbl_p4.place(x=1010, y=25)

# Contenedores de Imagen (Canvas)
LImagen = tk.Label(ventana, background="gray")
LImagen.place(x=30, y=50, width=300, height=240)

canvas_roi = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_roi.place(x=350, y=50, width=300, height=240)

canvas_crop = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_crop.place(x=670, y=50, width=300, height=240)

canvas_umbra = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_umbra.place(x=990, y=50, width=300, height=240)

# Cuadro de Texto para el Análisis
CajaTexto = tk.Text(ventana, state="disabled", font=("Segoe UI", 9))
CajaTexto.place(x=990, y=300, width=300, height=110)

# Deslizador de Umbral
sliderUmbra = tk.Scale(ventana, from_=0, to=255, orient='horizontal', command=umbralizacion)
sliderUmbra.place(x=730, y=300, width=200)

lblUmbra = tk.Label(ventana, text="Umbral:", font=("Arial", 9, "bold"))
lblUmbra.place(x=675, y=318)

sliderUmbra.bind("<Button-1>", seleccionar_al_hacer_clic)
sliderUmbra.bind("<Left>", tecla_presionada)
sliderUmbra.bind("<Right>", tecla_presionada)
sliderUmbra.bind("<Up>", tecla_presionada)
sliderUmbra.bind("<Down>", tecla_presionada)

# Eventos de ratón para el recuadro interactivo (Paso 1 / ROI)
canvas_roi.bind("<ButtonPress-1>", al_presionar_click)
canvas_roi.bind("<B1-Motion>", al_arrastrar_mouse)
canvas_roi.bind("<ButtonRelease-1>", al_soltar_click)

# Botones
BCamara = tk.Button(ventana, text="Iniciar cámara", command=camara)
BCamara.place(x=30, y=310, width=90, height=23)

BCapturar = tk.Button(ventana, text="Tomar foto", command=Capturar)
BCapturar.place(x=130, y=310, width=90, height=23)

BSubir = tk.Button(ventana, text="Subir foto", command=SubirFoto)
BSubir.place(x=230, y=310, width=90, height=23)

BRecortar = tk.Button(ventana, text="Recortar (R)", command=recortar)
BRecortar.place(x=400, y=310, width=90, height=23)

BRevertir = tk.Button(ventana, text="Revertir (Z)", command=revertir)
BRevertir.place(x=510, y=310, width=90, height=23)

# Vincular teclas de acceso rápido
ventana.bind("<r>", recortar)
ventana.bind("<R>", recortar)
ventana.bind("<Return>", recortar)
ventana.bind("<z>", revertir)
ventana.bind("<Z>", revertir)
ventana.bind("<BackSpace>", revertir)
ventana.bind("<Key>", tecla_presionada)

sliderUmbra.focus_set()

ventana.mainloop()