import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import numpy as np
import cv2
import os
from math import copysign, log10

CARPETA_PATRONES = "patrones_guardados"
if not os.path.exists(CARPETA_PATRONES):
    os.makedirs(CARPETA_PATRONES)

# Colores UI (Catppuccin / Dashboard moderno)
BG = "#1e1e2e"
PANEL = "#252538"
ACCENT = "#313244"
FG = "#cdd6f4"
BLUE = "#89b4fa"
GREEN = "#a6e3a1"
YELLOW = "#f9e2af"
RED = "#f38ba8"
FONT = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_TITLE = ("Segoe UI", 10, "bold")

STYLE_BTN = {"font": FONT_BOLD, "relief": "flat", "cursor": "hand2"}

imageToShow = None      # Imagen BGR original cargada/capturada
Captura = None
capture = None
camara_activa = False   # Indica si la cámara está activa
valor = 0               # 0: Archivo, 2: Cámara
recorte_activo = None   # Matriz OpenCV escala de grises recortada
historial_recortes = [] # Pila para deshacer recortes (Z)
patron_seleccionado = None # Patrón activo seleccionado por el usuario

start_x, start_y = None, None
end_x, end_y = None, None
rect_id = None
offset_x, offset_y = 0, 0

ventana = tk.Tk()
ventana.geometry("1320x740")
ventana.title("Detector de Objetos Integrado - Paso 15.3")
ventana.configure(bg=BG)
ventana.resizable(False, False)

def mostrar(widget, img_np, bgr=False, w=280, h=210):
    if bgr:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    img_np = cv2.resize(img_np, (w, h), interpolation=cv2.INTER_NEAREST)
    pil = Image.fromarray(img_np)
    tk_img = ImageTk.PhotoImage(image=pil)
    
    if isinstance(widget, tk.Canvas):
        widget.delete("all")
        off_x = (w - img_np.shape[1]) // 2
        off_y = (h - img_np.shape[0]) // 2
        widget.create_image(off_x, off_y, anchor=tk.NW, image=tk_img)
        widget.image = tk_img
    else:
        widget.configure(image=tk_img)
        widget.image = tk_img

def imagenBase():
    return imageToShow if valor == 0 else Captura

def mostrar_imagen_original():
    global offset_x, offset_y
    base = imagenBase()
    if base is not None:
        h_img, w_img = base.shape[:2]
        offset_x = (280 - w_img) // 2
        offset_y = (210 - h_img) // 2
        
        im = cv2.cvtColor(base, cv2.COLOR_BGR2RGB) if base.ndim == 3 else base
        pil = Image.fromarray(im)
        tk_img = ImageTk.PhotoImage(image=pil)
        
        LImagen.delete("all")
        LImagen.create_image(offset_x, offset_y, anchor=tk.NW, image=tk_img)
        LImagen.image = tk_img

def archivo():
    global imageToShow, valor, recorte_activo, historial_recortes, camara_activa
    if camara_activa:
        camara()
        
    path = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.bmp")])
    if not path:
        return
    bgr = cv2.imread(path)
    if bgr is None:
        messagebox.showerror("Error", "No se pudo leer el archivo de imagen")
        return
    
    h_bgr, w_bgr = bgr.shape[:2]
    prop = min(280 / w_bgr, 210 / h_bgr)
    new_w, new_h = max(1, int(w_bgr * prop)), max(1, int(h_bgr * prop))
    img_resized = cv2.resize(bgr, (new_w, new_h))
        
    imageToShow = img_resized.copy()
    recorte_activo = cv2.cvtColor(imageToShow, cv2.COLOR_BGR2GRAY)
    historial_recortes = [recorte_activo.copy()]
    valor = 0
    mostrar_imagen_original()
    umbralizar()

