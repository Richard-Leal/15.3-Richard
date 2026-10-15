import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import imutils
import cv2
import os

CARPETA_PATRONES = "patrones_guardados"
if not os.path.exists(CARPETA_PATRONES):
    os.makedirs(CARPETA_PATRONES)

BG = "#1e1e2e"
PANEL = "#252538"
ACCENT = "#313244"
FG = "#cdd6f4"
FONT = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")

imageToShow = None
Captura = None
capture = None
camara_activada = False
valor = 0
recorte_activo = None

start_x = None
start_y = None
end_x = None
end_y = None
rect_id = None
offset_x = 0
offset_y = 0

ventana = tk.Tk()
ventana.geometry("1150x640")
ventana.resizable(False, False)
ventana.title("Análisis de Patrones - Tutorial MatchShape OK")
ventana.configure(bg=BG)

def archivo():
    try:
        path_image = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")])
        if len(path_image) > 0:
            global imagenFile, imageToShow, valor, recorte_activo
            imagenFile = cv2.imread(path_image)
            
            img_rgb = cv2.cvtColor(imagenFile, cv2.COLOR_BGR2RGB)
            img_rgb = imutils.resize(img_rgb, width=311)
            if img_rgb.shape[0] > 241:
                img_rgb = imutils.resize(img_rgb, height=241)
                
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
        BCamara.configure(text="Iniciar Cámara")
        canvas_orig.delete("all")

def iniciar():
    global capture
    if capture is not None and camara_activada:
        ret, frame = capture.read()
        if ret:
            frame = imutils.resize(frame, width=311)
            if frame.shape[0] > 241:
                frame = imutils.resize(frame, height=241)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(frame_rgb)
            img = ImageTk.PhotoImage(image=im)
            canvas_orig.delete("all")
            canvas_orig.create_image(155, 120, image=img)
            canvas_orig.image = img
            canvas_orig.after(10, iniciar)

def Capturar():
    global valor, Captura, recorte_activo
    if capture is not None:
        ret, frame = capture.read()
        if ret:
            frame = imutils.resize(frame, width=311)
            if frame.shape[0] > 241:
                frame = imutils.resize(frame, height=241)
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
        offset_x = (311 - w_img) // 2
        offset_y = (241 - h_img) // 2
        im = Image.fromarray(base)
        img = ImageTk.PhotoImage(image=im)
        canvas_orig.delete("all")
        canvas_orig.create_image(offset_x, offset_y, anchor=tk.NW, image=img)
        canvas_orig.image = img

def al_presionar_click(event):
    global start_x, start_y, rect_id
    start_x, start_y = event.x, event.y
    if rect_id is not None:
        canvas_orig.delete(rect_id)
    rect_id = canvas_orig.create_rectangle(start_x, start_y, start_x, start_y, outline="#f9e2af", width=2, dash=(4, 4))

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
            umbralizar_tiempo_real()

def resetear_recorte():
    global recorte_activo, rect_id
    base = imageToShow if valor == 0 else Captura
    if base is not None:
        recorte_activo = cv2.cvtColor(base, cv2.COLOR_RGB2GRAY)
        if rect_id is not None:
            canvas_orig.delete(rect_id)
        umbralizar_tiempo_real()

def umbralizar_tiempo_real(val=None):
    global recorte_activo
    if recorte_activo is not None:
        umb = int(SGray.get())
        img_mask = cv2.inRange(recorte_activo, umb, 255)
        
        img_mask_resized = cv2.resize(img_mask, (311, 241), interpolation=cv2.INTER_NEAREST)
        
        im = Image.fromarray(img_mask_resized)
        img_tk = ImageTk.PhotoImage(image=im)
        canvas_mask.delete("all")
        canvas_mask.create_image(0, 0, anchor=tk.NW, image=img_tk)
        canvas_mask.image = img_tk
        
        comparar_patrones_silencioso()

# MANEJO DIRECTO Y LIMPIO DEL TECLADO
def tecla_presionada(event):
    # Si estás escribiendo en la caja de texto, NO mover el slider
    if ventana.focus_get() == EntradaNombre:
        return
    
    key = event.keysym
    val_actual = SGray.get()
    
    if key in ["Left", "Down"]:
        SGray.set(max(0, val_actual - 1))
        umbralizar_tiempo_real()
    elif key in ["Right", "Up"]:
        SGray.set(min(255, val_actual + 1))
        umbralizar_tiempo_real()

