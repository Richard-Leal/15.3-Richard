import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import imutils
import cv2
import os

# Variables globales
imageToShow = None
Captura = None
patron_global = None
patron_path = None
capture = None
camara_activada = False
valor = 0

# Variables para recorte por ratón (Rubberband)
start_x = None
start_y = None
end_x = None
end_y = None
rect_id = None
offset_x = 0
offset_y = 0
recorte_activo = None

ventana = tk.Tk()
ventana.geometry("1500x550")
ventana.title("Análisis de Patrones - Tutorial Templates Mejorado")

# Funciones de carga e inicio
def archivo():
    try:
        path_image = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")])
        if len(path_image) > 0:
            global imagenFile, imageToShow, valor, recorte_activo
            imagenFile = cv2.imread(path_image)
            
            # Redimensionar proporcionalmente para ajustar a 300x240
            img_rgb = cv2.cvtColor(imagenFile, cv2.COLOR_BGR2RGB)
            img_rgb = imutils.resize(img_rgb, width=300)
            if img_rgb.shape[0] > 240:
                img_rgb = imutils.resize(img_rgb, height=240)
                
            imageToShow = img_rgb.copy()
            recorte_activo = cv2.cvtColor(imageToShow, cv2.COLOR_RGB2GRAY)
            valor = 0
            mostrar_imagen_original()
            umbralizar_tiempo_real()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir la imagen: {e}")

def camara():
    global capture, camara_activada
    if not camara_activada:
        try:
            capture = cv2.VideoCapture(0)
            iniciar()
            camara_activada = True
            BCamara.configure(text="Detener")
        except Exception as e:
            messagebox.showerror("Error", f"Error al inicializar cámara: {e}")
    else:
        if capture is not None:
            capture.release()
        camara_activada = False
        BCamara.configure(text="Cámara")
        canvas_orig.delete("all")

def iniciar():
    global capture
    if capture is not None and camara_activada:
        ret, frame = capture.read()
        if ret:
            frame = imutils.resize(frame, width=300)
            if frame.shape[0] > 240:
                frame = imutils.resize(frame, height=240)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(frame_rgb)
            img = ImageTk.PhotoImage(image=im)
            canvas_orig.delete("all")
            canvas_orig.create_image(150, 120, image=img)
            canvas_orig.image = img
            canvas_orig.after(10, iniciar)

def Capturar():
    global valor, Captura, recorte_activo
    if capture is not None:
        ret, frame = capture.read()
        if ret:
            frame = imutils.resize(frame, width=300)
            if frame.shape[0] > 240:
                frame = imutils.resize(frame, height=240)
            Captura = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            recorte_activo = cv2.cvtColor(Captura, cv2.COLOR_RGB2GRAY)
            valor = 2
            mostrar_imagen_original()
            umbralizar_tiempo_real()

def mostrar_imagen_original():
    global offset_x, offset_y
    base = imageToShow if valor == 0 else Captura
    if base is not None:
        h_img, w_img = base.shape[:2]
        offset_x = (300 - w_img) // 2
        offset_y = (240 - h_img) // 2
        im = Image.fromarray(base)
        img = ImageTk.PhotoImage(image=im)
        canvas_orig.delete("all")
        canvas_orig.create_image(offset_x, offset_y, anchor=tk.NW, image=img)
        canvas_orig.image = img

# Eventos para Recorte Interactivo con el Ratón
def al_presionar_click(event):
    global start_x, start_y, rect_id
    start_x, start_y = event.x, event.y
    if rect_id is not None:
        canvas_orig.delete(rect_id)
    rect_id = canvas_orig.create_rectangle(start_x, start_y, start_x, start_y, outline="yellow", width=2, dash=(4, 4))

def al_arrastrar_mouse(event):
    global rect_id, end_x, end_y
    end_x, end_y = event.x, event.y
    if rect_id is not None:
        canvas_orig.coords(rect_id, start_x, start_y, end_x, end_y)