def iniciar():
    if not camara_activa or capture is None:
        return
    ret, frame = capture.read()
    if ret:
        h_f, w_f = frame.shape[:2]
        prop = min(280 / w_f, 210 / h_f)
        new_w, new_h = max(1, int(w_f * prop)), max(1, int(h_f * prop))
        frame_resized = cv2.resize(frame, (new_w, new_h))
        
        im = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(im)
        tk_img = ImageTk.PhotoImage(image=pil)
        
        off_x = (280 - new_w) // 2
        off_y = (210 - new_h) // 2
        LImagen.delete("all")
        LImagen.create_image(off_x, off_y, anchor=tk.NW, image=tk_img)
        LImagen.image = tk_img
        
        LImagen.after(30, iniciar)

def camara():
    global capture, camara_activa
    if not camara_activa:
        cam_found = False
        for idx in (0, 1, 2):
            cap_try = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == 'nt' else cv2.VideoCapture(idx)
            if not cap_try.isOpened():
                cap_try = cv2.VideoCapture(idx)
            
            if cap_try.isOpened():
                ret, _ = cap_try.read()
                if ret:
                    capture = cap_try
                    cam_found = True
                    break
                else:
                    cap_try.release()
        
        if not cam_found or capture is None or not capture.isOpened():
            messagebox.showerror("Error", "No se pudo acceder a ninguna webcam conectada.")
            return

        camara_activa = True
        if 'BCamara' in globals():
            BCamara.configure(text="Detener")
        iniciar()
    else:
        camara_activa = False
        if capture is not None:
            capture.release()
            capture = None
        if 'BCamara' in globals():
            BCamara.configure(text="Cámara (C)")
        LImagen.delete("all")

def Capturar():
    global valor, Captura, recorte_activo, historial_recortes
    if capture is None or not capture.isOpened():
        messagebox.showwarning("Aviso", "Primero debes activar la cámara web (Cámara).")
        return
    ret, frame = capture.read()
    if not ret:
        messagebox.showerror("Error", "No se pudo obtener el fotograma de la cámara")
        return
    h_f, w_f = frame.shape[:2]
    prop = min(280 / w_f, 210 / h_f)
    new_w, new_h = max(1, int(w_f * prop)), max(1, int(h_f * prop))
    frame_resized = cv2.resize(frame, (new_w, new_h))
    
    Captura = frame_resized.copy()
    recorte_activo = cv2.cvtColor(Captura, cv2.COLOR_BGR2GRAY)
    historial_recortes = [recorte_activo.copy()]
    valor = 2
    
    camara()
    mostrar_imagen_original()
    umbralizar()

def aplicar_recorte():
    global recorte_activo, start_x, start_y, end_x, end_y, rect_id
    base = imagenBase()
    if base is None or start_x is None or end_x is None:
        return
    
    h_img, w_img = base.shape[:2]
    x1_c, x2_c = min(start_x, end_x), max(start_x, end_x)
    y1_c, y2_c = min(start_y, end_y), max(start_y, end_y)

    x1 = int(np.clip(x1_c - offset_x, 0, w_img))
    x2 = int(np.clip(x2_c - offset_x, 0, w_img))
    y1 = int(np.clip(y1_c - offset_y, 0, h_img))
    y2 = int(np.clip(y2_c - offset_y, 0, h_img))

    if (x2 - x1) > 5 and (y2 - y1) > 5:
        base_gray = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
        recorte_activo = base_gray[y1:y2, x1:x2]
        historial_recortes.append(recorte_activo.copy())
        if rect_id is not None:
            LImagen.delete(rect_id)
            rect_id = None
        start_x, start_y, end_x, end_y = None, None, None, None
        umbralizar()

def retroceder_recorte(event=None):
    global recorte_activo, historial_recortes, rect_id
    if len(historial_recortes) > 1:
        historial_recortes.pop()
        recorte_activo = historial_recortes[-1].copy()
    elif len(historial_recortes) == 1:
        recorte_activo = historial_recortes[0].copy()
    
    if rect_id is not None:
        LImagen.delete(rect_id)
        rect_id = None
    umbralizar()

def resetear_recorte():
    global recorte_activo, historial_recortes, rect_id
    base = imagenBase()
    if base is not None:
        recorte_activo = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
        historial_recortes = [recorte_activo.copy()]
        if rect_id is not None:
            LImagen.delete(rect_id)
            rect_id = None
        umbralizar()

