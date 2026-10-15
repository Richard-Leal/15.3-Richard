import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import imutils
import cv2
import os
from math import copysign, log10

CARPETA_PATRONES = "patrones_guardados"
if not os.path.exists(CARPETA_PATRONES):
    os.makedirs(CARPETA_PATRONES)

BG = "#1a1a2e"
PANEL = "#16213e"
ACCENT = "#0F3460"
GREEN = "#2d6a4f"
BLUE = "#1d3557"
RED = "#e63946"
FG = "#e0e0e0"
FONT = ("Consolas", 9)
STYLE_BTN = {"font": ("Consolas", 9, "bold"), "relief": "flat", "cursor": "hand2"}

# Variables globales
camara_activa = False
valor = 0  # 0: imagen cargada, 1: imagen de cámara, 2: imagen capturada
imageToShow = None
Captura = None
capture = None

ventana = tk.Tk()
ventana.geometry("1500x700")
ventana.title("Detector de objetos")
ventana.resizable(False, False)

def mostrar(label, img_np, bgr=False, w=300, h=240):
    if bgr:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    img_np = cv2.resize(img_np, (w, h))
    pil = Image.fromarray(img_np)
    tk_img = ImageTk.PhotoImage(image=pil)
    label.configure(image=tk_img)
    label.image = tk_img

def imagenBase():
    return imageToShow if valor == 0 else Captura

def archivo():
    global imageToShow, valor
    path = filedialog.askopenfilename(
        filetypes=[("Imagen", "*.jpg *.jpeg *.png")]
    )
    if not path:
        return
    bgr = cv2.imread(path)
    if bgr is None:
        messagebox.showerror("Error", "No se pudo leer el archivo")
        return
    mostrar(LImagen, bgr, bgr=True)
    imageToShow = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    mostrar(LImagen2, imageToShow)
    valor = 0

def iniciar():
    if not camara_activa or capture is None:
        return
    ret, frame = capture.read()
    if ret:
        mostrar(LImagen, frame, bgr=True)
        LImagen.after(30, iniciar)

def camara():
    global capture, camara_activa
    if not camara_activa:
        capture = cv2.VideoCapture(1)
        if not capture.isOpened():
            messagebox.showerror("Error", "No se pudo abrir la cámara")
            return
        camara_activa = True
        BCamara.configure(text="Detener")
        iniciar()
    else:
        camara_activa = False
        capture.release()
        BCamara.configure(text="Camara")
        LImagen.configure(image="")

def Capturar():
    global valor, Captura
    if capture is None or not capture.isOpened():
        messagebox.showwarning("Aviso", "Primero activa la cámara")
        return
    ret, frame = capture.read()
    if not ret:
        messagebox.showerror("Error", "No se pudo capturar fotograma")
        return
    frame = imutils.resize(imutils.resize(frame, width=300), height=240)
    Captura = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mostrar(LImagen2, Captura)
    valor = 2

def actualizar_area_recorte(_=None):
    base = imagenBase()
    if base is None:
        return
    x, y, w, h = SX.get(), SY.get(), SW.get(), SH.get()
    mascara_negra = np.zeros_like(base)
    mascara_negra[y:h+y, x:w+x] = 255
    mostrar(LImagen2, cv2.bitwise_and(base, mascara_negra))

def recortar_imagen():
    base = imagenBase()
    if base is None:
        return None
    x = SX.get(); y = SY.get()
    w = SW.get(); h = SH.get()
    recortada = base[y:y+h, x:x+w]
    if recortada.size == 0:
        return None
    mostrar(LImagen2, recortada, w=recortada.shape[1], h=recortada.shape[0])
    return recortada

def umbralizar():
    recortada = recortar_imagen()
    if recortada is None:
        return None
    umb = int(SGray.get())
    binaria = cv2.inRange(recortada, umb, 255)
    mostrar(LImagenUmbral, binaria)
    return binaria