def al_soltar_click(event):
    global end_x, end_y, recorte_activo
    end_x, end_y = event.x, event.y
    base = imageToShow if valor == 0 else Captura
    if base is not None and start_x is not None and end_x is not None:
        x1 = max(0, min(start_x, end_x) - offset_x)
        y1 = max(0, min(start_y, end_y) - offset_y)
        x2 = min(base.shape[1], max(start_x, end_x) - offset_x)
        y2 = min(base.shape[0], max(start_y, end_y) - offset_y)
        
        if (x2 - x1) > 5 and (y2 - y1) > 5:
            recorte_rgb = base[y1:y2, x1:x2]
            recorte_activo = cv2.cvtColor(recorte_rgb, cv2.COLOR_RGB2GRAY)
            
            im = Image.fromarray(recorte_activo)
            img = ImageTk.PhotoImage(image=im)
            canvas_recorte.delete("all")
            canvas_recorte.create_image(150, 120, image=img)
            canvas_recorte.image = img
            
            umbralizar_tiempo_real()

def resetear_recorte():
    global recorte_activo, rect_id
    base = imageToShow if valor == 0 else Captura
    if base is not None:
        recorte_activo = cv2.cvtColor(base, cv2.COLOR_RGB2GRAY)
        if rect_id is not None:
            canvas_orig.delete(rect_id)
        canvas_recorte.delete("all")
        umbralizar_tiempo_real()

# Umbralización y Análisis de Manchas en Tiempo Real
def umbralizar_tiempo_real(val=None):
    global recorte_activo
    if recorte_activo is not None:
        umb = int(SGray.get())
        img_mask = cv2.inRange(recorte_activo, umb, 255)
        
        im = Image.fromarray(img_mask)
        img_tk = ImageTk.PhotoImage(image=im)
        canvas_mask.delete("all")
        canvas_mask.create_image(150, 120, image=img_tk)
        canvas_mask.image = img_tk
        
        # Análisis de manchas en vivo
        num_pixels = cv2.countNonZero(img_mask)
        tot = img_mask.size
        porcentaje = (num_pixels / tot) * 100 if tot > 0 else 0
        contornos, _ = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        cadena = (f"Cantidad de manchas blancas: {len(contornos)}\n"
                  f"Área mancha: {num_pixels} px\n"
                  f"Porcentaje área con manchas: {round(porcentaje, 2)}%")
        CajaTexto.configure(state='normal')
        CajaTexto.delete(1.0, tk.END)
        CajaTexto.insert(1.0, cadena)
        CajaTexto.configure(state='disabled')

# Control con teclado para Slider
def cambiar_valor_deslizador(delta):
    SGray.focus_set()
    nuevo_val = SGray.get() + delta
    nuevo_val = max(0, min(255, nuevo_val))
    SGray.set(nuevo_val)
    umbralizar_tiempo_real()

def tecla_presionada(event):
    key = event.keysym
    if key in ["Left", "Down"]:
        cambiar_valor_deslizador(-1)
        return "break"
    elif key in ["Right", "Up"]:
        cambiar_valor_deslizador(1)
        return "break"

# Lógica de Guardar, Cargar y Comparación
def Guardar_Patron():
    global patron_global, patron_path, recorte_activo
    if recorte_activo is None:
        messagebox.showerror("Error", "No hay imagen/recorte activo para guardar")
        return
    umb = int(SGray.get())
    template = cv2.inRange(recorte_activo, umb, 255)
    
    ruta = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")], title="Guardar template como...")
    if not ruta:
        return
    cv2.imwrite(ruta, template)
    patron_global = template
    patron_path = ruta
    messagebox.showinfo("Éxito", f"Template guardado en:\n{ruta}")

def Cargar_Patron():
    global patron_global, patron_path
    ruta = filedialog.askopenfilename(filetypes=[("PNG image", "*.png")], title="Cargar template...")
    if not ruta:
        return
    template = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
    if template is None:
        messagebox.showerror("Error", "No se pudo cargar el template")
        return
    patron_global = template
    patron_path = ruta
    
    im = Image.fromarray(template)
    img = ImageTk.PhotoImage(image=im)
    canvas_recorte.delete("all")
    canvas_recorte.create_image(150, 120, image=img)
    canvas_recorte.image = img
    messagebox.showinfo("Cargado", f"Template cargado: {os.path.basename(ruta)}")