def al_presionar_click(event):
    global start_x, start_y, end_x, end_y, rect_id
    if imagenBase() is None:
        return
    start_x, start_y = event.x, event.y
    end_x, end_y = event.x, event.y
    if rect_id is not None:
        LImagen.delete(rect_id)
    rect_id = LImagen.create_rectangle(start_x, start_y, start_x, start_y, outline=YELLOW, width=2, dash=(4, 4))

def al_arrastrar_mouse(event):
    global end_x, end_y, rect_id
    if rect_id is not None and imagenBase() is not None:
        end_x, end_y = event.x, event.y
        LImagen.coords(rect_id, start_x, start_y, end_x, end_y)

def al_soltar_click(event):
    global end_x, end_y
    if start_x is not None:
        end_x, end_y = event.x, event.y
        aplicar_recorte()

def al_presionar_tecla(event):
    # Si el usuario está escribiendo dentro de la caja de nombre, ignorar atajos del teclado
    if ventana.focus_get() == EntradaNombre:
        return

    key = event.keysym.lower()
    if key in ('r', 'r'):
        aplicar_recorte()
    elif key in ('z', 'z'):
        retroceder_recorte()
    elif key in ('t', 't'):
        Capturar()
    elif key in ('c', 'c'):
        camara()
    elif key == 'up':
        SGray.set(min(255, SGray.get() + 1))
    elif key == 'down':
        SGray.set(max(0, SGray.get() - 1))
    elif key == 'right':
        SAngulo.set(min(90, SAngulo.get() + 1))
    elif key == 'left':
        SAngulo.set(max(1, SAngulo.get() - 1))

ventana.bind("<Key>", al_presionar_tecla)

def umbralizar(val=None):
    global recorte_activo
    if recorte_activo is None:
        return None
    
    mostrar(LImagen2, recorte_activo)
    umb = int(SGray.get())
    binaria = cv2.inRange(recorte_activo, umb, 255)
    mostrar(LImagenUmbral, binaria)
    
    comparar_todo()
    return binaria

def Guardar_patron():
    binaria = umbralizar()
    if binaria is None:
        messagebox.showwarning("Aviso", "No hay imagen recortada/umbralizada para guardar.")
        return
    nombre = EntradaNombre.get().strip().replace(" ", "_") or "patron"
    ruta = os.path.join(CARPETA_PATRONES, f"{nombre}.png")
    if cv2.imwrite(ruta, binaria):
        messagebox.showinfo("Guardado", f"Patrón guardado exitosamente:\n{ruta}")
        comparar_todo()
    else:
        messagebox.showerror("Error", f"No se pudo guardar la imagen en:\n{ruta}")