def Guardar_patron():
    binaria = umbralizar()
    if binaria is None:
        messagebox.showwarning("Aviso", "Primero carga o captura una imagen.")
        return
    nombre = EntradaNombre.get().strip().replace(" ", "_") or "patron"
    ruta = os.path.join(CARPETA_PATRONES, f"{nombre}.png")
    if cv2.imwrite(ruta, binaria):
        messagebox.showinfo("Guardado",
            f"Patrón guardado correctamente en:\n{ruta}\n"
            f"Tamaño: {binaria.shape[1]}x{binaria.shape[0]} px")
    else:
        messagebox.showerror("Error", f"No se pudo guardar en:\n{ruta}")

def obtener_hu(imagen_bin):
    cnts, _ = cv2.findContours(imagen_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    cnt = max(cnts, key=cv2.contourArea)
    moments = cv2.moments(cnt)
    if moments['m00'] == 0:  # Evitar división por cero
        return None
    hu = cv2.HuMoments(moments).flatten()
    return [
        -copysign(1.0, v) * log10(abs(v)) if v != 0 else 0.0
        for v in hu
    ]

def contorno_mayor(imagen_bin):
    cnts, _ = cv2.findContours(imagen_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(cnts, key=cv2.contourArea) if cnts else None

def rotar_template(template, angulo):
    h, w = template.shape[:2]
    cx, cy = w // 2, h // 2
    M = cv2.getRotationMatrix2D((cx, cy), angulo, 1.0)
    cos_a, sin_a = abs(M[0, 0]), abs(M[0, 1])
    new_w, new_h = int(h * sin_a + w * cos_a), int(h * cos_a + w * sin_a)
    M[0, 2] += (new_w / 2) - cx
    M[1, 2] += (new_h / 2) - cy
    return cv2.warpAffine(template, M, (new_w, new_h), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def escribir(caja, texto):
    caja.configure(state="normal")
    caja.delete("1.0", tk.END)
    caja.insert(tk.END, texto)
    caja.configure(state="disabled")

def comparar_todo():
    base = imagenBase()
    if base is None:
        messagebox.showwarning("Aviso", "Primero carga o captura una imagen")
        return
    archivos = [f for f in os.listdir(CARPETA_PATRONES)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not archivos:
        messagebox.showwarning("Aviso", "No hay patrones en la carpeta")
        return

    paso = int(SAngulo.get())
    umb = int(SGray.get())
    img_bin = cv2.inRange(base, umb, 255)
    ih, iw = img_bin.shape[:2]
    cnt_actual = contorno_mayor(img_bin)
    hu_actual = obtener_hu(img_bin)

    res_tm, res_shapes, res_hu = [], [], []
    mejor_tm_val = -1.0
    mejor_tm_img = None

    for archivo in archivos:
        path = os.path.join(CARPETA_PATRONES, archivo)
        patron = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if patron is None:
            continue

        nombre = os.path.splitext(archivo)[0].replace("_", " ")
        best_v, best_tmpl, best_loc = -1.0, None, (0, 0)

        for angulo in range(0, 360, paso):
            rot = rotar_template(patron, angulo)
            th, tw = rot.shape[:2]
            if th > ih or tw > iw:
                continue
            for t in (rot, cv2.bitwise_not(rot)):
                r = cv2.matchTemplate(img_bin, t, cv2.TM_CCOEFF_NORMED)
                _, v, _, loc = cv2.minMaxLoc(r)
                if v > best_v:
                    best_v, best_tmpl, best_loc = v, t, loc

        sim = best_v * 100 if best_v >= 0 else 0.0
        res_tm.append((nombre, sim))

        if best_v > mejor_tm_val and best_tmpl is not None:
            mejor_tm_val = best_v
            th2, tw2 = best_tmpl.shape[:2]
            mx, my = best_loc
            vis = cv2.cvtColor(img_bin, cv2.COLOR_GRAY2RGB)
            cv2.rectangle(vis, (mx, my), (mx+tw2, my+th2), (255, 220, 0), 2)
            mejor_tm_img = vis

        # matchShapes
        cnt_p = contorno_mayor(patron)
        score = (cv2.matchShapes(cnt_actual, cnt_p, cv2.CONTOURS_MATCH_I2, 0)
                 if cnt_actual is not None and cnt_p is not None
                 else float("inf"))
        res_shapes.append((nombre, score))

        # Momentos Hu
        hu_p = obtener_hu(patron)
        dist = (float(np.linalg.norm(np.array(hu_actual) - np.array(hu_p)))
                if hu_actual and hu_p else float("inf"))
        res_hu.append((nombre, dist, hu_p))

    res_tm.sort(key=lambda x: x[1], reverse=True)
    res_shapes.sort(key=lambda x: x[1])
    res_hu.sort(key=lambda x: x[1])

    if mejor_tm_img is not None:
        mostrar(LImagenResultado, mejor_tm_img, w=300, h=240)

    # Template matching
    txt = f"{'Patrón': <22} {'Similitud':>9}\n" + "-"*33 + "\n"
    for nom, sim in res_tm:
        marca = " <" if nom == res_tm[0][0] else ""
        txt += f"{nom: <22} {sim:>7.2f}%{marca}\n"
    escribir(CajaTemplate, txt)

    # matchShapes
    txt = f"{'Patrón': <22} {'Diferencia':>10}\n" + "-"*34 + "\n"
    for nom, sc in res_shapes:
        marca = " <" if nom == res_shapes[0][0] else ""
        txt += f"{nom: <22} {sc:>10.5f}{marca}\n"
    escribir(CajaShapes, txt)

    # Momentos Hu
    txt = f"{'Patrón': <20} {'Dist':>6} Calidad\n" + "-"*40 + "\n"
    for nom, d, _ in res_hu:
        marca = " <" if nom == res_hu[0][0] else ""
        if d == float("inf"):
            cal = "sin forma"
        elif d < 0.5:
            cal = "muy similar"
        elif d < 1.5:
            cal = "parecido"
        else:
            cal = "diferente"
        txt += f"{nom:<20} {d:>6.3f} {cal}{marca}\n"
    escribir(CajaHu, txt)

# Frames
F0 = tk.Frame(ventana, bg=BG)
F1 = tk.Frame(ventana, bg=BG)
F2 = tk.Frame(ventana, bg=BG)
F3 = tk.Frame(ventana, bg=BG)

F0.grid(row=0, column=0, padx=6, pady=6, sticky="n")
F1.grid(row=0, column=1, padx=6, pady=6, sticky="n")
F2.grid(row=0, column=2, padx=6, pady=6, sticky="n")
F3.grid(row=0, column=3, padx=6, pady=6, sticky="n")

# Controles F0 (Imagen original)
SX = tk.Scale(F0, from_=0, to=300, orient="horizontal", label="X",
              bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0,
              command=actualizar_area_recorte)
SX.pack(fill="x")

FImagen = tk.Frame(F0, bg=BG)
FImagen.pack()

SY = tk.Scale(FImagen, from_=0, to=240, orient="vertical", label="Y",
              bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0,
              command=actualizar_area_recorte)
SY.pack(side="left")

FContenedor = tk.Frame(FImagen, width=300, height=240, bg=PANEL)
FContenedor.pack_propagate(False)
FContenedor.pack(side="left")

LImagen = tk.Label(FContenedor, bg=PANEL)
LImagen.pack(expand=True, fill="both")

SH = tk.Scale(FImagen, from_=0, to=240, orient="vertical", label="H",
              bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0,
              command=actualizar_area_recorte)
SH.set(240)
SH.pack(side="left")

SW = tk.Scale(F0, from_=0, to=300, orient="horizontal", label="W",
              bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0,
              command=actualizar_area_recorte)
SW.set(300)
SW.pack(fill="x")

FBotones = tk.Frame(F0, bg=BG)
FBotones.pack()
BArchivo = tk.Button(FBotones, text="Archivo", command=archivo, **STYLE_BTN)
BArchivo.pack(side="left", padx=2, pady=1)

BCamara = tk.Button(FBotones, text="Cámara", command=camara, **STYLE_BTN)
BCamara.pack(side="left", padx=2, pady=1)

BCapturar = tk.Button(FBotones, text="Tomar foto", command=Capturar, **STYLE_BTN)
BCapturar.pack(side="left", padx=2, pady=1)

# Controles F1 (Recorte / umbral)
FContenedor2 = tk.Frame(F1, width=300, height=240, bg=PANEL)
FContenedor2.pack_propagate(False)
FContenedor2.pack()

LImagen2 = tk.Label(FContenedor2, bg=PANEL)
LImagen2.pack(expand=True, fill="both")

tk.Label(F1, text="Recorte / umbral", bg=BG, fg=FG, font=FONT).pack()

SGray = tk.Scale(F1, from_=0, to=255, orient="horizontal", label="Umbral gris",
                 bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0)
SGray.pack(fill="x")

SAngulo = tk.Scale(F1, from_=0, to=90, orient="horizontal", label="Paso angular",
                   bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0)
SAngulo.set(5)
SAngulo.pack(fill="x")

BRecortar = tk.Button(F1, text="Recortar", command=recortar_imagen, **STYLE_BTN)
BRecortar.pack(fill="x", pady=1)

# Controles F2 (Imagen umbralizada)
FContenedor3 = tk.Frame(F2, width=300, height=240, bg=PANEL)
FContenedor3.pack_propagate(False)
FContenedor3.pack()

LImagenUmbral = tk.Label(FContenedor3, bg=PANEL)
LImagenUmbral.pack(expand=True, fill="both")

tk.Label(F2, text="Imagen umbralizada", bg=BG, fg=FG, font=FONT).pack()

BUmbral = tk.Button(F2, text="Umbralizar", command=umbralizar,
                    bg=BLUE, fg=FG, **STYLE_BTN)
BUmbral.pack(fill="x", pady=1)

tk.Label(F2, text="Nombre patrón:", bg=BG, fg=FG, font=FONT).pack(anchor="w")

EntradaNombre = tk.Entry(F2, bg=PANEL, fg=FG, font=FONT,
                         insertbackground=FG, relief="flat")
EntradaNombre.insert(0, "patron")
EntradaNombre.pack(fill="x", pady=1)

BGuardar = tk.Button(F2, text="Guardar patrón", command=Guardar_patron,
                     bg=GREEN, fg="white", font=("Arial", 9, "bold"))
BGuardar.pack(fill="x", pady=1)

# Controles F3 (Resultados)
FContenedor4 = tk.Frame(F3, width=300, height=240, bg=PANEL)
FContenedor4.pack_propagate(False)
FContenedor4.pack()

LImagenResultado = tk.Label(FContenedor4, bg=PANEL)
LImagenResultado.pack(expand=True, fill="both")

tk.Label(F3, text="Mejor coincidencia", bg=BG, fg=FG, font=FONT).pack()

BCompararCamara = tk.Button(F3, text="Comparar con todos los patrones",
                            command=comparar_todo,
                            bg="#457b9d", fg="white", font=("Arial", 9, "bold"))
BCompararCamara.pack(fill="x", pady=4)

# Cajas de texto de resultados
tk.Label(ventana, text="Template matching", bg=BG, fg="#ffd166",
         font=("Consolas", 9, "bold")).grid(row=1, column=0, sticky="w", padx=6)
CajaTemplate = tk.Text(ventana, bg=PANEL, fg=FG, font=("Consolas", 10),
                       state="disabled", relief="flat", width=40, height=12)
CajaTemplate.grid(row=2, column=0, padx=6, pady=4, sticky="nsew")

tk.Label(ventana, text="matchShapes", bg=BG, fg="#06d6a0",
         font=("Consolas", 9, "bold")).grid(row=1, column=1, sticky="w", padx=6)
CajaShapes = tk.Text(ventana, bg=PANEL, fg=FG, font=("Consolas", 10),
                     state="disabled", relief="flat", width=40, height=12)
CajaShapes.grid(row=2, column=1, padx=6, pady=4, sticky="nsew")

tk.Label(ventana, text="Momentos Hu", bg=BG, fg="#ef476f",
         font=("Consolas", 9, "bold")).grid(row=1, column=2, sticky="w", padx=6)
CajaHu = tk.Text(ventana, bg=PANEL, fg=FG, font=("Consolas", 10),
                 state="disabled", relief="flat", width=40, height=12)
CajaHu.grid(row=2, column=2, columnspan=2, padx=6, pady=4, sticky="nsew")

for c in range(4):
    ventana.columnconfigure(c, weight=1)

ventana.rowconfigure(0, weight=1)
ventana.rowconfigure(2, weight=1)

ventana.update_idletasks()
ventana.mainloop()