def rotar_template(template, angulo):
    h, w = template.shape[:2]
    cx, cy = w // 2, h // 2
    M = cv2.getRotationMatrix2D((cx, cy), angulo, 1.0)
    cos_a, sin_a = abs(M[0, 0]), abs(M[0, 1])
    new_w = int(h * sin_a + w * cos_a)
    new_h = int(h * cos_a + w * sin_a)
    M[0, 2] += (new_w / 2) - cx
    M[1, 2] += (new_h / 2) - cy
    return cv2.warpAffine(template, M, (new_w, new_h), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def comparar_imagen(origen="archivo"):
    global patron_global, Captura, imageToShow
    if patron_global is None:
        messagebox.showerror("Error", "Primero guarda o carga un template")
        return
    umb = int(SGray.get())
    paso = int(SAngulo.get())
    
    if origen == "archivo":
        path = filedialog.askopenfilename(filetypes=[("Imagen", "*.jpg *.jpeg *.png")], title="Selecciona imagen a comparar")
        if not path:
            return
        img_raw = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img_raw is None:
            messagebox.showerror("Error", "No se pudo cargar la imagen")
            return
        imagen_nueva = imutils.resize(img_raw, width=300)
    elif origen == "camara":
        if Captura is None:
            messagebox.showerror("Error", "Primero toma una foto con la cámara")
            return
        imagen_nueva = cv2.cvtColor(Captura, cv2.COLOR_RGB2GRAY)
    else:
        return

    imagen_umb = cv2.inRange(imagen_nueva, umb, 255)
    ih, iw = imagen_umb.shape[:2]
    
    CajaTexto2.configure(state='normal')
    CajaTexto2.delete(1.0, tk.END)
    CajaTexto2.insert(1.0, f"Buscando en ángulos (paso {paso}°)...")
    CajaTexto2.configure(state='disabled')
    ventana.update_idletasks()
    
    mejor_val = -999.0
    mejor_angulo, mejor_tipo, mejor_tmpl, mejor_loc = 0, "original", None, (0, 0)

    for ang in range(0, 360, paso):
        tmpl_rot = rotar_template(patron_global, ang)
        th, tw = tmpl_rot.shape[:2]
        if th > ih or tw > iw:
            continue
        for tipo, tmpl in [("original", tmpl_rot), ("invertido", cv2.bitwise_not(tmpl_rot))]:
            r = cv2.matchTemplate(imagen_umb, tmpl, cv2.TM_CCOEFF_NORMED)
            _, v, _, loc = cv2.minMaxLoc(r)
            if v > mejor_val:
                mejor_val, mejor_loc, mejor_angulo, mejor_tipo, mejor_tmpl = v, loc, ang, tipo, tmpl

    if mejor_tmpl is None:
        messagebox.showerror("Error", "El template es más grande que la imagen elegida.")
        return

    th, tw = mejor_tmpl.shape[:2]
    mx, my = mejor_loc
    resultado_color = cv2.cvtColor(imagen_umb, cv2.COLOR_GRAY2RGB)
    cv2.rectangle(resultado_color, (mx, my), (mx + tw, my + th), (255, 255, 0), 2)
    
    im = Image.fromarray(resultado_color)
    tk_img = ImageTk.PhotoImage(image=im)
    canvas_patron.delete("all")
    canvas_patron.create_image(150, 120, image=tk_img)
    canvas_patron.image = tk_img

    similitud = mejor_val * 100
    info = (f"Similitud: {round(similitud, 2)}%\n"
            f"Tipo: {mejor_tipo} | Ángulo: {mejor_angulo}°\n"
            f"Posición: x={mx}, y={my}\n"
            f"Umbral: {umb} | Paso angular: {paso}°")
    CajaTexto2.configure(state='normal')
    CajaTexto2.delete(1.0, tk.END)
    CajaTexto2.insert(1.0, info)
    CajaTexto2.configure(state='disabled')

# UI INTERFAZ
canvas_orig = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_orig.place(x=50, y=50)

canvas_recorte = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_recorte.place(x=430, y=50)

canvas_mask = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_mask.place(x=810, y=50)

canvas_patron = tk.Canvas(ventana, background="gray", width=300, height=240, highlightthickness=0)
canvas_patron.place(x=1150, y=50)

# Eventos de ratón sobre la imagen original para recuadrar por arrastre
canvas_orig.bind("<ButtonPress-1>", al_presionar_click)
canvas_orig.bind("<B1-Motion>", al_arrastrar_mouse)
canvas_orig.bind("<ButtonRelease-1>", al_soltar_click)

# Sliders
SGray = tk.Scale(ventana, from_=0, to=255, orient='horizontal', label="Umbral Gris (Tiempo Real)", command=umbralizar_tiempo_real)
SGray.set(171)
SGray.place(x=430, y=320, width=300)

SAngulo = tk.Scale(ventana, from_=1, to=45, orient='horizontal', label="Paso angular (°)")
SAngulo.set(5)
SAngulo.place(x=430, y=380, width=300)

SGray.bind("<Button-1>", lambda e: SGray.focus_set())
SGray.bind("<Left>", tecla_presionada)
SGray.bind("<Right>", tecla_presionada)
SGray.bind("<Up>", tecla_presionada)
SGray.bind("<Down>", tecla_presionada)

# Botones
BArchivo = tk.Button(ventana, text="Archivo", command=archivo)
BArchivo.place(x=50, y=310, width=80, height=25)

BCamara = tk.Button(ventana, text="Cámara", command=camara)
BCamara.place(x=140, y=310, width=80, height=25)

BCapturar = tk.Button(ventana, text="Tomar foto", command=Capturar)
BCapturar.place(x=230, y=310, width=80, height=25)

BResetRecorte = tk.Button(ventana, text="Revertir Recorte", command=resetear_recorte)
BResetRecorte.place(x=520, y=300, width=120, height=23)

BGuardar = tk.Button(ventana, text="Guardar template", command=Guardar_Patron, bg="#2d6a4f", fg="white", font=("Arial", 9, "bold"))
BGuardar.place(x=1150, y=300, width=145, height=26) 

BCargar = tk.Button(ventana, text="Cargar template", command=Cargar_Patron, bg="#1d3557", fg="white", font=("Arial", 9, "bold"))
BCargar.place(x=1305, y=300, width=145, height=26)

BCompararArchivo = tk.Button(ventana, text="Comparar con imagen", command=lambda: comparar_imagen("archivo"), bg="#457b9d", fg="white", font=("Arial", 9, "bold"))
BCompararArchivo.place(x=1150, y=470, width=145, height=30)

BCompararCamara = tk.Button(ventana, text="Comparar con cámara", command=lambda: comparar_imagen("camara"), bg="#457b9d", fg="white", font=("Arial", 9, "bold"))
BCompararCamara.place(x=1305, y=470, width=145, height=30)

# Labels informativos
tk.Label(ventana, text="Imagen original (Arrastra con el ratón)").place(x=50, y=25, width=300)
tk.Label(ventana, text="Recorte / Template").place(x=430, y=25, width=300)
tk.Label(ventana, text="Análisis de manchas").place(x=810, y=25, width=300)
tk.Label(ventana, text="Resultado comparación").place(x=1150, y=25, width=300)

CajaTexto = tk.Text(ventana, state="disabled")
CajaTexto.place(x=810, y=300, width=300, height=120)

CajaTexto2 = tk.Text(ventana, state="disabled")
CajaTexto2.place(x=1150, y=340, width=300, height=120)

ventana.bind("<Key>", tecla_presionada)
SGray.focus_set()

ventana.mainloop()