def obtener_hu(imagen_bin):
    cnts, _ = cv2.findContours(imagen_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    cnt = max(cnts, key=cv2.contourArea)
    moments = cv2.moments(cnt)
    if moments['m00'] == 0:
        return None
    hu = cv2.HuMoments(moments).flatten()
    return [-copysign(1.0, v) * log10(abs(v)) if v != 0 else 0.0 for v in hu]

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

def actualizar_treeview(tree, lista_datos):
    for item in tree.get_children():
        tree.delete(item)
    for row in lista_datos:
        tree.insert("", "end", values=row)

def al_seleccionar_patron(event):
    global patron_seleccionado
    widget = event.widget
    selected_items = widget.selection()
    if selected_items:
        item = widget.item(selected_items[0])
        patron_seleccionado = item['values'][0]
        comparar_todo()

def comparar_todo():
    global patron_seleccionado
    base = imagenBase()
    if base is None:
        return
    archivos = [f for f in os.listdir(CARPETA_PATRONES) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not archivos:
        actualizar_treeview(TablaTemplate, [])
        actualizar_treeview(TablaShapes, [])
        actualizar_treeview(TablaHu, [])
        return

    umb = int(SGray.get())
    paso = max(1, int(SAngulo.get()))
    
    img_bin = cv2.inRange(recorte_activo, umb, 255) if recorte_activo is not None else cv2.inRange(cv2.cvtColor(base, cv2.COLOR_BGR2GRAY), umb, 255)
    ih, iw = img_bin.shape[:2]
    
    cnt_actual = contorno_mayor(img_bin)
    hu_actual = obtener_hu(img_bin)
    
    res_tm, res_shapes, res_hu = [], [], []
    mejor_tm_val = -1.0
    mejor_tm_img = None
    info_patron_activo = ""

    if not patron_seleccionado and archivos:
        patron_seleccionado = os.path.splitext(archivos[0])[0].replace("_", " ")

    for archivo_patron in archivos:
        path = os.path.join(CARPETA_PATRONES, archivo_patron)
        patron = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if patron is None:
            continue
        
        nombre = os.path.splitext(archivo_patron)[0].replace("_", " ")
        es_el_seleccionado = (nombre.strip().lower() == str(patron_seleccionado).strip().lower())
        
        best_v, best_tmpl, best_loc = -1.0, None, (0, 0)
        if es_el_seleccionado or len(archivos) <= 3:
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
        else:
            th, tw = patron.shape[:2]
            if th <= ih and tw <= iw:
                r = cv2.matchTemplate(img_bin, patron, cv2.TM_CCOEFF_NORMED)
                _, best_v, _, best_loc = cv2.minMaxLoc(r)
                best_tmpl = patron

        sim = best_v * 100 if best_v >= 0 else 0.0
        res_tm.append((nombre, f"{sim:.2f}%"))
        
        if es_el_seleccionado or (mejor_tm_img is None and best_v > mejor_tm_val):
            if best_tmpl is not None:
                mejor_tm_val = best_v
                th2, tw2 = best_tmpl.shape[:2]
                mx, my = best_loc
                vis = cv2.cvtColor(img_bin, cv2.COLOR_GRAY2RGB)
                cv2.rectangle(vis, (mx, my), (mx + tw2, my + th2), (255, 220, 0), 2)
                mejor_tm_img = vis
                info_patron_activo = f"🎯 Evaluando: {nombre}\nSimilitud: {sim:.2f}%"
            
        cnt_p = contorno_mayor(patron)
        score = cv2.matchShapes(cnt_actual, cnt_p, cv2.CONTOURS_MATCH_I2, 0) if cnt_actual is not None and cnt_p is not None else float("inf")
        res_shapes.append((nombre, f"{score:.5f}" if score != float("inf") else "N/A"))
        
        hu_p = obtener_hu(patron)
        dist = float(np.linalg.norm(np.array(hu_actual) - np.array(hu_p))) if hu_actual and hu_p else float("inf")
        cal = "Muy Similar" if dist < 0.5 else ("Parecido" if dist < 1.5 else "Diferente")
        res_hu.append((nombre, f"{dist:.3f}" if dist != float("inf") else "N/A", cal if dist != float("inf") else "Sin Datos"))

    res_tm.sort(key=lambda x: float(x[1].replace("%", "")), reverse=True)
    res_shapes.sort(key=lambda x: float(x[1]) if x[1] != "N/A" else 9999)
    res_hu.sort(key=lambda x: float(x[1]) if x[1] != "N/A" else 9999)

    if mejor_tm_img is not None:
        mostrar(LImagenResultado, mejor_tm_img, w=280, h=210)
        lbl_info.configure(text=info_patron_activo, fg=BLUE)

    actualizar_treeview(TablaTemplate, res_tm)
    actualizar_treeview(TablaShapes, res_shapes)
    actualizar_treeview(TablaHu, res_hu)

# Estilos seguros TTK
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background=BG, foreground=FG, fieldbackground=BG, rowheight=22, font=("Consolas", 9), borderwidth=0)
style.configure("Treeview.Heading", background=ACCENT, foreground=FG, font=FONT_BOLD, borderwidth=1)
style.map("Treeview", background=[("selected", BLUE)], foreground=[("selected", "#11111b")])

grid_container = tk.Frame(ventana, bg=BG)
grid_container.pack(expand=True, fill="both", padx=16, pady=12)

grid_container.columnconfigure((0, 1, 2, 3), weight=1, uniform="col")
grid_container.rowconfigure(0, weight=0)
grid_container.rowconfigure(1, weight=1)

for i in range(4):
    card = tk.Frame(grid_container, bg=PANEL, highlightthickness=1, highlightbackground=ACCENT)
    card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
    
    if i == 0:
        tk.Label(card, text="1. Imagen Entrada", bg=PANEL, fg=FG, font=FONT_TITLE).pack(pady=(8, 4))
        FCont = tk.Frame(card, width=280, height=210, bg=BG)
        FCont.pack_propagate(False)
        FCont.pack(pady=2)
        
        LImagen = tk.Canvas(FCont, bg=BG, highlightthickness=0)
        LImagen.pack(expand=True, fill="both")
        LImagen.bind("<ButtonPress-1>", al_presionar_click)
        LImagen.bind("<B1-Motion>", al_arrastrar_mouse)
        LImagen.bind("<ButtonRelease-1>", al_soltar_click)
        
        FBot = tk.Frame(card, bg=PANEL)
        FBot.pack(pady=4)
        BArchivo = tk.Button(FBot, text="Archivo", command=archivo, bg=BLUE, fg="#11111b", **STYLE_BTN, width=8)
        BArchivo.pack(side="left", padx=3)
        BCamara = tk.Button(FBot, text="Cámara (C)", command=camara, bg=BLUE, fg="#11111b", **STYLE_BTN, width=8)
        BCamara.pack(side="left", padx=3)
        BCapturar = tk.Button(FBot, text="Foto (T)", command=Capturar, bg=GREEN, fg="#11111b", **STYLE_BTN, width=9)
        BCapturar.pack(side="left", padx=3)
        
        FBotRecorte = tk.Frame(card, bg=PANEL)
        FBotRecorte.pack(fill="x", padx=8, pady=(2, 6))
        FBotRecorte.columnconfigure((0, 1), weight=1, uniform="btn_col")
        
        tk.Button(FBotRecorte, text="Atrás (Z)", command=retroceder_recorte, bg=RED, fg="#11111b", **STYLE_BTN).grid(row=0, column=0, padx=2, sticky="ew")
        tk.Button(FBotRecorte, text="Reset", command=resetear_recorte, bg=ACCENT, fg=FG, **STYLE_BTN).grid(row=0, column=1, padx=2, sticky="ew")

    elif i == 1:
        tk.Label(card, text="2. Recorte Seleccionado", bg=PANEL, fg=FG, font=FONT_TITLE).pack(pady=(8, 4))
        FCont = tk.Frame(card, width=280, height=210, bg=BG)
        FCont.pack_propagate(False)
        FCont.pack(pady=2)
        
        LImagen2 = tk.Label(FCont, bg=BG)
        LImagen2.pack(expand=True, fill="both")
        
        SGray = tk.Scale(card, from_=0, to=255, resolution=1, orient="horizontal", label="Umbral Gris (▲/▼)", bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0, command=umbralizar, takefocus=1)
        SGray.set(127)
        SGray.pack(fill="x", padx=8, pady=2)
        
        SAngulo = tk.Scale(card, from_=1, to=90, orient="horizontal", label="Paso Angular (◄/►)", bg=PANEL, fg=FG, troughcolor=ACCENT, highlightthickness=0, command=umbralizar, takefocus=1)
        SAngulo.set(5)
        SAngulo.pack(fill="x", padx=8, pady=(0, 6))

    elif i == 2:
        tk.Label(card, text="3. Imagen Umbralizada", bg=PANEL, fg=FG, font=FONT_TITLE).pack(pady=(8, 4))
        FCont = tk.Frame(card, width=280, height=210, bg=BG)
        FCont.pack_propagate(False)
        FCont.pack(pady=2)
        
        LImagenUmbral = tk.Label(FCont, bg=BG)
        LImagenUmbral.pack(expand=True, fill="both")
        
        FNombre = tk.Frame(card, bg=PANEL)
        FNombre.pack(fill="x", padx=8, pady=5)
        tk.Label(FNombre, text="Nombre:", bg=PANEL, fg=FG, font=FONT_BOLD).pack(side="left")
        EntradaNombre = tk.Entry(FNombre, bg=BG, fg=FG, font=FONT, insertbackground=FG, relief="flat")
        EntradaNombre.insert(0, "patron")
        EntradaNombre.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        tk.Button(card, text="Guardar Patrón", command=Guardar_patron, bg=GREEN, fg="#11111b", **STYLE_BTN).pack(fill="x", padx=8, pady=(0, 6))

    elif i == 3:
        tk.Label(card, text="4. Mejor Coincidencia", bg=PANEL, fg=FG, font=FONT_TITLE).pack(pady=(8, 4))
        FCont = tk.Frame(card, width=280, height=210, bg=BG)
        FCont.pack_propagate(False)
        FCont.pack(pady=2)
        
        LImagenResultado = tk.Label(FCont, bg=BG)
        LImagenResultado.pack(expand=True, fill="both")
        
        lbl_info = tk.Label(card, text="Haz clic en cualquier patrón de la tabla\npara compararlo en tiempo real", bg=PANEL, fg=BLUE, font=("Segoe UI", 9, "bold"))
        lbl_info.pack(fill="both", expand=True, padx=8, pady=8)

for j in range(3):
    card_bot = tk.Frame(grid_container, bg=PANEL, highlightthickness=1, highlightbackground=ACCENT)
    card_bot.grid(row=1, column=j if j < 2 else 2, columnspan=2 if j == 2 else 1, padx=6, pady=6, sticky="nsew")
    
    if j == 0:
        tk.Label(card_bot, text="Template Matching", bg=PANEL, fg=YELLOW, font=FONT_TITLE).pack(anchor="w", padx=8, pady=(6, 2))
        TablaTemplate = ttk.Treeview(card_bot, columns=("Patrón", "Similitud"), show="headings", height=6)
        TablaTemplate.heading("Patrón", text="Patrón")
        TablaTemplate.heading("Similitud", text="Similitud")
        TablaTemplate.column("Patrón", width=170, anchor="w")
        TablaTemplate.column("Similitud", width=90, anchor="e")
        TablaTemplate.bind("<<TreeviewSelect>>", al_seleccionar_patron)
        TablaTemplate.pack(expand=True, fill="both", padx=8, pady=(0, 6))
        
    elif j == 1:
        tk.Label(card_bot, text="matchShapes (Contornos)", bg=PANEL, fg=GREEN, font=FONT_TITLE).pack(anchor="w", padx=8, pady=(6, 2))
        TablaShapes = ttk.Treeview(card_bot, columns=("Patrón", "Diferencia"), show="headings", height=6)
        TablaShapes.heading("Patrón", text="Patrón")
        TablaShapes.heading("Diferencia", text="Diferencia")
        TablaShapes.column("Patrón", width=170, anchor="w")
        TablaShapes.column("Diferencia", width=90, anchor="e")
        TablaShapes.bind("<<TreeviewSelect>>", al_seleccionar_patron)
        TablaShapes.pack(expand=True, fill="both", padx=8, pady=(0, 6))
        
    elif j == 2:
        tk.Label(card_bot, text="Momentos de Hu", bg=PANEL, fg=RED, font=FONT_TITLE).pack(anchor="w", padx=8, pady=(6, 2))
        TablaHu = ttk.Treeview(card_bot, columns=("Patrón", "Distancia", "Calidad"), show="headings", height=6)
        TablaHu.heading("Patrón", text="Patrón")
        TablaHu.heading("Distancia", text="Distancia")
        TablaHu.heading("Calidad", text="Calidad")
        TablaHu.column("Patrón", width=220, anchor="w")
        TablaHu.column("Distancia", width=100, anchor="e")
        TablaHu.column("Calidad", width=120, anchor="center")
        TablaHu.bind("<<TreeviewSelect>>", al_seleccionar_patron)
        TablaHu.pack(expand=True, fill="both", padx=8, pady=(0, 6))

ventana.focus_set()
ventana.mainloop()