def Guardar_Patron():
    global recorte_activo
    if recorte_activo is None:
        messagebox.showwarning("Advertencia", "No hay imagen/recorte para guardar")
        return
        
    nombre = EntradaNombre.get().strip().replace(" ", "_") or "patron"
    tipo = VariableTipo.get().lower()
    umb = int(SGray.get())
    img_mask = cv2.inRange(recorte_activo, umb, 255)
    
    filename = f"{nombre}_{tipo}.png"
    path = os.path.join(CARPETA_PATRONES, filename)
    try:
        cv2.imwrite(path, img_mask)
        messagebox.showinfo("Guardado", f"Patrón guardado correctamente:\n{filename}")
        comparar_patrones_silencioso()
    except Exception as e:
        messagebox.showerror("Error", f"Error al guardar: {e}")

def comparar_patrones_silencioso():
    global recorte_activo
    if recorte_activo is None:
        return
        
    archivos = [f for f in os.listdir(CARPETA_PATRONES) if f.endswith((".png", ".jpg", ".jpeg"))]
    if not archivos:
        ComparacionCaja.config(state="normal")
        ComparacionCaja.delete(1.0, tk.END)
        ComparacionCaja.insert(tk.END, "No hay patrones en 'patrones_guardados'")
        ComparacionCaja.config(state="disabled")
        return
        
    umb = int(SGray.get())
    img_actual_bin = cv2.inRange(recorte_activo, umb, 255)
    
    contornos_actual, _ = cv2.findContours(img_actual_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos_validos = [cnt for cnt in contornos_actual if cv2.contourArea(cnt) > 20]
    
    if len(contornos_validos) == 0:
        ComparacionCaja.config(state="normal")
        ComparacionCaja.delete(1.0, tk.END)
        ComparacionCaja.insert(tk.END, "Ajusta el umbral: No hay objeto blanco detectable.")
        ComparacionCaja.config(state="disabled")
        return
        
    cnt_actual = max(contornos_validos, key=cv2.contourArea)
    resultados = []
    
    for archivo in archivos:
        path = os.path.join(CARPETA_PATRONES, archivo)
        plantilla = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if plantilla is None:
            continue
        try:
            contornos_plantilla, _ = cv2.findContours(plantilla, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contornos_p_validos = [cnt for cnt in contornos_plantilla if cv2.contourArea(cnt) > 20]
            if len(contornos_p_validos) == 0:
                continue
            cnt_plantilla = max(contornos_p_validos, key=cv2.contourArea)
            
            score = cv2.matchShapes(cnt_actual, cnt_plantilla, cv2.CONTOURS_MATCH_I2, 0)
            resultados.append((archivo, score))
        except Exception as e:
            pass
            
    resultados.sort(key=lambda x: x[1])
    
    ComparacionCaja.config(state="normal")
    ComparacionCaja.delete(1.0, tk.END)
    encabezado = f"{'Nombre':<25} {'Diferencia':<10}\n" + "-"*38 + "\n"
    ComparacionCaja.insert(tk.END, encabezado)
    
    for nombre, score in resultados:
        nombre_mostrar = os.path.splitext(nombre)[0].replace("_", " ")
        texto = f"{nombre_mostrar:<25} {score:.5f}\n"
        ComparacionCaja.insert(tk.END, texto)
    ComparacionCaja.config(state="disabled")
    
    if resultados:
        mejor_match = resultados[0][0]
        path_mejor = os.path.join(CARPETA_PATRONES, mejor_match)
        try:
            im_mejor = Image.open(path_mejor)
            im_mejor = im_mejor.resize((311, 241), Image.NEAREST)
            img_mejor = ImageTk.PhotoImage(image=im_mejor)
            canvas_patron.delete("all")
            canvas_patron.create_image(0, 0, anchor=tk.NW, image=img_mejor)
            canvas_patron.image = img_mejor
        except Exception as e:
            pass

# INTERFAZ GRÁFICA
canvas_orig = tk.Canvas(ventana, background=PANEL, width=311, height=241, highlightthickness=1, highlightbackground=ACCENT)
canvas_orig.place(x=40, y=50)

canvas_mask = tk.Canvas(ventana, background=PANEL, width=311, height=241, highlightthickness=1, highlightbackground=ACCENT)
canvas_mask.place(x=410, y=50)

canvas_patron = tk.Canvas(ventana, background=PANEL, width=311, height=241, highlightthickness=1, highlightbackground=ACCENT)
canvas_patron.place(x=780, y=50)

canvas_orig.bind("<ButtonPress-1>", al_presionar_click)
canvas_orig.bind("<Button1-Motion>", al_arrastrar_mouse)
canvas_orig.bind("<ButtonRelease-1>", al_soltar_click)

# Slider desligado de eventos nativos de teclado para evitar doble disparo
SGray = tk.Scale(ventana, from_=0, to=255, resolution=1, orient='horizontal', label="Umbral Gris (Tiempo Real)", bg=BG, fg=FG, troughcolor=ACCENT, highlightthickness=0, command=umbralizar_tiempo_real, takefocus=0)
SGray.set(127)
SGray.place(x=410, y=305, width=311)

# Vincular teclado ÚNICAMENTE a la ventana principal
ventana.bind("<Left>", tecla_presionada)
ventana.bind("<Right>", tecla_presionada)
ventana.bind("<Up>", tecla_presionada)
ventana.bind("<Down>", tecla_presionada)

tk.Label(ventana, text="Paso 1: Seleccionar foto o cámara", bg=BG, fg=FG, font=FONT_BOLD).place(x=40, y=20)
tk.Label(ventana, text="Paso 2: Recorte e Imagen Umbralizada", bg=BG, fg=FG, font=FONT_BOLD).place(x=410, y=20)
tk.Label(ventana, text="Patrón más similar (MatchShape)", bg=BG, fg=FG, font=FONT_BOLD).place(x=780, y=20)

FBotones1 = tk.Frame(ventana, bg=BG)
FBotones1.place(x=40, y=305)

BArchivo = tk.Button(FBotones1, text="Archivo", command=archivo, bg="#89b4fa", fg="#11111b", font=FONT_BOLD, relief="flat", cursor="hand2", width=9)
BArchivo.pack(side="left", padx=2)

BCamara = tk.Button(FBotones1, text="Iniciar Cámara", command=camara, bg="#89b4fa", fg="#11111b", font=FONT_BOLD, relief="flat", cursor="hand2", width=12)
BCamara.pack(side="left", padx=2)

BCapturar = tk.Button(FBotones1, text="Tomar foto", command=Capturar, bg="#a6e3a1", fg="#11111b", font=FONT_BOLD, relief="flat", cursor="hand2", width=9)
BCapturar.pack(side="left", padx=2)

BReset = tk.Button(ventana, text="Revertir Recorte", command=resetear_recorte, bg=ACCENT, fg=FG, font=FONT, relief="flat", cursor="hand2")
BReset.place(x=505, y=370, width=120, height=25)

FGuardar = tk.Frame(ventana, bg=BG)
FGuardar.place(x=410, y=410)

BGuardar = tk.Button(FGuardar, text="Guardar patrón", command=Guardar_Patron, bg="#a6e3a1", fg="#11111b", font=FONT_BOLD, relief="flat", cursor="hand2")
BGuardar.pack(side="left", padx=(0, 5))

EntradaNombre = tk.Entry(FGuardar, bg=PANEL, fg=FG, font=FONT, insertbackground=FG, relief="flat", width=10)
EntradaNombre.insert(0, "nombre")
EntradaNombre.pack(side="left", padx=2)

EntradaNombre.bind("<Button-1>", lambda e: EntradaNombre.focus_set())

VariableTipo = tk.StringVar(value="Macho")
RadioMacho = tk.Radiobutton(FGuardar, text="Macho", variable=VariableTipo, value="Macho", bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG, activeforeground=FG)
RadioHembra = tk.Radiobutton(FGuardar, text="Hembra", variable=VariableTipo, value="Hembra", bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG, activeforeground=FG)
RadioMacho.pack(side="left", padx=2)
RadioHembra.pack(side="left", padx=2)

tk.Label(ventana, text="Comparación en tiempo real (Menor = Mayor semejanza)", bg=BG, fg="#f9e2af", font=FONT_BOLD).place(x=780, y=305)
ComparacionCaja = tk.Text(ventana, bg=PANEL, fg=FG, font=("Consolas", 9), state="disabled", relief="flat")
ComparacionCaja.place(x=780, y=330, width=311, height=250)

ventana.focus_set()

ventana.mainloop()