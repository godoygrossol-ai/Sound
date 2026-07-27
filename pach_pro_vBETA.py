import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import math
import json
from collections import defaultdict

# ── PALETA INDUSTRIAL ────────────────────────────────────────────────────────
BG_BASE      = "#1A1C1E"
BG_PANEL     = "#22252A"
BG_WIDGET    = "#2C3038"
BG_ROW_ALT   = "#282B31"
BORDER       = "#3A3F4A"
BORDER_LIT   = "#4A5060"
ORANGE       = "#FF6B00"
ORANGE_DIM   = "#C25200"
GREEN        = "#39FF14"
GREEN_DIM    = "#1DB310"
RED          = "#FF3B3B"
RED_DIM      = "#C22A2A"
BLUE_ACCENT  = "#4A9EFF"
PURPLE       = "#A855F7"
CYAN         = "#00D4FF"
YELLOW       = "#FFD700"
TEXT_MAIN    = "#E8EAF0"
TEXT_DIM     = "#7A8090"
TEXT_LABEL   = "#A0A8B8"

FONT_MONO    = ("Courier New", 9)
FONT_MONO_B  = ("Courier New", 9, "bold")
FONT_MONO_SM = ("Courier New", 8)
FONT_TITLE   = ("Courier New", 10, "bold")
FONT_HDR     = ("Courier New", 8, "bold")

# Colores por grupo de instrumento
GRUPOS_PREDEFINIDOS = [
    "DRUMS", "BASS", "GUITARS", "KEYS", "BRASS",
    "STRINGS", "VOCALS", "PERC", "OTHER"
]
GRUPO_COLORES = {
    "DRUMS":   "#FF6B6B",
    "BASS":    "#4ECDC4",
    "GUITARS": "#45B7D1",
    "KEYS":    "#96CEB4",
    "BRASS":   "#FFEAA7",
    "STRINGS": "#DDA0DD",
    "VOCALS":  "#98FB98",
    "PERC":    "#F0E68C",
    "OTHER":   "#808080",
}

# Lados / zonas del escenario (punto 4)
LADOS_ESCENARIO = ["L", "L2", "CENTER", "CENTER2", "R", "R2"]

# Tipos de wireless
WIRELESS_TIPOS = ["MIC WL", "BODYPACK", "IEM"]


class AplicacionAudioEscenario:
    def __init__(self, root):
        self.root = root
        self.root.title("PACH PRO  v9.0  ──  STAGE PATCH MANAGER")
        self.root.geometry("1500x920")
        self.root.minsize(1280, 780)
        self.root.configure(bg=BG_BASE)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)

        self.ancho_escenario = 10
        self.profundidad_escenario = 6
        self.pacheras  = []
        self.bandas    = []
        self.tarimas   = []   # Lista de tarimas en el mapa (global, permanente)
        self.banda_actual = 0
        self.posiciones_predefinidas = []
        self.pachera_seleccionada = None
        self.canal_seleccionado   = None
        self.tarima_seleccionada  = None
        self.drag_data  = {"x": 0, "y": 0, "item": None}
        self.zoom_level = 1.0
        self.pan_start  = None
        self.ultimo_canal_global = 0
        self.remember_pach  = False
        self.mostrar_grupos = True
        self.tab_activa     = "CHANNELS"
        self.wireless_seleccionado = None  # para drag en mapa

        self._aplicar_estilos_ttk()
        self.crear_menu()
        self.crear_layout_principal()
        self.generar_posiciones_predefinidas()
        self.crear_nueva_banda("BAND 01")

    # ── ESTILOS TTK ──────────────────────────────────────────────────────────
    def _aplicar_estilos_ttk(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TFrame",      background=BG_BASE)
        s.configure("Panel.TFrame",background=BG_PANEL)
        s.configure("TLabelFrame", background=BG_PANEL, foreground=TEXT_LABEL,
                    borderwidth=1, relief="flat", font=FONT_HDR)
        s.configure("TLabelFrame.Label", background=BG_PANEL,
                    foreground=ORANGE, font=FONT_HDR)
        s.configure("TEntry", fieldbackground=BG_WIDGET, foreground=TEXT_MAIN,
                    insertcolor=ORANGE, borderwidth=1, relief="flat", font=FONT_MONO)
        s.map("TEntry", fieldbackground=[("focus","#353A44")])
        s.configure("TCombobox", fieldbackground=BG_WIDGET, foreground=TEXT_MAIN,
                    selectbackground=BG_WIDGET, selectforeground=ORANGE,
                    background=BG_WIDGET, font=FONT_MONO, arrowcolor=ORANGE)
        s.map("TCombobox", fieldbackground=[("readonly", BG_WIDGET)])
        s.configure("TLabel", background=BG_PANEL, foreground=TEXT_LABEL, font=FONT_MONO)
        s.configure("TButton", background=BG_WIDGET, foreground=TEXT_MAIN,
                    font=FONT_MONO_B, borderwidth=1, relief="flat", padding=(8,4))
        s.map("TButton", background=[("active", BORDER_LIT)])
        s.configure("Treeview", background=BG_WIDGET, fieldbackground=BG_WIDGET,
                    foreground=TEXT_MAIN, font=FONT_MONO_SM, rowheight=22, borderwidth=0)
        s.configure("Treeview.Heading", background=BG_BASE, foreground=ORANGE,
                    font=FONT_HDR, relief="flat", borderwidth=0)
        s.map("Treeview", background=[("selected", ORANGE_DIM)],
              foreground=[("selected","#000000")])
        s.configure("Thin.Vertical.TScrollbar",   background=BG_WIDGET,
                    troughcolor=BG_BASE, arrowcolor=BORDER_LIT, width=8)
        s.configure("Thin.Horizontal.TScrollbar", background=BG_WIDGET,
                    troughcolor=BG_BASE, arrowcolor=BORDER_LIT, width=8)

    # ── MENÚ ─────────────────────────────────────────────────────────────────
    def crear_menu(self):
        mb = tk.Menu(self.root, bg=BG_PANEL, fg=TEXT_MAIN,
                     activebackground=ORANGE, activeforeground="#000",
                     font=FONT_MONO, tearoff=0, relief="flat", bd=0)
        self.root.config(menu=mb)
        fm = tk.Menu(mb, bg=BG_PANEL, fg=TEXT_MAIN, activebackground=ORANGE,
                     activeforeground="#000", font=FONT_MONO, tearoff=0)
        fm.add_command(label="  NEW CONFIG",  command=self.nueva_configuracion)
        fm.add_command(label="  SAVE CONFIG", command=self.guardar_configuracion)
        fm.add_command(label="  LOAD CONFIG", command=self.cargar_configuracion)
        fm.add_separator()
        fm.add_command(label="  EXIT", command=self.root.quit)
        mb.add_cascade(label=" FILE ", menu=fm)
        am = tk.Menu(mb, bg=BG_PANEL, fg=TEXT_MAIN, activebackground=ORANGE,
                     activeforeground="#000", font=FONT_MONO, tearoff=0)
        am.add_command(label="  STATISTICS",        command=self.mostrar_estadisticas)
        am.add_command(label="  CONNECTION REPORT", command=self.mostrar_conexiones)
        am.add_command(label="  WIRELESS REPORT",   command=self.mostrar_reporte_wireless)
        mb.add_cascade(label=" ANALYSIS ", menu=am)
        vm = tk.Menu(mb, bg=BG_PANEL, fg=TEXT_MAIN, activebackground=ORANGE,
                     activeforeground="#000", font=FONT_MONO, tearoff=0)
        vm.add_command(label="  TOGGLE GROUP COLORS", command=self.toggle_grupos)
        mb.add_cascade(label=" VIEW ", menu=vm)

    # ── LAYOUT PRINCIPAL ─────────────────────────────────────────────────────
    def crear_layout_principal(self):
        self._crear_header()
        self.main = tk.Frame(self.root, bg=BG_BASE)
        self.main.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))
        self.main.grid_columnconfigure(0, weight=4)   # izquierda (mapa) más ancho
        self.main.grid_columnconfigure(1, weight=0)
        self.main.grid_columnconfigure(2, weight=2)   # panel derecho más angosto
        self.main.grid_rowconfigure(0, weight=1)

        left = tk.Frame(self.main, bg=BG_BASE)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._crear_panel_pacheras(left)
        self._crear_panel_canales(left)
        self._crear_mapa(left)
        self._crear_barra_acciones(left)

        tk.Frame(self.main, bg=BORDER, width=1).grid(row=0, column=1, sticky="ns", padx=4)

        right = tk.Frame(self.main, bg=BG_BASE)
        right.grid(row=0, column=2, sticky="nsew", padx=(4,0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._crear_panel_bandas(right)
        self._crear_panel_derecho(right)
        self._crear_footer()

    def _crear_header(self):
        hdr = tk.Frame(self.root, bg="#111315", height=38)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        tk.Frame(hdr, bg=ORANGE, height=2).pack(side=tk.TOP, fill=tk.X)
        inner = tk.Frame(hdr, bg="#111315")
        inner.pack(fill=tk.BOTH, expand=True, padx=12)
        tk.Label(inner, text="◈ PACH PRO", bg="#111315", fg=ORANGE,
                 font=("Courier New",13,"bold")).pack(side=tk.LEFT, pady=6)
        tk.Label(inner, text="v9.0", bg="#111315", fg=TEXT_DIM,
                 font=("Courier New",9)).pack(side=tk.LEFT, padx=(6,20), pady=6)
        tk.Label(inner, text="STAGE PATCH MANAGER", bg="#111315", fg=TEXT_DIM,
                 font=("Courier New",9)).pack(side=tk.LEFT, pady=6)
        self.status_var = tk.StringVar(value="READY")
        tk.Label(inner, textvariable=self.status_var, bg="#111315", fg=GREEN,
                 font=FONT_HDR).pack(side=tk.RIGHT, pady=6)
        tk.Label(inner, text="STATUS: ", bg="#111315", fg=TEXT_DIM,
                 font=FONT_HDR).pack(side=tk.RIGHT, pady=6)

    def _crear_footer(self):
        footer = tk.Frame(self.root, bg="#111315", height=44)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        tk.Frame(footer, bg=ORANGE, height=2).pack(side=tk.TOP, fill=tk.X)
        inner = tk.Frame(footer, bg="#111315")
        inner.pack(fill=tk.BOTH, expand=True, padx=16)
        tk.Label(inner, text="BY LAUTARO GODOY GROSSO", bg="#111315", fg=ORANGE,
                 font=("Courier New",12,"bold")).pack(side=tk.LEFT, pady=8)
        tk.Label(inner, text="──", bg="#111315", fg=BORDER_LIT,
                 font=("Courier New",12)).pack(side=tk.LEFT, padx=10, pady=8)
        tk.Label(inner, text="FOR LIVE SOUND", bg="#111315", fg=TEXT_DIM,
                 font=("Courier New",12)).pack(side=tk.LEFT, pady=8)
        tk.Label(inner, text="PACH PRO  v9.0", bg="#111315", fg=BORDER_LIT,
                 font=("Courier New",10)).pack(side=tk.RIGHT, pady=8)

    # ── PANEL PACHERAS ───────────────────────────────────────────────────────
    def _crear_panel_pacheras(self, parent):
        frame = self._panel(parent, "── PATCH BAY CONFIG")
        frame.grid(row=0, column=0, sticky="ew", pady=(0,4))
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(3, weight=1)

        self._lbl(frame,"NAME").grid(row=0,column=0,padx=(0,4),sticky="e")
        self.pachera_nombre_entry = self._entry(frame, width=14)
        self.pachera_nombre_entry.grid(row=0,column=1,sticky="ew",padx=(0,8))

        self._lbl(frame,"CH").grid(row=0,column=2,padx=(0,4),sticky="e")
        self.pachera_cantidad_entry = self._entry(frame, width=5)
        self.pachera_cantidad_entry.grid(row=0,column=3,sticky="w",padx=(0,8))

        self._lbl(frame,"GROUP →").grid(row=0,column=4,padx=(0,4),sticky="e")
        self.pachera_grupo_combo = self._combo(frame, width=10)
        self.pachera_grupo_combo['values'] = ["ANY"] + GRUPOS_PREDEFINIDOS
        self.pachera_grupo_combo.current(0)
        self.pachera_grupo_combo.grid(row=0,column=5,sticky="w",padx=(0,8))

        self.pachera_wl_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="WL BAY", variable=self.pachera_wl_var,
                       bg=BG_PANEL, fg=CYAN, selectcolor=BG_WIDGET,
                       activebackground=BG_PANEL, activeforeground=CYAN,
                       font=FONT_MONO_SM
                       ).grid(row=0, column=6, padx=(0,6), sticky="w")

        tk.Button(frame, text="+ ADD BAY", bg=ORANGE, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", activebackground=ORANGE_DIM,
                  command=self.agregar_pachera_manual, padx=10, pady=3
                  ).grid(row=0, column=7, sticky="e")

        tk.Frame(frame, bg=BORDER, height=1).grid(
            row=1, column=0, columnspan=7, sticky="ew", pady=(6,4))

        hdr = tk.Frame(frame, bg=BG_BASE)
        hdr.grid(row=2, column=0, columnspan=7, sticky="ew", pady=(0,2))
        for txt, w in [("  BAY NAME",14),("CH",4),("GROUP",8),("USAGE",8),("SPL IN",7)]:
            tk.Label(hdr, text=txt, bg=BG_BASE, fg=ORANGE,
                     font=FONT_HDR, width=w, anchor="w").pack(side=tk.LEFT, padx=2)
        tk.Label(hdr, text="ACTIONS", bg=BG_BASE, fg=ORANGE,
                 font=FONT_HDR).pack(side=tk.RIGHT, padx=4)

        self.pacheras_lista_frame = tk.Frame(frame, bg=BG_PANEL)
        self.pacheras_lista_frame.grid(row=3, column=0, columnspan=7, sticky="ew")
        self.actualizar_lista_pacheras()

    # ── PANEL CANALES ────────────────────────────────────────────────────────
    def _crear_panel_canales(self, parent):
        frame = self._panel(parent, "── CHANNEL INPUT")
        frame.grid(row=1, column=0, sticky="ew", pady=(0,4))
        for i in [1,3,5]: frame.grid_columnconfigure(i, weight=1)

        self._lbl(frame,"CH#").grid(row=0,column=0,padx=(0,4),sticky="e")
        self.canal_num_entry = self._entry(frame, width=5)
        self.canal_num_entry.grid(row=0,column=1,sticky="ew")
        tk.Button(frame, text="AUTO", bg=BG_WIDGET, fg=TEXT_DIM, font=FONT_MONO_SM,
                  relief="flat", cursor="hand2", activebackground=BORDER,
                  command=self.autoasignar_numero_canal, padx=6, pady=2
                  ).grid(row=0,column=2,padx=(2,8))

        self._lbl(frame,"INSTRUMENT").grid(row=0,column=3,padx=(0,4),sticky="e")
        self.instrumento_entry = self._entry(frame, width=14)
        self.instrumento_entry.grid(row=0,column=4,sticky="ew",padx=(0,8))

        self._lbl(frame,"MIC").grid(row=0,column=5,padx=(0,4),sticky="e")
        self.microfono_entry = self._entry(frame, width=14)
        self.microfono_entry.grid(row=0,column=6,sticky="ew",padx=(0,8))

        self._lbl(frame,"GROUP").grid(row=0,column=7,padx=(0,4),sticky="e")
        self.grupo_combo = self._combo(frame, width=9)
        self.grupo_combo['values'] = GRUPOS_PREDEFINIDOS
        self.grupo_combo.current(0)
        self.grupo_combo.grid(row=0,column=8,sticky="w",padx=(0,8))

        tk.Button(frame, text="+ ADD CH", bg=ORANGE, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", activebackground=ORANGE_DIM,
                  command=self.agregar_canal, padx=10, pady=3
                  ).grid(row=0, column=9, sticky="e")

    # ── MAPA ─────────────────────────────────────────────────────────────────
    def _crear_mapa(self, parent):
        # Punto 4: sin LabelFrame para no desperdiciar espacio — todo compacto
        wrap = tk.Frame(parent, bg=BG_BASE)
        wrap.grid(row=2, column=0, sticky="nsew", pady=(0,2))
        wrap.grid_rowconfigure(1, weight=1)   # canvas crece
        wrap.grid_columnconfigure(0, weight=1)

        # Toolbar compacto: RISER | GROUP COLORS | leyenda inline
        toolbar = tk.Frame(wrap, bg=BG_PANEL, pady=3)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        tk.Label(toolbar, text="STAGE MAP", bg=BG_PANEL, fg=ORANGE,
                 font=FONT_HDR).pack(side=tk.LEFT, padx=(8,12))
        tk.Frame(toolbar, bg=BORDER, width=1, height=16).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="+ RISER", bg=BG_WIDGET, fg=CYAN,
                  font=FONT_MONO_SM, relief="flat", cursor="hand2",
                  activebackground=BORDER, padx=8, pady=2,
                  command=self.agregar_tarima).pack(side=tk.LEFT, padx=4)
        tk.Frame(toolbar, bg=BORDER, width=1, height=16).pack(side=tk.LEFT, padx=4)
        self.btn_grupos = tk.Button(toolbar, text="● GROUPS: ON",
                  bg=BG_WIDGET, fg=GREEN, font=FONT_MONO_SM, relief="flat",
                  cursor="hand2", activebackground=BORDER, padx=8, pady=2,
                  command=self.toggle_grupos)
        self.btn_grupos.pack(side=tk.LEFT, padx=4)
        tk.Frame(toolbar, bg=BORDER, width=1, height=16).pack(side=tk.LEFT, padx=4)

        # Leyenda inline en el toolbar
        self.leyenda_frame = tk.Frame(toolbar, bg=BG_PANEL)
        self.leyenda_frame.pack(side=tk.LEFT, padx=4)
        self._actualizar_leyenda()

        # Canvas del mapa
        self.mapa_canvas = tk.Canvas(wrap, bg="#0D0F11", cursor="crosshair",
                                     highlightthickness=1, highlightbackground=BORDER)
        self.mapa_canvas.grid(row=1, column=0, sticky="nsew")

        hs = tk.Scrollbar(wrap, orient="horizontal", command=self.mapa_canvas.xview,
                          bg=BG_WIDGET, troughcolor=BG_BASE, width=6)
        hs.grid(row=2, column=0, sticky="ew")
        vs = tk.Scrollbar(wrap, orient="vertical", command=self.mapa_canvas.yview,
                          bg=BG_WIDGET, troughcolor=BG_BASE, width=6)
        vs.grid(row=1, column=1, sticky="ns")
        self.mapa_canvas.configure(xscrollcommand=hs.set, yscrollcommand=vs.set)

        self.mapa_canvas.bind("<Configure>",      lambda e: self.dibujar_escenario())
        self.mapa_canvas.bind("<Button-1>",        self.iniciar_arrastre)
        self.mapa_canvas.bind("<B1-Motion>",       self.arrastrar_item)
        self.mapa_canvas.bind("<ButtonRelease-1>", self.soltar_item)
        self.mapa_canvas.bind("<MouseWheel>",      self.zoom)
        self.mapa_canvas.bind("<Button-2>",        self.iniciar_pan)
        self.mapa_canvas.bind("<B2-Motion>",       self.pan)
        self.mapa_canvas.bind("<Button-3>",        self._menu_mapa)

    def _actualizar_leyenda(self):
        for w in self.leyenda_frame.winfo_children(): w.destroy()
        items = [(GREEN,"OK"),(RED,"FREE"),(BLUE_ACCENT,"BAY"),(ORANGE,"RISER+BAY"),(CYAN,"RISER")]
        if self.mostrar_grupos:
            items += [(v, k[:4]) for k,v in GRUPO_COLORES.items()]
        for color, texto in items:
            tk.Frame(self.leyenda_frame, bg=color, width=8, height=8).pack(
                side=tk.LEFT, padx=(4,2), pady=3)
            tk.Label(self.leyenda_frame, text=texto, bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New",7)).pack(side=tk.LEFT, padx=(0,6))

    # ── BARRA ACCIONES ───────────────────────────────────────────────────────
    def _crear_barra_acciones(self, parent):
        bar = tk.Frame(parent, bg=BG_BASE)
        bar.grid(row=3, column=0, sticky="ew")
        for i in range(5): bar.grid_columnconfigure(i, weight=1)
        tk.Frame(bar, bg=BORDER, height=1).grid(
            row=0, column=0, columnspan=5, sticky="ew", pady=(0,6))
        for i,(txt,cmd,bg,fg) in enumerate([
            ("▶ AUTO ASSIGN",   self.calcular_conexiones_mejorado, ORANGE,  "#000"),
            ("✕ CLEAR ASSIGNS", self.cancelar_asignaciones,        RED_DIM, TEXT_MAIN),
            ("⊗ RESET ALL",     self.limpiar_todo,                 "#333",  TEXT_MAIN),
        ]):
            tk.Button(bar, text=txt, bg=bg, fg=fg, font=FONT_MONO_B,
                      relief="flat", cursor="hand2",
                      activebackground=BORDER_LIT, activeforeground=TEXT_MAIN,
                      command=cmd, padx=8, pady=5
                      ).grid(row=1, column=i, padx=3, sticky="ew")
        self.btn_remember = tk.Button(
            bar, text="◎ REMEMBER: OFF", bg=BG_WIDGET, fg=TEXT_DIM,
            font=FONT_MONO_B, relief="flat", cursor="hand2",
            activebackground=BORDER_LIT, command=self.toggle_remember_pach,
            padx=8, pady=5)
        self.btn_remember.grid(row=1, column=3, padx=3, sticky="ew")

        tk.Button(bar, text="▶ ASSIGN BY GROUP", bg=PURPLE, fg=TEXT_MAIN,
                  font=FONT_MONO_B, relief="flat", cursor="hand2",
                  activebackground="#7C3AED", padx=8, pady=5,
                  command=self.asignar_por_grupos
                  ).grid(row=1, column=4, padx=3, sticky="ew")

    # ── PANEL DERECHO (BANDS + TABS) ─────────────────────────────────────────
    def _crear_panel_bandas(self, parent):
        wrap = tk.Frame(parent, bg=BG_BASE)
        wrap.grid(row=0, column=0, sticky="ew", pady=(0,4))
        wrap.grid_columnconfigure(0, weight=1)
        header = tk.Frame(wrap, bg=BG_PANEL, pady=4)
        header.pack(fill=tk.X)
        tk.Label(header, text="── BANDS", bg=BG_PANEL, fg=ORANGE,
                 font=FONT_HDR).pack(side=tk.LEFT, padx=8)
        tk.Button(header, text="+ NEW BAND", bg=BG_WIDGET, fg=ORANGE,
                  font=FONT_MONO_SM, relief="flat", cursor="hand2",
                  activebackground=BORDER, command=self.agregar_nueva_banda,
                  padx=6, pady=2).pack(side=tk.RIGHT, padx=8)
        # Contenedor de tabs con flechas de scroll (Punto 5)
        nav_frame = tk.Frame(wrap, bg=BG_PANEL)
        nav_frame.pack(fill=tk.X)

        tk.Button(nav_frame, text="◀", bg=BG_BASE, fg=TEXT_DIM,
                  font=FONT_MONO_SM, relief="flat", cursor="hand2",
                  padx=4, pady=3,
                  command=lambda: self.canvas_bandas.xview_scroll(-1,"units")
                  ).pack(side=tk.LEFT)

        self.canvas_bandas = tk.Canvas(nav_frame, bg=BG_PANEL, height=32,
                                       highlightthickness=0)
        self.canvas_bandas.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(nav_frame, text="▶", bg=BG_BASE, fg=TEXT_DIM,
                  font=FONT_MONO_SM, relief="flat", cursor="hand2",
                  padx=4, pady=3,
                  command=lambda: self.canvas_bandas.xview_scroll(1,"units")
                  ).pack(side=tk.LEFT)

        self.frame_bandas = tk.Frame(self.canvas_bandas, bg=BG_PANEL)
        self.canvas_bandas.create_window((0,0), window=self.frame_bandas, anchor="nw")
        self.frame_bandas.bind("<Configure>",
            lambda e: self.canvas_bandas.configure(
                scrollregion=self.canvas_bandas.bbox("all")))

    def _crear_panel_derecho(self, parent):
        """Panel unificado: formulario wireless + lista canales+wireless"""
        wrap = tk.Frame(parent, bg=BG_BASE)
        wrap.grid(row=1, column=0, sticky="nsew")
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        self._crear_formulario_wireless(wrap)
        self._crear_lista_canales(wrap)

    # ── LISTA CANALES + WIRELESS (unificada) ────────────────────────────────
    def _crear_lista_canales(self, parent):
        self.frame_channels = self._panel(parent, "── CHANNEL & WIRELESS LIST")
        self.frame_channels.grid(row=1, column=0, sticky="nsew")
        self.frame_channels.grid_rowconfigure(0, weight=1)
        self.frame_channels.grid_columnconfigure(0, weight=1)

        cols = [("num","CH",38),("grupo","GRP",46),
                ("inst","INSTRUMENT",100),("mic","MIC/USER",85),
                ("freq","FREQ",70),("pachera","BAY",65),("splitter","SPL IN",48)]
        self.tree = ttk.Treeview(self.frame_channels,
                                  columns=[c[0] for c in cols],
                                  show="headings", selectmode="browse")
        for col_id, heading, width in cols:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor=tk.CENTER, minwidth=30)

        # Tags por grupo
        for grupo, color in GRUPO_COLORES.items():
            self.tree.tag_configure(f"grp_{grupo}", foreground=color, background=BG_WIDGET)
            self.tree.tag_configure(f"grp_{grupo}_alt", foreground=color, background=BG_ROW_ALT)
        self.tree.tag_configure("sinasignar",     foreground=RED,    background=BG_WIDGET)
        self.tree.tag_configure("sinasignar_alt", foreground=RED,    background=BG_ROW_ALT)
        # Tags wireless en la lista unificada
        self.tree.tag_configure("wireless_iem",     foreground=CYAN,   background="#001820")
        self.tree.tag_configure("wireless_iem_alt", foreground=CYAN,   background="#001A22")
        self.tree.tag_configure("wireless_mic",     foreground=YELLOW, background="#1A1400")
        self.tree.tag_configure("wireless_mic_alt", foreground=YELLOW, background="#1C1600")

        vs = ttk.Scrollbar(self.frame_channels, orient="vertical",
                           command=self.tree.yview, style="Thin.Vertical.TScrollbar")
        vs.grid(row=0, column=1, sticky="ns")
        hs = ttk.Scrollbar(self.frame_channels, orient="horizontal",
                           command=self.tree.xview, style="Thin.Horizontal.TScrollbar")
        hs.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", self.editar_canal)
        self.tree.bind("<Button-3>", self._menu_contextual_canal)

        acciones = tk.Frame(self.frame_channels, bg=BG_PANEL)
        acciones.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4,0))
        tk.Label(acciones, text="SELECTED:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=FONT_MONO_SM).pack(side=tk.LEFT, padx=(0,6))
        tk.Button(acciones, text="✎ EDIT", bg=BG_WIDGET, fg=ORANGE,
                  font=FONT_MONO_SM, relief="flat", cursor="hand2",
                  activebackground=BORDER, padx=8, pady=2,
                  command=lambda: self.editar_canal(None)).pack(side=tk.LEFT, padx=2)
        tk.Button(acciones, text="✕ DELETE", bg=BG_WIDGET, fg=RED,
                  font=FONT_MONO_SM, relief="flat", cursor="hand2",
                  activebackground=BORDER, padx=8, pady=2,
                  command=self.eliminar_canal_seleccionado).pack(side=tk.LEFT, padx=2)
        tk.Label(acciones, text="  dbl-click to edit  ·  right-click menu",
                 bg=BG_PANEL, fg=TEXT_DIM, font=FONT_MONO_SM).pack(side=tk.LEFT, padx=8)

    # ── FORMULARIO WIRELESS (con SPL input como pacheras) ───────────────────
    def _crear_formulario_wireless(self, parent):
        form = self._panel(parent, "── WIRELESS / RF INPUT")
        form.grid(row=0, column=0, sticky="ew", pady=(0,4))
        for i in [1,3,5,7]: form.grid_columnconfigure(i, weight=1)

        # Fila 0: CH# | TYPE | MODEL | SPL INPUT
        self._lbl(form,"CH#").grid(row=0,column=0,padx=(0,4),sticky="e")
        self.wl_canal_entry = self._entry(form, width=5)
        self.wl_canal_entry.grid(row=0,column=1,sticky="ew",padx=(0,6))

        self._lbl(form,"TYPE").grid(row=0,column=2,padx=(0,4),sticky="e")
        self.wl_tipo_combo = self._combo(form, width=9)
        self.wl_tipo_combo['values'] = WIRELESS_TIPOS
        self.wl_tipo_combo.current(0)
        self.wl_tipo_combo.grid(row=0,column=3,sticky="ew",padx=(0,6))

        self._lbl(form,"MODEL").grid(row=0,column=4,padx=(0,4),sticky="e")
        self.wl_modelo_entry = self._entry(form, width=10)
        self.wl_modelo_entry.grid(row=0,column=5,sticky="ew",padx=(0,6))

        self._lbl(form,"SPL IN").grid(row=0,column=6,padx=(0,4),sticky="e")
        self.wl_spl_entry = self._entry(form, width=5)
        self.wl_spl_entry.grid(row=0,column=7,sticky="ew",padx=(0,6))

        # Fila 1: FREQ | USER | NOTES
        self._lbl(form,"FREQ").grid(row=1,column=0,padx=(0,4),sticky="e",pady=(4,0))
        self.wl_freq_entry = self._entry(form, width=9)
        self.wl_freq_entry.grid(row=1,column=1,sticky="ew",padx=(0,6),pady=(4,0))

        self._lbl(form,"USER").grid(row=1,column=2,padx=(0,4),sticky="e",pady=(4,0))
        self.wl_user_entry = self._entry(form, width=10)
        self.wl_user_entry.grid(row=1,column=3,sticky="ew",padx=(0,6),pady=(4,0))

        self._lbl(form,"NOTES").grid(row=1,column=4,padx=(0,4),sticky="e",pady=(4,0))
        self.wl_notes_entry = self._entry(form, width=10)
        self.wl_notes_entry.grid(row=1,column=5,sticky="ew",padx=(0,6),pady=(4,0))

        # Indicador del próximo SPL libre
        self.wl_spl_hint = tk.Label(form, text="", bg=BG_PANEL, fg=CYAN,
                                     font=FONT_MONO_SM)
        self.wl_spl_hint.grid(row=1,column=6,columnspan=2,sticky="w",pady=(4,0))

        tk.Button(form, text="+ ADD WL", bg=CYAN, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", activebackground="#00A8CC",
                  command=self.agregar_wireless, padx=8, pady=3
                  ).grid(row=0, column=8, rowspan=2, sticky="ns", padx=(4,0))

        # Hint de SPL libre al hacer foco en el campo
        self.wl_spl_entry.bind("<FocusIn>", lambda e: self._actualizar_hint_spl())
        self.wl_canal_entry.bind("<FocusIn>", lambda e: self._actualizar_hint_spl())

    # ── HELPERS ──────────────────────────────────────────────────────────────
    def _panel(self, parent, title=""):
        return tk.LabelFrame(parent, text=f" {title} ", bg=BG_PANEL, fg=ORANGE,
                             font=FONT_HDR, bd=1, relief="flat",
                             highlightbackground=BORDER, highlightthickness=1,
                             padx=8, pady=6)

    def _lbl(self, parent, text):
        return tk.Label(parent, text=text, bg=BG_PANEL, fg=TEXT_LABEL, font=FONT_MONO_SM)

    def _entry(self, parent, width=12):
        return tk.Entry(parent, bg=BG_WIDGET, fg=TEXT_MAIN, insertbackground=ORANGE,
                        relief="flat", font=FONT_MONO, width=width,
                        highlightbackground=BORDER, highlightthickness=1,
                        highlightcolor=ORANGE)

    def _combo(self, parent, width=14):
        return ttk.Combobox(parent, state="readonly", width=width, font=FONT_MONO)

    def _set_status(self, text):
        self.status_var.set(text)

    @property
    def wireless(self):
        """Wireless de la banda actual"""
        if self.banda_actual < len(self.bandas):
            return self.bandas[self.banda_actual].setdefault("wireless", [])
        return []

    def _pachera_en_tarima(self, tarima):
        """Devuelve la pachera que está posicionada dentro de una tarima, o None"""
        tx1 = tarima["x"]
        ty1 = tarima["y"]
        tx2 = tx1 + tarima["w"]
        ty2 = ty1 + tarima["h"]
        for p in self.pacheras:
            if tx1 <= p["x"] <= tx2 and ty1 <= p["y"] <= ty2:
                return p
        return None

    def _tarima_del_canal(self, canal):
        """Devuelve la tarima que contiene al canal, o None"""
        for t in self.tarimas:
            tx1, ty1 = t["x"], t["y"]
            tx2, ty2 = tx1 + t["w"], ty1 + t["h"]
            if tx1 <= canal["x"] <= tx2 and ty1 <= canal["y"] <= ty2:
                return t
        return None

    def _calcular_offset_splitter(self, nombre_pachera):
        """Retorna el input inicial del splitter para una pachera (suma acumulada de anteriores)"""
        offset = 0
        for p in self.pacheras:
            if p["nombre"] == nombre_pachera:
                return offset
            offset += p["capacidad"]
        return offset

    def _input_splitter(self, canal):
        """Dado un canal asignado, retorna su número de input en el splitter global"""
        if not canal.get("pachera_asignada") or not canal.get("input_pach"):
            return None
        offset = self._calcular_offset_splitter(canal["pachera_asignada"])
        try:
            return offset + int(canal["input_pach"])
        except:
            return None

    def toggle_grupos(self):
        self.mostrar_grupos = not self.mostrar_grupos
        color = GREEN if self.mostrar_grupos else TEXT_DIM
        txt   = "● GROUP COLORS: ON" if self.mostrar_grupos else "○ GROUP COLORS: OFF"
        self.btn_grupos.configure(text=txt, fg=color)
        self._actualizar_leyenda()
        self.dibujar_escenario()
        self.actualizar_lista_canales()

    # ── POSICIONES ───────────────────────────────────────────────────────────
    def generar_posiciones_predefinidas(self):
        """Genera posiciones de referencia (usadas internamente, no en UI)"""
        filas = {"FRONT": 1, "MID": 3, "REAR": 5}
        lados_x = {"L": 1, "L2": 2.5, "CENTER": 4.5, "CENTER2": 5.5, "R2": 7.5, "R": 9}
        posiciones = []
        for fila, y in filas.items():
            for lado, x in lados_x.items():
                posiciones.append({"nombre": f"{fila} {lado}", "x": x, "y": y})
        self.posiciones_predefinidas = posiciones

    # ── BANDAS ───────────────────────────────────────────────────────────────
    def crear_nueva_banda(self, nombre):
        self.bandas.append({
            "nombre": nombre, "canales": [], "wireless": [],
            "pacheras_utilizacion": {
                p["nombre"]: {"canales_asignados":[], "entradas":{}}
                for p in self.pacheras}})
        self.banda_actual = len(self.bandas) - 1
        self.actualizar_pestanas_bandas()
        self.actualizar_lista_canales()
        self.dibujar_escenario()

    def actualizar_pestanas_bandas(self):
        for w in self.frame_bandas.winfo_children(): w.destroy()
        for i, banda in enumerate(self.bandas):
            activa = i == self.banda_actual
            bg = ORANGE if activa else BG_WIDGET
            fg = "#000"  if activa else TEXT_DIM
            fnt= FONT_MONO_B if activa else FONT_MONO_SM

            grp = tk.Frame(self.frame_bandas, bg=BG_PANEL)
            grp.pack(side=tk.LEFT, padx=(0,4))

            btn = tk.Button(grp, text=banda["nombre"],
                      bg=bg, fg=fg, font=fnt, relief="flat", cursor="hand2",
                      activebackground=ORANGE_DIM, padx=10, pady=4,
                      command=lambda idx=i: self.cambiar_banda_actual(idx))
            btn.pack(side=tk.LEFT)
            # Doble click = renombrar
            btn.bind("<Double-1>", lambda e, idx=i: self.renombrar_banda(idx))

            # Botón ✎ renombrar (solo si activa)
            if activa:
                tk.Button(grp, text="✎", bg=bg, fg=ORANGE_DIM,
                          font=FONT_MONO_SM, relief="flat", cursor="hand2",
                          padx=3, pady=4,
                          command=lambda idx=i: self.renombrar_banda(idx)
                          ).pack(side=tk.LEFT)

            if len(self.bandas) > 1:
                tk.Button(grp, text="×", bg=bg,
                          fg=RED if activa else TEXT_DIM,
                          font=FONT_MONO_SM, relief="flat", cursor="hand2",
                          padx=4, pady=4,
                          command=lambda idx=i: self.eliminar_banda(idx)
                          ).pack(side=tk.LEFT)

    def renombrar_banda(self, idx):
        """Ventana estilo app para renombrar banda"""
        banda = self.bandas[idx]
        win = tk.Toplevel(self.root)
        win.title("RENAME BAND")
        win.configure(bg=BG_BASE)
        win.resizable(False, False)
        win.grab_set()

        tk.Frame(win, bg=ORANGE, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="RENAME BAND", bg=BG_PANEL, fg=ORANGE,
                 font=FONT_TITLE).grid(row=0, column=0, columnspan=2,
                                        sticky="w", pady=(0,12))
        tk.Label(body, text="CURRENT NAME", bg=BG_PANEL, fg=TEXT_DIM,
                 font=FONT_MONO_SM).grid(row=1, column=0, sticky="e", padx=(0,8), pady=4)
        tk.Label(body, text=banda["nombre"], bg=BG_PANEL, fg=TEXT_MAIN,
                 font=FONT_MONO_B).grid(row=1, column=1, sticky="w", pady=4)

        tk.Label(body, text="NEW NAME", bg=BG_PANEL, fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=2, column=0, sticky="e", padx=(0,8), pady=4)
        entry = self._entry(body, width=22)
        entry.insert(0, banda["nombre"])
        entry.select_range(0, tk.END)
        entry.grid(row=2, column=1, sticky="ew", pady=4)
        entry.focus_set()

        tk.Frame(body, bg=BORDER, height=1).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=10)

        bf = tk.Frame(body, bg=BG_PANEL)
        bf.grid(row=4, column=0, columnspan=2, sticky="ew")
        bf.grid_columnconfigure(0, weight=1)
        bf.grid_columnconfigure(1, weight=1)

        def _save():
            nuevo = entry.get().strip().upper()
            if not nuevo:
                messagebox.showerror("ERROR", "Name cannot be empty.", parent=win)
                return
            self.bandas[idx]["nombre"] = nuevo
            win.destroy()
            self.actualizar_pestanas_bandas()
            self._set_status(f"BAND RENAMED → {nuevo}")

        entry.bind("<Return>", lambda e: _save())

        tk.Button(bf, text="SAVE", bg=ORANGE, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=_save).grid(row=0, column=0, sticky="ew", padx=(0,4))
        tk.Button(bf, text="CANCEL", bg=BG_WIDGET, fg=TEXT_DIM, font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=win.destroy).grid(row=0, column=1, sticky="ew", padx=(4,0))

    def cambiar_banda_actual(self, idx):
        self.banda_actual = idx
        self.actualizar_pestanas_bandas()
        self.actualizar_lista_canales()   # recarga canales + wireless de la nueva banda
        self.actualizar_lista_pacheras()
        self.dibujar_escenario()
        self._actualizar_hint_spl()

    def agregar_nueva_banda(self):
        win = tk.Toplevel(self.root)
        win.title("NEW BAND")
        win.configure(bg=BG_BASE)
        win.resizable(False, False)
        win.grab_set()

        tk.Frame(win, bg=ORANGE, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="NEW BAND", bg=BG_PANEL, fg=ORANGE,
                 font=FONT_TITLE).grid(row=0, column=0, columnspan=2,
                                        sticky="w", pady=(0,12))
        tk.Label(body, text="BAND NAME", bg=BG_PANEL, fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=1, column=0, sticky="e", padx=(0,8), pady=4)
        entry = self._entry(body, width=22)
        entry.grid(row=1, column=1, sticky="ew", pady=4)
        entry.focus_set()

        tk.Frame(body, bg=BORDER, height=1).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=10)

        bf = tk.Frame(body, bg=BG_PANEL)
        bf.grid(row=3, column=0, columnspan=2, sticky="ew")
        bf.grid_columnconfigure(0, weight=1); bf.grid_columnconfigure(1, weight=1)

        def _create():
            nombre = entry.get().strip().upper()
            if not nombre:
                messagebox.showerror("ERROR","Name cannot be empty.",parent=win); return
            win.destroy()
            self.crear_nueva_banda(nombre)

        entry.bind("<Return>", lambda e: _create())
        tk.Button(bf, text="CREATE", bg=ORANGE, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=_create).grid(row=0, column=0, sticky="ew", padx=(0,4))
        tk.Button(bf, text="CANCEL", bg=BG_WIDGET, fg=TEXT_DIM, font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=win.destroy).grid(row=0, column=1, sticky="ew", padx=(4,0))

    def eliminar_banda(self, idx):
        if len(self.bandas) > 1:
            if messagebox.askyesno("DELETE BAND",
                                   f"Delete '{self.bandas[idx]['nombre']}'?",
                                   parent=self.root):
                del self.bandas[idx]
                if self.banda_actual >= len(self.bandas):
                    self.banda_actual = len(self.bandas) - 1
                self.actualizar_pestanas_bandas()
                self.actualizar_lista_canales()
                self.dibujar_escenario()
        else:
            messagebox.showwarning("ERROR","At least one band required.",parent=self.root)

    # ── PACHERAS ─────────────────────────────────────────────────────────────
    def agregar_pachera_manual(self):
        nombre = self.pachera_nombre_entry.get().strip().upper()
        grupo  = self.pachera_grupo_combo.get()
        es_wl  = self.pachera_wl_var.get()
        try:
            cap = int(self.pachera_cantidad_entry.get())
            if not nombre: raise ValueError("Name required")
            if cap <= 0:   raise ValueError("Capacity must be > 0")
            if any(p["nombre"].lower()==nombre.lower() for p in self.pacheras):
                raise ValueError("Bay name already exists")
        except ValueError as e:
            messagebox.showerror("INPUT ERROR", str(e), parent=self.root); return
        self.pacheras.append({
            "nombre":nombre, "x":self.ancho_escenario/2,
            "y":self.profundidad_escenario/2, "capacidad":cap,
            "grupo_exclusivo": grupo,
            "es_wireless": es_wl})
        for banda in self.bandas:
            banda["pacheras_utilizacion"][nombre] = {"canales_asignados":[],"entradas":{}}
        self.pachera_nombre_entry.delete(0,tk.END)
        self.pachera_cantidad_entry.delete(0,tk.END)
        self.dibujar_escenario()
        self.actualizar_lista_pacheras()
        self._set_status(f"BAY '{nombre}' ADDED")

    def actualizar_lista_pacheras(self):
        for w in self.pacheras_lista_frame.winfo_children(): w.destroy()
        if not self.pacheras:
            tk.Label(self.pacheras_lista_frame, text="  No bays added yet.",
                     bg=BG_PANEL, fg=TEXT_DIM, font=FONT_MONO_SM
                     ).pack(anchor="w", pady=2); return
        for i, p in enumerate(self.pacheras):
            util = 0
            if self.banda_actual < len(self.bandas):
                util = len(self.bandas[self.banda_actual]["pacheras_utilizacion"]
                           .get(p["nombre"],{}).get("canales_asignados",[]))
            bg_row = BG_WIDGET if i%2==0 else BG_ROW_ALT
            row = tk.Frame(self.pacheras_lista_frame, bg=bg_row)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=p["nombre"], bg=bg_row, fg=TEXT_MAIN,
                     font=FONT_MONO_B, width=14, anchor="w"
                     ).pack(side=tk.LEFT, padx=6, pady=3)
            tk.Label(row, text=str(p["capacidad"]), bg=bg_row, fg=TEXT_DIM,
                     font=FONT_MONO_SM, width=4, anchor="center"
                     ).pack(side=tk.LEFT, padx=2)
            grp = p.get("grupo_exclusivo","ANY")
            grp_color = GRUPO_COLORES.get(grp, TEXT_DIM)
            tk.Label(row, text=grp[:6], bg=bg_row, fg=grp_color,
                     font=FONT_MONO_SM, width=7, anchor="center"
                     ).pack(side=tk.LEFT, padx=2)
            uso_color = GREEN if util < p["capacidad"] else RED
            tk.Label(row, text=f"{util}/{p['capacidad']}", bg=bg_row,
                     fg=uso_color, font=FONT_MONO_SM, width=6, anchor="center"
                     ).pack(side=tk.LEFT, padx=2)
            # Número de input inicial en el splitter
            spl_start = self._calcular_offset_splitter(p["nombre"]) + 1
            spl_end   = spl_start + p["capacidad"] - 1
            es_wl_bay = p.get("es_wireless", False)
            spl_color = CYAN if es_wl_bay else TEXT_DIM
            spl_label = f"◎{spl_start}-{spl_end}" if es_wl_bay else f"{spl_start}-{spl_end}"
            tk.Label(row, text=spl_label, bg=bg_row,
                     fg=spl_color, font=FONT_MONO_SM, width=8, anchor="center"
                     ).pack(side=tk.LEFT, padx=2)
            tk.Button(row, text="✎ EDIT", bg=BG_BASE, fg=ORANGE,
                      font=FONT_MONO_SM, relief="flat", cursor="hand2",
                      activebackground=BORDER, padx=6, pady=2,
                      command=lambda idx=i: self.editar_pachera(idx)
                      ).pack(side=tk.RIGHT, padx=2, pady=2)
            tk.Button(row, text="✕ DEL", bg=BG_BASE, fg=RED,
                      font=FONT_MONO_SM, relief="flat", cursor="hand2",
                      activebackground=BORDER, padx=6, pady=2,
                      command=lambda idx=i: self.eliminar_pachera(idx)
                      ).pack(side=tk.RIGHT, padx=2, pady=2)

    def editar_pachera(self, idx):
        p = self.pacheras[idx]
        win = tk.Toplevel(self.root)
        win.title("EDIT BAY"); win.configure(bg=BG_BASE); win.resizable(False,False)
        tk.Frame(win, bg=ORANGE, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=16, pady=14)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text=f"EDIT BAY  ·  {p['nombre']}", bg=BG_PANEL,
                 fg=ORANGE, font=FONT_TITLE).grid(row=0,column=0,columnspan=2,
                                                   sticky="w",pady=(0,10))
        tk.Label(body,text="NAME",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=1,column=0,sticky="e",padx=(0,8),pady=4)
        nombre_e = self._entry(body, width=18); nombre_e.insert(0, p["nombre"])
        nombre_e.grid(row=1,column=1,sticky="ew",pady=4)
        tk.Label(body,text="CHANNELS",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=2,column=0,sticky="e",padx=(0,8),pady=4)
        cap_e = self._entry(body, width=6); cap_e.insert(0, str(p["capacidad"]))
        cap_e.grid(row=2,column=1,sticky="w",pady=4)
        tk.Label(body,text="GROUP →",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=3,column=0,sticky="e",padx=(0,8),pady=4)
        grp_c = self._combo(body, width=14)
        grp_c['values'] = ["ANY"] + GRUPOS_PREDEFINIDOS
        grp_c.set(p.get("grupo_exclusivo","ANY"))
        grp_c.grid(row=3,column=1,sticky="w",pady=4)
        tk.Frame(body,bg=BORDER,height=1).grid(row=4,column=0,columnspan=2,
                                                sticky="ew",pady=8)
        tk.Button(body, text="SAVE CHANGES", bg=ORANGE, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=14, pady=4,
                  command=lambda: self._guardar_edicion_pachera(
                      idx, nombre_e.get(), cap_e.get(), grp_c.get(), win)
                  ).grid(row=5,column=0,columnspan=2,sticky="ew")

    def _guardar_edicion_pachera(self, idx, nuevo_nombre, nueva_cap_str, grupo, win):
        nuevo_nombre = nuevo_nombre.strip().upper()
        try:
            nueva_cap = int(nueva_cap_str)
            if not nuevo_nombre: raise ValueError("Name required")
            if nueva_cap <= 0:   raise ValueError("Capacity must be > 0")
            for i,p in enumerate(self.pacheras):
                if i!=idx and p["nombre"].lower()==nuevo_nombre.lower():
                    raise ValueError("Bay name already exists")
        except ValueError as e:
            messagebox.showerror("INPUT ERROR", str(e), parent=win); return
        viejo = self.pacheras[idx]["nombre"]
        self.pacheras[idx].update({"nombre":nuevo_nombre,"capacidad":nueva_cap,
                                    "grupo_exclusivo":grupo})
        for banda in self.bandas:
            if viejo in banda["pacheras_utilizacion"]:
                banda["pacheras_utilizacion"][nuevo_nombre] = \
                    banda["pacheras_utilizacion"].pop(viejo)
            for canal in banda["canales"]:
                if canal.get("pachera_asignada") == viejo:
                    canal["pachera_asignada"] = nuevo_nombre
        win.destroy()
        self.actualizar_lista_pacheras()
        self.actualizar_lista_canales()
        self.dibujar_escenario()
        self._set_status(f"BAY '{nuevo_nombre}' UPDATED")

    def eliminar_pachera(self, idx):
        p = self.pacheras[idx]
        if not messagebox.askyesno("DELETE BAY",
                                   f"Delete bay '{p['nombre']}'?\n"
                                   "All assignments to this bay will be cleared.",
                                   parent=self.root): return
        nombre = p["nombre"]
        for banda in self.bandas:
            for canal in banda["canales"]:
                if canal.get("pachera_asignada") == nombre:
                    canal["pachera_asignada"] = None
                    canal["input_pach"]       = None
            banda["pacheras_utilizacion"].pop(nombre, None)
        del self.pacheras[idx]
        self.actualizar_lista_pacheras()
        self.actualizar_lista_canales()
        self.dibujar_escenario()
        self._set_status(f"BAY '{nombre}' DELETED")

    # ── CANALES ──────────────────────────────────────────────────────────────
    def autoasignar_numero_canal(self):
        """Siguiente número libre considerando canales cableados Y wireless"""
        usados = set()
        if self.banda_actual < len(self.bandas):
            for c in self.bandas[self.banda_actual]["canales"]:
                usados.add(c["numero"])
        for w in self.wireless:
            try: usados.add(int(w["canal"]))
            except: pass
        siguiente = 1
        while siguiente in usados:
            siguiente += 1
        self.ultimo_canal_global = max(self.ultimo_canal_global, siguiente)
        self.canal_num_entry.delete(0,tk.END)
        self.canal_num_entry.insert(0, str(siguiente))
        self.instrumento_entry.focus()

    def agregar_canal(self):
        try:
            if not self.canal_num_entry.get(): self.autoasignar_numero_canal()
            numero      = int(self.canal_num_entry.get())
            instrumento = self.instrumento_entry.get().strip().upper()
            microfono   = self.microfono_entry.get().strip().upper()
            grupo       = self.grupo_combo.get()
            if numero < 1 or numero > 200: raise ValueError("Channel number must be 1–200")
            if not all([instrumento, microfono]):
                raise ValueError("Instrument and Mic fields are required")
            if self.banda_actual < len(self.bandas):
                if any(c["numero"]==numero for c in self.bandas[self.banda_actual]["canales"]):
                    raise ValueError(f"Channel {numero} already exists in this band")
            # Posición por defecto: centro del escenario (drag para mover)
            canal = {"numero":numero,"instrumento":instrumento,"microfono":microfono,
                     "grupo":grupo,"x":self.ancho_escenario/2,"y":self.profundidad_escenario/2,
                     "pachera_asignada":None,"input_pach":None,"posicion_predefinida":"CUSTOM"}
            if self.banda_actual < len(self.bandas):
                self.bandas[self.banda_actual]["canales"].append(canal)
            if numero > self.ultimo_canal_global: self.ultimo_canal_global = numero
            self.canal_num_entry.delete(0,tk.END)
            self.instrumento_entry.delete(0,tk.END)
            self.microfono_entry.delete(0,tk.END)
            self.instrumento_entry.focus()
            self.dibujar_escenario()
            self.actualizar_lista_canales()
            self._set_status(f"CH {numero} ADDED  ·  drag to position on map")
        except ValueError as e:
            messagebox.showerror("INPUT ERROR", str(e), parent=self.root)

    def actualizar_lista_canales(self):
        """Lista unificada: canales cableados + wireless, ordenados por número de canal"""
        for item in self.tree.get_children(): self.tree.delete(item)
        if self.banda_actual >= len(self.bandas): return

        # Construir lista unificada: canales + wireless
        items = []

        for canal in self.bandas[self.banda_actual]["canales"]:
            items.append(("canal", canal))

        for w in self.wireless:
            try:
                num = int(w["canal"])
            except:
                num = 9999
            items.append(("wireless", w, num))

        # Ordenar por número de canal
        def sort_key(entry):
            if entry[0] == "canal":
                return entry[1]["numero"]
            else:
                return entry[2]
        items.sort(key=sort_key)

        for i, entry in enumerate(items):
            es_alt = i % 2 == 1
            if entry[0] == "canal":
                canal  = entry[1]
                asignado = bool(canal["pachera_asignada"])
                grupo    = canal.get("grupo","OTHER")
                if asignado and self.mostrar_grupos:
                    tag = f"grp_{grupo}_alt" if es_alt else f"grp_{grupo}"
                elif asignado:
                    tag = "alt_asig" if es_alt else "asignado"
                else:
                    tag = "sinasignar_alt" if es_alt else "sinasignar"
                spl_num = self._input_splitter(canal)
                spl_txt = str(spl_num) if spl_num else "—"
                self.tree.insert("","end", tags=(tag,), values=(
                    f"{canal['numero']:02d}",
                    canal.get("grupo","OTHER")[:4],
                    canal["instrumento"],
                    canal["microfono"],
                    "",                                    # FREQ vacío para cableado
                    canal["pachera_asignada"] or "—",
                    spl_txt),
                    iid=f"ch_{canal['numero']}")
            else:
                w   = entry[1]
                is_iem = "IEM" in w["tipo"].upper()
                tag = ("wireless_iem_alt" if es_alt else "wireless_iem") if is_iem                        else ("wireless_mic_alt" if es_alt else "wireless_mic")
                tipo_icono = "◎" if is_iem else "♪"
                spl_wl = w.get("spl_input", 0)
                spl_wl_txt = str(spl_wl) if spl_wl else "—"
                modelo_txt = w.get("modelo","") or ""
                nombre_txt = f"{tipo_icono} {modelo_txt}"
                self.tree.insert("","end", tags=(tag,), values=(
                    f"W{w['canal']}",
                    "WL",
                    nombre_txt,
                    w.get("usuario","") or "—",           # USER en col MIC/USER
                    w.get("frecuencia","") or "—",         # FREQ en col FREQ
                    "WIRELESS",
                    spl_wl_txt),
                    iid=f"wl_{self.wireless.index(w)}")

    def editar_canal(self, event=None):
        if self.banda_actual >= len(self.bandas): return
        sel = self.tree.selection()
        if not sel: return
        item = sel[0]
        # Detectar si es wireless o canal
        if item.startswith("wl_"):
            idx = int(item.split("_")[1])
            self._editar_wireless_por_idx(idx)
            return
        canal_num = int(self.tree.item(item,"values")[0])
        canal = next(c for c in self.bandas[self.banda_actual]["canales"]
                     if c["numero"]==canal_num)
        win = tk.Toplevel(self.root)
        win.title(f"EDIT  CH {canal_num:02d}")
        win.configure(bg=BG_BASE); win.resizable(False,False)
        tk.Frame(win, bg=ORANGE, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text=f"CHANNEL  {canal_num:02d}", bg=BG_PANEL,
                 fg=ORANGE, font=FONT_TITLE).grid(row=0,column=0,columnspan=2,
                                                   sticky="w",pady=(0,10))
        fields = [("INSTRUMENT",canal["instrumento"]),("MIC",canal["microfono"])]
        entries = {}
        for r,(lbl,val) in enumerate(fields,1):
            tk.Label(body,text=lbl,bg=BG_PANEL,fg=TEXT_LABEL,
                     font=FONT_MONO_SM).grid(row=r,column=0,sticky="e",padx=(0,8),pady=3)
            e = self._entry(body, width=22); e.insert(0,val)
            e.grid(row=r,column=1,sticky="ew",pady=3)
            entries[lbl] = e
        tk.Label(body,text="GROUP",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=3,column=0,sticky="e",padx=(0,8),pady=3)
        grp_c = self._combo(body, width=16)
        grp_c['values'] = GRUPOS_PREDEFINIDOS; grp_c.set(canal.get("grupo","OTHER"))
        grp_c.grid(row=3,column=1,sticky="w",pady=3)

        tk.Label(body,text="SIDE",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=4,column=0,sticky="e",padx=(0,8),pady=3)
        lado_c = self._combo(body, width=16)
        lado_c['values'] = ["—"] + LADOS_ESCENARIO
        lado_c.set(canal.get("lado","—") or "—")
        lado_c.grid(row=4,column=1,sticky="w",pady=3)

        tk.Frame(body,bg=BORDER,height=1).grid(row=5,column=0,columnspan=2,
                                                sticky="ew",pady=8)
        bf = tk.Frame(body, bg=BG_PANEL); bf.grid(row=6,column=0,columnspan=2,sticky="ew")
        bf.grid_columnconfigure(0,weight=1); bf.grid_columnconfigure(1,weight=1)
        tk.Button(bf, text="SAVE", bg=ORANGE, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=4,
                  command=lambda: self._guardar_edicion_canal(
                      canal_num, entries["INSTRUMENT"].get(),
                      entries["MIC"].get(), grp_c.get(), lado_c.get(), win)
                  ).grid(row=0,column=0,sticky="ew",padx=(0,4))
        tk.Button(bf, text="DELETE CHANNEL", bg=RED_DIM, fg=TEXT_MAIN,
                  font=FONT_MONO_B, relief="flat", cursor="hand2", padx=16, pady=4,
                  command=lambda: self._confirmar_eliminar_canal(canal_num, win)
                  ).grid(row=0,column=1,sticky="ew",padx=(4,0))

    def _guardar_edicion_canal(self, num, instrumento, microfono, grupo, lado, win):
        if self.banda_actual < len(self.bandas):
            canal = next(c for c in self.bandas[self.banda_actual]["canales"]
                         if c["numero"]==num)
            canal["instrumento"] = instrumento.strip().upper()
            canal["microfono"]   = microfono.strip().upper()
            canal["grupo"]       = grupo
            canal["lado"]        = lado if lado != "—" else ""
            self.actualizar_lista_canales()
            self.dibujar_escenario()
        win.destroy()

    def guardar_edicion_canal(self, num, instrumento, microfono, win):
        self._guardar_edicion_canal(num, instrumento, microfono, "OTHER", win)

    def eliminar_canal_seleccionado(self):
        if self.banda_actual >= len(self.bandas): return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("WARNING","Select a channel first.",parent=self.root); return
        item = sel[0]
        if item.startswith("wl_"):
            idx = int(item.split("_")[1])
            self._eliminar_wireless_idx(idx)
        else:
            self._confirmar_eliminar_canal(int(self.tree.item(item,"values")[0]))

    def _confirmar_eliminar_canal(self, canal_num, win=None):
        if not messagebox.askyesno("DELETE CHANNEL",
                                   f"Delete channel {canal_num:02d}?",
                                   parent=self.root): return
        banda = self.bandas[self.banda_actual]
        canal = next((c for c in banda["canales"] if c["numero"]==canal_num), None)
        if canal is None: return
        if canal["pachera_asignada"] and canal["input_pach"]:
            util = banda["pacheras_utilizacion"].get(canal["pachera_asignada"])
            if util:
                util["entradas"].pop(canal["input_pach"], None)
                if canal_num in util["canales_asignados"]:
                    util["canales_asignados"].remove(canal_num)
        banda["canales"].remove(canal)
        if win: win.destroy()
        self.actualizar_lista_canales()
        self.actualizar_lista_pacheras()
        self.dibujar_escenario()
        self._set_status(f"CH {canal_num:02d} DELETED")

    def _menu_contextual_canal(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return
        self.tree.selection_set(item)
        menu = tk.Menu(self.root, tearoff=0, bg=BG_PANEL, fg=TEXT_MAIN,
                       activebackground=ORANGE, activeforeground="#000",
                       font=FONT_MONO, relief="flat")
        if item.startswith("wl_"):
            idx = int(item.split("_")[1])
            w   = self.wireless[idx]
            menu.add_command(label=f"  ✎  Edit  {w['tipo']} · {w['modelo']}",
                             command=lambda: self._editar_wireless_por_idx(idx))
            menu.add_separator()
            menu.add_command(label=f"  ✕  Delete  W{w['canal']} {w['modelo']}",
                             command=lambda: self._eliminar_wireless_idx(idx))
        else:
            canal_num = int(self.tree.item(item,"values")[0])
            menu.add_command(label=f"  ✎  Edit  CH {canal_num:02d}",
                             command=lambda: self.editar_canal(None))
            menu.add_separator()
            menu.add_command(label=f"  ✕  Delete  CH {canal_num:02d}",
                             command=lambda: self._confirmar_eliminar_canal(canal_num))
        menu.tk_popup(event.x_root, event.y_root)

    # ── TARIMAS ──────────────────────────────────────────────────────────────
    def agregar_tarima(self):
        win = tk.Toplevel(self.root)
        win.title("NEW RISER")
        win.configure(bg=BG_BASE)
        win.resizable(False, False)
        win.grab_set()

        tk.Frame(win, bg=CYAN, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="NEW RISER", bg=BG_PANEL, fg=CYAN,
                 font=FONT_TITLE).grid(row=0, column=0, columnspan=2,
                                        sticky="w", pady=(0,12))
        tk.Label(body, text="RISER NAME", bg=BG_PANEL, fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=1, column=0, sticky="e", padx=(0,8), pady=4)
        entry = self._entry(body, width=22)
        entry.insert(0, "DRUM RISER")
        entry.select_range(0, tk.END)
        entry.grid(row=1, column=1, sticky="ew", pady=4)
        entry.focus_set()

        tk.Frame(body, bg=BORDER, height=1).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=10)

        bf = tk.Frame(body, bg=BG_PANEL)
        bf.grid(row=3, column=0, columnspan=2, sticky="ew")
        bf.grid_columnconfigure(0, weight=1); bf.grid_columnconfigure(1, weight=1)

        def _add():
            nombre = entry.get().strip().upper()
            if not nombre:
                messagebox.showerror("ERROR","Name cannot be empty.",parent=win); return
            self.tarimas.append({
                "nombre": nombre,
                "x": self.ancho_escenario/2 - 1,
                "y": self.profundidad_escenario/2 - 0.5,
                "w": 2.0, "h": 1.0
            })
            win.destroy()
            self.dibujar_escenario()
            self._set_status(f"RISER '{nombre}' ADDED")

        entry.bind("<Return>", lambda e: _add())
        tk.Button(bf, text="ADD RISER", bg=CYAN, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=_add).grid(row=0, column=0, sticky="ew", padx=(0,4))
        tk.Button(bf, text="CANCEL", bg=BG_WIDGET, fg=TEXT_DIM, font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=win.destroy).grid(row=0, column=1, sticky="ew", padx=(4,0))

    def eliminar_tarima_seleccionada(self):
        if not self.tarimas:
            messagebox.showwarning("WARNING","No risers to delete.",parent=self.root); return
        nombres = [t["nombre"] for t in self.tarimas]
        win = tk.Toplevel(self.root)
        win.title("DELETE RISER"); win.configure(bg=BG_BASE); win.resizable(False,False)
        tk.Frame(win, bg=ORANGE, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=16, pady=14)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text="SELECT RISER TO DELETE", bg=BG_PANEL,
                 fg=ORANGE, font=FONT_TITLE).pack(anchor="w", pady=(0,10))
        combo = self._combo(body, width=24)
        combo['values'] = nombres; combo.current(0)
        combo.pack(fill=tk.X, pady=4)
        def _do_delete():
            idx = nombres.index(combo.get())
            nombre = self.tarimas[idx]["nombre"]
            del self.tarimas[idx]
            win.destroy()
            self.dibujar_escenario()
            self._set_status(f"RISER '{nombre}' DELETED")
        tk.Button(body, text="DELETE", bg=RED_DIM, fg=TEXT_MAIN, font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=4,
                  command=_do_delete).pack(fill=tk.X, pady=(8,0))

    def _menu_mapa(self, event):
        """Click derecho en el mapa: menú de tarima (solo renombrar, no eliminar)"""
        sx, sy, mx, my = self._escalas()
        for i, t in enumerate(self.tarimas):
            tx1 = mx + t["x"]*sx
            ty1 = my + t["y"]*sy
            tx2 = tx1 + t["w"]*sx
            ty2 = ty1 + t["h"]*sy
            if tx1 <= event.x <= tx2 and ty1 <= event.y <= ty2:
                menu = tk.Menu(self.root, tearoff=0, bg=BG_PANEL, fg=TEXT_MAIN,
                               activebackground=ORANGE, activeforeground="#000",
                               font=FONT_MONO, relief="flat")
                menu.add_command(label=f"  ✎  Rename riser '{t['nombre']}'",
                                 command=lambda idx=i: self._renombrar_tarima(idx))
                menu.tk_popup(event.x_root, event.y_root)
                return

    def _eliminar_tarima_idx(self, idx):
        nombre = self.tarimas[idx]["nombre"]
        del self.tarimas[idx]
        self.dibujar_escenario()
        self._set_status(f"RISER '{nombre}' DELETED")

    def _renombrar_tarima(self, idx):
        win = tk.Toplevel(self.root)
        win.title("RENAME RISER")
        win.configure(bg=BG_BASE)
        win.resizable(False, False)
        win.grab_set()

        tk.Frame(win, bg=CYAN, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(body, text="RENAME RISER", bg=BG_PANEL, fg=CYAN,
                 font=FONT_TITLE).grid(row=0, column=0, columnspan=2,
                                        sticky="w", pady=(0,12))
        tk.Label(body, text="NEW NAME", bg=BG_PANEL, fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=1, column=0, sticky="e", padx=(0,8), pady=4)
        entry = self._entry(body, width=22)
        entry.insert(0, self.tarimas[idx]["nombre"])
        entry.select_range(0, tk.END)
        entry.grid(row=1, column=1, sticky="ew", pady=4)
        entry.focus_set()

        tk.Frame(body, bg=BORDER, height=1).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=10)

        def _save():
            nuevo = entry.get().strip().upper()
            if nuevo:
                self.tarimas[idx]["nombre"] = nuevo
                win.destroy()
                self.dibujar_escenario()

        entry.bind("<Return>", lambda e: _save())
        bf = tk.Frame(body, bg=BG_PANEL)
        bf.grid(row=3, column=0, columnspan=2, sticky="ew")
        bf.grid_columnconfigure(0, weight=1); bf.grid_columnconfigure(1, weight=1)
        tk.Button(bf, text="SAVE", bg=CYAN, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=_save).grid(row=0, column=0, sticky="ew", padx=(0,4))
        tk.Button(bf, text="CANCEL", bg=BG_WIDGET, fg=TEXT_DIM, font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=win.destroy).grid(row=0, column=1, sticky="ew", padx=(4,0))

    # ── WIRELESS ─────────────────────────────────────────────────────────────
    def _proximo_spl_wireless_libre(self):
        """Calcula el próximo número de SPL input libre considerando pacheras y wireless ya agregados"""
        # SPL ocupados por pacheras
        ocupados = set()
        offset = 0
        for p in self.pacheras:
            for n in range(1, p["capacidad"] + 1):
                ocupados.add(offset + n)
            offset += p["capacidad"]
        # SPL ocupados por wireless ya agregados
        for w in self.wireless:
            try:
                spl = int(w.get("spl_input", 0))
                if spl > 0: ocupados.add(spl)
            except: pass
        # Primer número libre
        siguiente = 1
        while siguiente in ocupados:
            siguiente += 1
        return siguiente

    def _actualizar_hint_spl(self):
        """Actualiza el hint mostrando el próximo SPL libre"""
        try:
            libre = self._proximo_spl_wireless_libre()
            self.wl_spl_hint.configure(text=f"next free: {libre}")
            if not self.wl_spl_entry.get():
                self.wl_spl_entry.delete(0, tk.END)
                self.wl_spl_entry.insert(0, str(libre))
        except: pass

    def agregar_wireless(self):
        try:
            ch    = self.wl_canal_entry.get().strip()
            tipo  = self.wl_tipo_combo.get()
            model = self.wl_modelo_entry.get().strip().upper()
            freq  = self.wl_freq_entry.get().strip()
            user  = self.wl_user_entry.get().strip().upper()
            notes = self.wl_notes_entry.get().strip()
            spl_raw = self.wl_spl_entry.get().strip()
            if not ch: raise ValueError("Channel # required")
            # Validar SPL input si se proveyó
            spl_input = 0
            if spl_raw:
                try:
                    spl_input = int(spl_raw)
                    if spl_input < 1: raise ValueError()
                except:
                    raise ValueError("SPL Input must be a positive number")
            self.wireless.append({
                "canal": ch, "tipo": tipo,
                "modelo": model or "—",
                "frecuencia": freq, "usuario": user, "notas": notes,
                "spl_input": spl_input,
                "x": self.ancho_escenario / 2,
                "y": self.profundidad_escenario / 2
            })
            for e in [self.wl_canal_entry, self.wl_modelo_entry,
                      self.wl_freq_entry, self.wl_user_entry,
                      self.wl_notes_entry, self.wl_spl_entry]:
                e.delete(0, tk.END)
            self.actualizar_lista_canales()
            self.dibujar_escenario()
            spl_txt = f"  SPL {spl_input}" if spl_input else ""
            self._set_status(f"WIRELESS W{ch} ADDED{spl_txt}  ·  drag to position")
            # Actualizar hint con próximo libre
            self._actualizar_hint_spl()
        except ValueError as e:
            messagebox.showerror("INPUT ERROR", str(e), parent=self.root)

    def actualizar_lista_wireless(self):
        """Delega en la lista unificada"""
        self.actualizar_lista_canales()

    def _editar_wireless_por_idx(self, idx):
        """Editar wireless desde la lista unificada"""
        w   = self.wireless[idx]
        win = tk.Toplevel(self.root)
        win.title("EDIT WIRELESS UNIT")
        win.configure(bg=BG_BASE); win.resizable(False,False); win.grab_set()
        tk.Frame(win, bg=CYAN, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text="EDIT WIRELESS UNIT", bg=BG_PANEL,
                 fg=CYAN, font=FONT_TITLE).grid(row=0,column=0,columnspan=2,
                                                 sticky="w",pady=(0,10))
        fields = [("CH #",w["canal"]),("MODEL",w["modelo"]),
                  ("SPL IN", str(w.get("spl_input","")) if w.get("spl_input") else ""),
                  ("FREQ (MHz)",w.get("frecuencia","")),
                  ("USER",w.get("usuario","")),("NOTES",w.get("notas",""))]
        entries = {}
        for r,(lbl,val) in enumerate(fields,1):
            tk.Label(body,text=lbl,bg=BG_PANEL,fg=TEXT_LABEL,
                     font=FONT_MONO_SM).grid(row=r,column=0,sticky="e",padx=(0,8),pady=3)
            e = self._entry(body,width=22); e.insert(0,val)
            e.grid(row=r,column=1,sticky="ew",pady=3)
            entries[lbl] = e
        tk.Label(body,text="TYPE",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=len(fields)+1,column=0,sticky="e",padx=(0,8),pady=3)
        tipo_c = self._combo(body,width=16)
        tipo_c['values'] = WIRELESS_TIPOS; tipo_c.set(w["tipo"])
        tipo_c.grid(row=len(fields)+1,column=1,sticky="w",pady=3)
        tk.Frame(body,bg=BORDER,height=1).grid(row=len(fields)+2,column=0,
                                                columnspan=2,sticky="ew",pady=8)
        bf = tk.Frame(body,bg=BG_PANEL)
        bf.grid(row=len(fields)+3,column=0,columnspan=2,sticky="ew")
        bf.grid_columnconfigure(0,weight=1); bf.grid_columnconfigure(1,weight=1)
        def _save():
            spl_raw = entries["SPL IN"].get().strip()
            spl_val = 0
            if spl_raw:
                try: spl_val = int(spl_raw)
                except: pass
            self.wireless[idx].update({
                "canal":      entries["CH #"].get().strip(),
                "modelo":     entries["MODEL"].get().strip().upper(),
                "spl_input":  spl_val,
                "frecuencia": entries["FREQ (MHz)"].get().strip(),
                "usuario":    entries["USER"].get().strip().upper(),
                "notas":      entries["NOTES"].get().strip(),
                "tipo":       tipo_c.get()})
            win.destroy()
            self.actualizar_lista_canales()
            self.dibujar_escenario()
        tk.Button(bf, text="SAVE", bg=CYAN, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=4,
                  command=_save).grid(row=0,column=0,sticky="ew",padx=(0,4))
        tk.Button(bf, text="DELETE", bg=RED_DIM, fg=TEXT_MAIN,
                  font=FONT_MONO_B, relief="flat", cursor="hand2", padx=16, pady=4,
                  command=lambda: self._eliminar_wireless_idx(idx, win)
                  ).grid(row=0,column=1,sticky="ew",padx=(4,0))

    def editar_wireless(self, event=None):
        sel = self.wl_tree.selection() if hasattr(self,'wl_tree') else []
        if not sel: return
        idx = self.wl_tree.index(sel[0])
        w   = self.wireless[idx]
        win = tk.Toplevel(self.root)
        win.title("EDIT WIRELESS UNIT")
        win.configure(bg=BG_BASE); win.resizable(False,False)
        tk.Frame(win, bg=CYAN, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text="EDIT WIRELESS UNIT", bg=BG_PANEL,
                 fg=CYAN, font=FONT_TITLE).grid(row=0,column=0,columnspan=2,
                                                 sticky="w",pady=(0,10))
        fields = [("CH #",w["canal"]),("BRAND/MODEL",w["modelo"]),
                  ("FREQ (MHz)",w["frecuencia"]),("USER",w["usuario"]),
                  ("NOTES",w["notas"])]
        entries = {}
        for r,(lbl,val) in enumerate(fields,1):
            tk.Label(body,text=lbl,bg=BG_PANEL,fg=TEXT_LABEL,
                     font=FONT_MONO_SM).grid(row=r,column=0,sticky="e",padx=(0,8),pady=3)
            e = self._entry(body,width=22); e.insert(0,val)
            e.grid(row=r,column=1,sticky="ew",pady=3)
            entries[lbl] = e
        tk.Label(body,text="TYPE",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_MONO_SM).grid(row=len(fields)+1,column=0,
                                          sticky="e",padx=(0,8),pady=3)
        tipo_c = self._combo(body,width=16)
        tipo_c['values'] = WIRELESS_TIPOS; tipo_c.set(w["tipo"])
        tipo_c.grid(row=len(fields)+1,column=1,sticky="w",pady=3)
        tk.Frame(body,bg=BORDER,height=1).grid(
            row=len(fields)+2,column=0,columnspan=2,sticky="ew",pady=8)
        bf = tk.Frame(body,bg=BG_PANEL)
        bf.grid(row=len(fields)+3,column=0,columnspan=2,sticky="ew")
        bf.grid_columnconfigure(0,weight=1); bf.grid_columnconfigure(1,weight=1)
        tk.Button(bf, text="SAVE", bg=CYAN, fg="#000", font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=16, pady=4,
                  command=lambda: self._guardar_edicion_wireless(
                      idx, entries, tipo_c.get(), win)
                  ).grid(row=0,column=0,sticky="ew",padx=(0,4))
        tk.Button(bf, text="DELETE", bg=RED_DIM, fg=TEXT_MAIN,
                  font=FONT_MONO_B, relief="flat", cursor="hand2", padx=16, pady=4,
                  command=lambda: self._eliminar_wireless_idx(idx, win)
                  ).grid(row=0,column=1,sticky="ew",padx=(4,0))

    def _guardar_edicion_wireless(self, idx, entries, tipo, win):
        self.wireless[idx].update({
            "canal":   entries["CH #"].get().strip(),
            "modelo":  entries["BRAND/MODEL"].get().strip().upper(),
            "frecuencia": entries["FREQ (MHz)"].get().strip(),
            "usuario": entries["USER"].get().strip().upper(),
            "notas":   entries["NOTES"].get().strip(),
            "tipo":    tipo})
        win.destroy()
        self.actualizar_lista_canales()
        self.dibujar_escenario()

    def eliminar_wireless_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("WARNING","Select a wireless unit first.",parent=self.root); return
        item = sel[0]
        if not item.startswith("wl_"):
            messagebox.showwarning("WARNING","Select a wireless unit (W prefix) first.",parent=self.root); return
        self._eliminar_wireless_idx(int(item.split("_")[1]))

    def _eliminar_wireless_idx(self, idx, win=None):
        modelo = self.wireless[idx]["modelo"]
        if not messagebox.askyesno("DELETE WIRELESS",
                                   f"Delete '{modelo}'?",parent=self.root): return
        del self.wireless[idx]
        if win: win.destroy()
        self.actualizar_lista_canales()
        self.dibujar_escenario()
        self._set_status(f"WIRELESS '{modelo}' DELETED")

    def _menu_contextual_wireless(self, event):
        """Legacy: redirige al menu contextual unificado"""
        self._menu_contextual_canal(event)

    def verificar_conflictos_rf(self):
        """Detecta frecuencias duplicadas o muy cercanas (<1 MHz)"""
        freqs = []
        for w in self.wireless:
            try: freqs.append((float(w["frecuencia"]), w["modelo"], w["canal"]))
            except: pass
        freqs.sort()
        conflictos = []
        for i in range(len(freqs)-1):
            diff = abs(freqs[i+1][0] - freqs[i][0])
            if diff < 1.0:
                conflictos.append(
                    f"  {freqs[i][1]} (CH{freqs[i][2]})  ↔  "
                    f"{freqs[i+1][1]} (CH{freqs[i+1][2]})  Δ={diff:.3f} MHz")
        win = tk.Toplevel(self.root)
        win.title("RF CONFLICT CHECK"); win.configure(bg=BG_BASE)
        tk.Frame(win, bg=YELLOW, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=16, pady=14)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text="RF CONFLICT CHECK", bg=BG_PANEL,
                 fg=YELLOW, font=FONT_TITLE).pack(anchor="w", pady=(0,8))
        if conflictos:
            tk.Label(body, text=f"⚠  {len(conflictos)} potential conflict(s) found:",
                     bg=BG_PANEL, fg=RED, font=FONT_MONO_B).pack(anchor="w", pady=(0,6))
            text = tk.Text(win, bg=BG_WIDGET, fg=RED, font=FONT_MONO,
                           relief="flat", padx=12, pady=8, width=60, height=10)
            text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,8))
            for c in conflictos: text.insert(tk.END, c+"\n")
            text.configure(state="disabled")
        else:
            tk.Label(body, text="✓  No conflicts detected.", bg=BG_PANEL,
                     fg=GREEN, font=FONT_MONO_B).pack(anchor="w")
        tk.Button(body, text="CLOSE", bg=BORDER, fg=TEXT_MAIN, font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=20, pady=4,
                  command=win.destroy).pack(pady=(12,0))

    def mostrar_reporte_wireless(self):
        win = tk.Toplevel(self.root)
        win.title("WIRELESS REPORT"); win.configure(bg=BG_BASE)
        tk.Frame(win, bg=CYAN, height=2).pack(fill=tk.X)
        body = tk.Frame(win, bg=BG_PANEL, padx=0, pady=0)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(body, text="  WIRELESS / RF REPORT", bg=BG_PANEL, fg=CYAN,
                 font=FONT_TITLE, anchor="w").pack(fill=tk.X, pady=(10,6), padx=12)
        text = tk.Text(win, bg=BG_WIDGET, fg=TEXT_MAIN, font=FONT_MONO,
                       relief="flat", padx=12, pady=8, width=60, height=24)
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,8))
        if not self.wireless:
            text.insert(tk.END,"  No wireless units registered.")
        else:
            by_type = defaultdict(list)
            for w in self.wireless: by_type[w["tipo"]].append(w)
            for tipo in sorted(by_type.keys()):
                text.insert(tk.END, f"\n◈ {tipo}\n")
                for w in by_type[tipo]:
                    text.insert(tk.END,
                        f"  CH{w['canal']:>3}  {w['modelo']:<16}  "
                        f"{w['frecuencia']:>10} MHz  {w['usuario']}\n")
        text.configure(state="disabled")
        tk.Button(win, text="CLOSE", bg=BORDER, fg=TEXT_MAIN, font=FONT_MONO_B,
                  relief="flat", cursor="hand2", padx=20, pady=4,
                  command=win.destroy).pack(pady=(0,10))

    # ── MAPA: DIBUJO ─────────────────────────────────────────────────────────
    def dibujar_escenario(self):
        c = self.mapa_canvas
        c.delete("all")
        cw = c.winfo_width()  or 700
        ch = c.winfo_height() or 460
        # Fix 2: mapa ocupa todo el canvas disponible
        sx = (cw - 60) / self.ancho_escenario  * self.zoom_level
        sy = (ch - 70) / self.profundidad_escenario * self.zoom_level
        mx, my = 30, 35

        x1,y1 = mx, my
        x2,y2 = mx + self.ancho_escenario*sx, my + self.profundidad_escenario*sy

        # Escenario
        c.create_rectangle(x1,y1,x2,y2, outline=BORDER_LIT, fill="#0D0F11", width=2)
        for i in range(self.ancho_escenario+1):
            xg=mx+i*sx; c.create_line(xg,y1,xg,y2,fill="#1A1E24",width=1)
        for j in range(self.profundidad_escenario+1):
            yg=my+j*sy; c.create_line(x1,yg,x2,yg,fill="#1A1E24",width=1)
        c.create_text(x1+6,y1+12,text="▲ STAGE FRONT",anchor="nw",fill=TEXT_DIM,font=FONT_MONO_SM)
        c.create_text(x1+6,y2-12,text="▼ STAGE REAR", anchor="sw",fill=TEXT_DIM,font=FONT_MONO_SM)

        # Etiquetas de lados (punto 4)
        lados_rel = {"L":0.09,"L2":0.24,"CENTER":0.44,"C2":0.54,"R2":0.74,"R":0.9}
        for lado, rel in lados_rel.items():
            xg = x1 + (x2-x1)*rel
            c.create_text(xg, y1-10, text=lado, fill=BORDER_LIT, font=FONT_MONO_SM, anchor="s")

        # Tarimas
        for t in self.tarimas:
            tx1=mx+t["x"]*sx; ty1=my+t["y"]*sy
            tx2=tx1+t["w"]*sx; ty2=ty1+t["h"]*sy
            p_riser = self._pachera_en_tarima(t)
            riser_color = ORANGE if p_riser else CYAN
            c.create_rectangle(tx1,ty1,tx2,ty2,fill="#0D2030",outline=riser_color,width=2,
                               tags=f"tarima_{t['nombre']}")
            label_riser = t["nombre"]
            if p_riser: label_riser += f"  →  {p_riser['nombre']}"
            c.create_text((tx1+tx2)/2,(ty1+ty2)/2,text=label_riser,
                          fill=riser_color,font=FONT_MONO_SM)
            # Handle de resize
            c.create_rectangle(tx2-5,ty2-5,tx2+5,ty2+5,fill=riser_color,outline="#000",width=1)

        # Pacheras
        for p in self.pacheras:
            px=mx+p["x"]*sx; py=my+p["y"]*sy
            util=0
            if self.banda_actual < len(self.bandas):
                util=len(self.bandas[self.banda_actual]["pacheras_utilizacion"]
                         .get(p["nombre"],{}).get("canales_asignados",[]))
            grp = p.get("grupo_exclusivo","ANY")
            es_wl_bay = p.get("es_wireless", False)
            if es_wl_bay:
                p_color = CYAN
                icono = "◎"
            else:
                p_color = GRUPO_COLORES.get(grp, BLUE_ACCENT) if grp!="ANY" else BLUE_ACCENT
                icono = "⬡"
            fill_c = p_color if util < p["capacidad"] else "#555"
            r=12
            c.create_oval(px-r,py-r,px+r,py+r,fill=fill_c,outline="#000",width=1,
                          tags=f"pachera_{p['nombre']}")
            c.create_text(px,py,text=icono,fill="#000",font=("Courier New",9,"bold"))
            spl_s = self._calcular_offset_splitter(p["nombre"]) + 1
            spl_e = spl_s + p["capacidad"] - 1
            wl_tag = " ◎WL" if es_wl_bay else ""
            c.create_text(px,py-r-8,
                          text=f"{p['nombre']}{wl_tag} [{spl_s}-{spl_e}] {util}/{p['capacidad']}",
                          fill=p_color,font=FONT_MONO_SM,anchor="s")

        # Canales
        if self.banda_actual < len(self.bandas):
            for canal in self.bandas[self.banda_actual]["canales"]:
                cx_=mx+canal["x"]*sx; cy_=my+canal["y"]*sy
                asignado=bool(canal["pachera_asignada"])
                grupo=canal.get("grupo","OTHER")
                if self.mostrar_grupos:
                    color = GRUPO_COLORES.get(grupo, GREEN) if asignado else RED
                else:
                    color = GREEN if asignado else RED
                s_r=8
                if asignado:
                    p=next((p for p in self.pacheras if p["nombre"]==canal["pachera_asignada"]),None)
                    if p:
                        ppx=mx+p["x"]*sx; ppy=my+p["y"]*sy
                        c.create_line(cx_,cy_,ppx,ppy,fill=GREEN_DIM,width=1,dash=(3,3))
                c.create_rectangle(cx_-s_r,cy_-s_r,cx_+s_r,cy_+s_r,
                                   fill=color,outline="#000",width=1,
                                   tags=f"canal_{canal['numero']}")
                c.create_text(cx_,cy_,text=f"{canal['numero']:02d}",
                              fill="#000",font=("Courier New",8,"bold"))
                inst_txt = canal["instrumento"][:6]
                spl_num  = self._input_splitter(canal)
                if spl_num:
                    label = f"SPL{spl_num}·{inst_txt}"
                else:
                    label = inst_txt
                c.create_text(cx_,cy_+s_r+7,text=label,
                              fill=TEXT_DIM,font=("Courier New",7),anchor="n")

        # Wireless: posicionados libremente en el mapa (sin zona fija)
        for i, w in enumerate(self.wireless):
            wx_ = mx + w.get("x", self.ancho_escenario/2) * sx
            wy_ = my + w.get("y", self.profundidad_escenario/2) * sy
            is_iem = "IEM" in w["tipo"].upper()
            wcolor = CYAN if is_iem else YELLOW
            wr = 10
            c.create_oval(wx_-wr,wy_-wr,wx_+wr,wy_+wr,
                          fill=wcolor,outline="#000",width=1,
                          tags=f"wireless_{i}")
            c.create_text(wx_,wy_,text="◎" if is_iem else "♪",
                          fill="#000",font=("Courier New",9,"bold"))
            modelo_txt = w["modelo"][:5] if w.get("modelo") and w["modelo"]!="—" else w["tipo"][:5]
            spl_wl = w.get("spl_input", 0)
            spl_wl_txt = f"SPL{spl_wl}·" if spl_wl else ""
            c.create_text(wx_,wy_+wr+7,
                          text=f"W{w['canal']}·{spl_wl_txt}{modelo_txt}",
                          fill=wcolor,font=("Courier New",7),anchor="n")

        c.configure(scrollregion=(0,0,
                                   mx+self.ancho_escenario*sx+40,
                                   my+self.profundidad_escenario*sy+50))

    # ── MAPA: INTERACCIÓN ────────────────────────────────────────────────────
    def _escalas(self):
        cw = self.mapa_canvas.winfo_width()  or 700
        ch = self.mapa_canvas.winfo_height() or 460
        sx = (cw - 60) / self.ancho_escenario      * self.zoom_level
        sy = (ch - 70) / self.profundidad_escenario * self.zoom_level
        return sx, sy, 30, 35

    def iniciar_arrastre(self, event):
        sx,sy,mx,my=self._escalas()

        # PRIORIDAD 1: Pacheras (círculos de patch bay)
        for p in self.pacheras:
            px,py=mx+p["x"]*sx,my+p["y"]*sy
            if abs(event.x-px)<=13 and abs(event.y-py)<=13:
                self.pachera_seleccionada=p
                self.drag_data={"x":event.x,"y":event.y,"item":"pachera"}; return

        # PRIORIDAD 2: Canales (siempre antes que tarimas)
        if self.banda_actual < len(self.bandas):
            for canal in self.bandas[self.banda_actual]["canales"]:
                cx,cy=mx+canal["x"]*sx,my+canal["y"]*sy
                if abs(event.x-cx)<=9 and abs(event.y-cy)<=9:
                    self.canal_seleccionado=canal
                    self.drag_data={"x":event.x,"y":event.y,"item":"canal"}; return

        # PRIORIDAD 3: Wireless (siempre antes que tarimas)
        for i, w in enumerate(self.wireless):
            wx_=mx+w.get("x", self.ancho_escenario/2)*sx
            wy_=my+w.get("y", self.profundidad_escenario/2)*sy
            if abs(event.x-wx_)<=12 and abs(event.y-wy_)<=12:
                self.wireless_seleccionado=w
                self.drag_data={"x":event.x,"y":event.y,"item":"wireless"}; return

        # PRIORIDAD 4: Tarimas (solo si no hay canal/wireless encima)
        # El handle de resize (esquina) tiene prioridad sobre el interior
        for t in self.tarimas:
            tx1=mx+t["x"]*sx; ty1=my+t["y"]*sy
            tx2=tx1+t["w"]*sx; ty2=ty1+t["h"]*sy
            if abs(event.x-tx2)<=10 and abs(event.y-ty2)<=10:
                self.tarima_seleccionada=t
                self.drag_data={"x":event.x,"y":event.y,"item":"tarima_resize"}; return
            if tx1<=event.x<=tx2 and ty1<=event.y<=ty2:
                self.tarima_seleccionada=t
                self.drag_data={"x":event.x,"y":event.y,"item":"tarima_move"}; return

    def arrastrar_item(self, event):
        sx,sy,_,_=self._escalas()
        dx=event.x-self.drag_data["x"]; dy=event.y-self.drag_data["y"]
        item=self.drag_data["item"]
        if item=="pachera" and self.pachera_seleccionada:
            obj=self.pachera_seleccionada
            obj["x"]=max(0,min(self.ancho_escenario,    obj["x"]+dx/sx))
            obj["y"]=max(0,min(self.profundidad_escenario,obj["y"]+dy/sy))
        elif item=="wireless" and self.wireless_seleccionado:
            w=self.wireless_seleccionado
            w["x"]=max(0, min(self.ancho_escenario, w.get("x", self.ancho_escenario/2)+dx/sx))
            w["y"]=max(0, min(self.profundidad_escenario, w.get("y", self.profundidad_escenario/2)+dy/sy))
        elif item=="tarima_move" and self.tarima_seleccionada:
            t=self.tarima_seleccionada
            t["x"]=max(0,min(self.ancho_escenario-t["w"],    t["x"]+dx/sx))
            t["y"]=max(0,min(self.profundidad_escenario-t["h"],t["y"]+dy/sy))
        elif item=="tarima_resize" and self.tarima_seleccionada:
            t=self.tarima_seleccionada
            t["w"]=max(0.5,min(self.ancho_escenario-t["x"],    t["w"]+dx/sx))
            t["h"]=max(0.3,min(self.profundidad_escenario-t["y"],t["h"]+dy/sy))
        elif item=="canal" and self.canal_seleccionado:
            obj=self.canal_seleccionado
            obj["x"]=max(0,min(self.ancho_escenario,    obj["x"]+dx/sx))
            obj["y"]=max(0,min(self.profundidad_escenario,obj["y"]+dy/sy))
            obj["posicion_predefinida"]="CUSTOM"
        self.drag_data["x"]=event.x; self.drag_data["y"]=event.y
        self.dibujar_escenario()

    def soltar_item(self, event):
        self.pachera_seleccionada  = None
        self.canal_seleccionado    = None
        self.tarima_seleccionada   = None
        self.wireless_seleccionado = None
        self.drag_data = {"x":0,"y":0,"item":None}

    def zoom(self, event):
        self.zoom_level*=1.1 if event.delta>0 else 0.9
        self.zoom_level=max(0.5,min(3.0,self.zoom_level))
        self.dibujar_escenario()

    def iniciar_pan(self, event): self.pan_start=(event.x,event.y)
    def pan(self, event):
        if self.pan_start:
            dx=event.x-self.pan_start[0]; dy=event.y-self.pan_start[1]
            self.mapa_canvas.scan_dragto(-dx,-dy,gain=1)
            self.pan_start=(event.x,event.y)

    # ── ALGORITMO ASIGNACIÓN ─────────────────────────────────────────────────
    def calcular_conexiones_mejorado(self):
        if not self.pacheras or not (self.banda_actual<len(self.bandas)
                                     and self.bandas[self.banda_actual]["canales"]):
            messagebox.showwarning("WARNING","Need at least one bay and one channel.",
                                   parent=self.root); return
        banda=self.bandas[self.banda_actual]
        for pnom in banda["pacheras_utilizacion"]:
            banda["pacheras_utilizacion"][pnom]={"canales_asignados":[],"entradas":{}}
        for canal in banda["canales"]:
            canal["pachera_asignada"]=None; canal["input_pach"]=None

        if self.remember_pach:
            preferencias={}
            for otra in self.bandas:
                if otra is banda: continue
                for co in otra["canales"]:
                    if co["pachera_asignada"] and co["input_pach"]:
                        inst=co["instrumento"]
                        if inst not in preferencias:
                            preferencias[inst]={"pachera":co["pachera_asignada"],
                                                "input":co["input_pach"],"votos":1}
                        else: preferencias[inst]["votos"]+=1
            for canal in banda["canales"]:
                if canal["instrumento"] not in preferencias: continue
                pref=preferencias[canal["instrumento"]]
                pachera=next((p for p in self.pacheras if p["nombre"]==pref["pachera"]),None)
                if pachera is None: continue
                util=banda["pacheras_utilizacion"][pachera["nombre"]]
                if (pref["input"] not in util["entradas"]
                        and len(util["canales_asignados"])<pachera["capacidad"]):
                    canal["pachera_asignada"]=pachera["nombre"]
                    canal["input_pach"]=pref["input"]
                    util["entradas"][pref["input"]]=canal["numero"]
                    util["canales_asignados"].append(canal["numero"])

        for canal in sorted([c for c in banda["canales"] if not c["pachera_asignada"]],
                            key=lambda x: x["numero"]):
            mejor,min_d=None,float("inf")

            # Punto 2: si el canal está en un riser que tiene una pachera, priorizar esa pachera
            tarima = self._tarima_del_canal(canal)
            pachera_riser = self._pachera_en_tarima(tarima) if tarima else None
            if pachera_riser:
                util_riser = banda["pacheras_utilizacion"].get(pachera_riser["nombre"])
                if util_riser and len(util_riser["canales_asignados"]) < pachera_riser["capacidad"]:
                    mejor = pachera_riser

            # Si no hay pachera en el riser, buscar la más cercana
            if not mejor:
                for p in self.pacheras:
                    if len(banda["pacheras_utilizacion"][p["nombre"]]["canales_asignados"])>=p["capacidad"]:
                        continue
                    d=math.hypot(canal["x"]-p["x"],canal["y"]-p["y"])
                    if d<min_d: mejor,min_d=p,d

            if mejor:
                canal["pachera_asignada"]=mejor["nombre"]
                util=banda["pacheras_utilizacion"][mejor["nombre"]]
                for n in range(1,mejor["capacidad"]+1):
                    if str(n) not in util["entradas"]:
                        util["entradas"][str(n)]=canal["numero"]
                        util["canales_asignados"].append(canal["numero"])
                        canal["input_pach"]=str(n); break

        self.actualizar_lista_canales()
        self.dibujar_escenario()
        self._set_status("ASSIGN COMPLETE")
        self.mostrar_estadisticas()

    def asignar_por_grupos(self):
        """Asigna cada canal a la pachera con grupo_exclusivo matching, o la más cercana"""
        if not self.pacheras or not (self.banda_actual<len(self.bandas)
                                     and self.bandas[self.banda_actual]["canales"]):
            messagebox.showwarning("WARNING","Need at least one bay and one channel.",
                                   parent=self.root); return
        banda=self.bandas[self.banda_actual]
        for pnom in banda["pacheras_utilizacion"]:
            banda["pacheras_utilizacion"][pnom]={"canales_asignados":[],"entradas":{}}
        for canal in banda["canales"]:
            canal["pachera_asignada"]=None; canal["input_pach"]=None

        for canal in sorted(banda["canales"],key=lambda x: x["numero"]):
            grupo_canal=canal.get("grupo","OTHER")
            # 1) Buscar pacheras con grupo_exclusivo matching y con capacidad
            candidatos=[p for p in self.pacheras
                        if p.get("grupo_exclusivo","ANY")==grupo_canal
                        and len(banda["pacheras_utilizacion"][p["nombre"]]["canales_asignados"])<p["capacidad"]]
            # 2) Si no hay, buscar pacheras ANY con capacidad
            if not candidatos:
                candidatos=[p for p in self.pacheras
                            if p.get("grupo_exclusivo","ANY")=="ANY"
                            and len(banda["pacheras_utilizacion"][p["nombre"]]["canales_asignados"])<p["capacidad"]]
            # 3) Si aún no hay, cualquier pachera con capacidad
            if not candidatos:
                candidatos=[p for p in self.pacheras
                            if len(banda["pacheras_utilizacion"][p["nombre"]]["canales_asignados"])<p["capacidad"]]
            if not candidatos: continue

            # Punto 2: si el canal está en un riser con pachera, usar esa primero
            tarima = self._tarima_del_canal(canal)
            pachera_riser = self._pachera_en_tarima(tarima) if tarima else None
            if pachera_riser and pachera_riser in candidatos:
                mejor = pachera_riser
            else:
                mejor=min(candidatos,key=lambda p:math.hypot(canal["x"]-p["x"],canal["y"]-p["y"]))
            canal["pachera_asignada"]=mejor["nombre"]
            util=banda["pacheras_utilizacion"][mejor["nombre"]]
            for n in range(1,mejor["capacidad"]+1):
                if str(n) not in util["entradas"]:
                    util["entradas"][str(n)]=canal["numero"]
                    util["canales_asignados"].append(canal["numero"])
                    canal["input_pach"]=str(n); break

        self.actualizar_lista_canales()
        self.dibujar_escenario()
        self._set_status("GROUP ASSIGN COMPLETE")
        self.mostrar_estadisticas()

    # ── ACCIONES ─────────────────────────────────────────────────────────────
    def toggle_remember_pach(self):
        self.remember_pach=not self.remember_pach
        if self.remember_pach:
            self.btn_remember.configure(text="◉ REMEMBER: ON",bg=ORANGE,fg="#000")
        else:
            self.btn_remember.configure(text="◎ REMEMBER: OFF",bg=BG_WIDGET,fg=TEXT_DIM)

    def cancelar_asignaciones(self):
        if messagebox.askyesno("CLEAR ASSIGNMENTS",
                               "Clear all assignments for current band?",parent=self.root):
            if self.banda_actual<len(self.bandas):
                banda=self.bandas[self.banda_actual]
                for pnom in banda["pacheras_utilizacion"]:
                    banda["pacheras_utilizacion"][pnom]={"canales_asignados":[],"entradas":{}}
                for canal in banda["canales"]:
                    canal["pachera_asignada"]=None; canal["input_pach"]=None
                self.actualizar_lista_canales(); self.dibujar_escenario()
                self._set_status("ASSIGNMENTS CLEARED")

    def limpiar_todo(self):
        if messagebox.askyesno("RESET ALL","Delete ALL channels, bays, risers and bands?",
                               parent=self.root):
            self.pacheras=[]; self.tarimas=[]
            self.bandas=[{"nombre":"BAND 01","canales":[],"wireless":[],"pacheras_utilizacion":{}}]
            self.banda_actual=0; self.ultimo_canal_global=0
            self.actualizar_pestanas_bandas(); self.dibujar_escenario()
            self.actualizar_lista_canales()
            self._set_status("RESET COMPLETE")

    def nueva_configuracion(self):
        if messagebox.askyesno("NEW CONFIG","Create new config? Unsaved data will be lost.",
                               parent=self.root):
            self.pacheras=[]; self.tarimas=[]
            self.bandas=[{"nombre":"BAND 01","canales":[],"wireless":[],"pacheras_utilizacion":{}}]
            self.banda_actual=0; self.ultimo_canal_global=0
            for e in [self.pachera_nombre_entry,self.pachera_cantidad_entry,
                      self.canal_num_entry,self.instrumento_entry,self.microfono_entry]:
                e.delete(0,tk.END)
            self.actualizar_pestanas_bandas(); self.dibujar_escenario()
            self.actualizar_lista_canales()
            self._set_status("NEW CONFIG")

    def guardar_configuracion(self):
        fp=filedialog.asksaveasfilename(defaultextension=".json",
            filetypes=[("JSON files","*.json"),("All files","*.*")],
            title="Save configuration")
        if not fp: return
        config={"pacheras":self.pacheras,"bandas":self.bandas,
                "tarimas":self.tarimas,"wireless":self.wireless,
                "ancho_escenario":self.ancho_escenario,
                "profundidad_escenario":self.profundidad_escenario,
                "posiciones_predefinidas":self.posiciones_predefinidas,
                "ultimo_canal_global":self.ultimo_canal_global,
                "remember_pach":self.remember_pach}
        try:
            with open(fp,"w") as f: json.dump(config,f,indent=4)
            self._set_status("CONFIG SAVED")
        except Exception as e:
            messagebox.showerror("SAVE ERROR",str(e),parent=self.root)

    def cargar_configuracion(self):
        fp=filedialog.askopenfilename(filetypes=[("JSON files","*.json"),("All files","*.*")],
            title="Load configuration")
        if not fp: return
        try:
            with open(fp,"r") as f: config=json.load(f)
            self.pacheras  =config.get("pacheras",[])
            self.bandas    =config.get("bandas",[{"nombre":"BAND 01","canales":[],
                                                   "wireless":[],"pacheras_utilizacion":{}}])
            self.tarimas   =config.get("tarimas",[])
            self.banda_actual=0
            # Asegurar que cada banda tenga lista wireless
            for banda in self.bandas:
                banda.setdefault("wireless", [])
            self.ancho_escenario     =config.get("ancho_escenario",10)
            self.profundidad_escenario=config.get("profundidad_escenario",6)
            self.posiciones_predefinidas=config.get("posiciones_predefinidas",[])
            self.ultimo_canal_global =config.get("ultimo_canal_global",0)
            self.remember_pach       =config.get("remember_pach",False)
            if self.remember_pach:
                self.btn_remember.configure(text="◉ REMEMBER: ON",bg=ORANGE,fg="#000")
            else:
                self.btn_remember.configure(text="◎ REMEMBER: OFF",bg=BG_WIDGET,fg=TEXT_DIM)
            for banda in self.bandas:
                if "pacheras_utilizacion" not in banda:
                    banda["pacheras_utilizacion"]={
                        p["nombre"]:{"canales_asignados":[],"entradas":{}}
                        for p in self.pacheras}
                else:
                    for p in self.pacheras:
                        if p["nombre"] not in banda["pacheras_utilizacion"]:
                            banda["pacheras_utilizacion"][p["nombre"]]={
                                "canales_asignados":[],"entradas":{}}
            # posiciones_predefinidas cargadas, no hay combo en UI
            self.actualizar_pestanas_bandas(); self.dibujar_escenario()
            self.actualizar_lista_canales()
            self._set_status("CONFIG LOADED")
        except Exception as e:
            messagebox.showerror("LOAD ERROR",str(e),parent=self.root)
            self.generar_posiciones_predefinidas()

    # ── ESTADÍSTICAS ─────────────────────────────────────────────────────────
    def mostrar_estadisticas(self):
        if self.banda_actual>=len(self.bandas): return
        banda=self.bandas[self.banda_actual]
        total=len(banda["canales"])
        asignados=sum(1 for c in banda["canales"] if c["pachera_asignada"])
        win=tk.Toplevel(self.root); win.title("STATISTICS")
        win.configure(bg=BG_BASE); win.resizable(False,False)
        tk.Frame(win,bg=ORANGE,height=2).pack(fill=tk.X)
        body=tk.Frame(win,bg=BG_PANEL,padx=20,pady=16)
        body.pack(fill=tk.BOTH,expand=True)
        tk.Label(body,text=f"BAND:  {banda['nombre']}",bg=BG_PANEL,
                 fg=ORANGE,font=FONT_TITLE).pack(anchor="w",pady=(0,10))
        for label,val,color in [
            ("TOTAL CHANNELS",total,TEXT_MAIN),
            ("ASSIGNED",asignados,GREEN),
            ("UNASSIGNED",total-asignados,RED if total-asignados else TEXT_DIM)]:
            row=tk.Frame(body,bg=BG_PANEL); row.pack(fill=tk.X,pady=1)
            tk.Label(row,text=label,bg=BG_PANEL,fg=TEXT_DIM,
                     font=FONT_MONO_SM,width=20,anchor="w").pack(side=tk.LEFT)
            tk.Label(row,text=str(val),bg=BG_PANEL,fg=color,
                     font=FONT_MONO_B).pack(side=tk.LEFT)

        # Por grupo
        tk.Frame(body,bg=BORDER,height=1).pack(fill=tk.X,pady=8)
        tk.Label(body,text="BY GROUP",bg=BG_PANEL,fg=TEXT_LABEL,font=FONT_HDR
                 ).pack(anchor="w",pady=(0,4))
        grupos_count=defaultdict(int)
        for canal in banda["canales"]: grupos_count[canal.get("grupo","OTHER")]+=1
        for grupo,count in sorted(grupos_count.items()):
            row=tk.Frame(body,bg=BG_PANEL); row.pack(fill=tk.X,pady=1)
            color=GRUPO_COLORES.get(grupo,TEXT_DIM)
            tk.Label(row,text=grupo,bg=BG_PANEL,fg=color,
                     font=FONT_MONO_SM,width=10,anchor="w").pack(side=tk.LEFT)
            tk.Label(row,text=str(count),bg=BG_PANEL,fg=color,
                     font=FONT_MONO_B).pack(side=tk.LEFT)

        tk.Frame(body,bg=BORDER,height=1).pack(fill=tk.X,pady=8)
        tk.Label(body,text="PATCH BAY USAGE",bg=BG_PANEL,fg=TEXT_LABEL,
                 font=FONT_HDR).pack(anchor="w",pady=(0,4))
        for p in self.pacheras:
            util=len(banda["pacheras_utilizacion"].get(p["nombre"],{})
                     .get("canales_asignados",[]))
            pct=int(util/p["capacidad"]*100) if p["capacidad"] else 0
            color=GREEN if pct<100 else RED
            row=tk.Frame(body,bg=BG_PANEL); row.pack(fill=tk.X,pady=2)
            tk.Label(row,text=p["nombre"],bg=BG_PANEL,fg=TEXT_MAIN,
                     font=FONT_MONO_SM,width=14,anchor="w").pack(side=tk.LEFT)
            bg_bar=tk.Frame(row,bg=BG_WIDGET,height=12,width=120)
            bg_bar.pack(side=tk.LEFT,padx=6); bg_bar.pack_propagate(False)
            tk.Frame(bg_bar,bg=color,height=12,width=int(120*pct/100)).pack(side=tk.LEFT)
            tk.Label(row,text=f"{util}/{p['capacidad']}",bg=BG_PANEL,
                     fg=color,font=FONT_MONO_SM).pack(side=tk.LEFT)
        tk.Button(body,text="CLOSE",bg=BORDER,fg=TEXT_MAIN,font=FONT_MONO_B,
                  relief="flat",cursor="hand2",padx=20,pady=4,
                  command=win.destroy).pack(pady=(12,0))

    def mostrar_conexiones(self):
        if self.banda_actual>=len(self.bandas): return
        banda=self.bandas[self.banda_actual]
        conexiones=defaultdict(list)
        for canal in banda["canales"]:
            if canal["pachera_asignada"] and canal["input_pach"]:
                spl_num = self._input_splitter(canal)
                spl_txt = f"SPL {spl_num:>3}" if spl_num else "       "
                conexiones[canal["pachera_asignada"]].append(
                    f"  CH {canal['numero']:02d}  [{canal.get('grupo','???'):6}]  "
                    f"{canal['instrumento']:<14}  →  IN {canal['input_pach']:<3}  {spl_txt}")
        win=tk.Toplevel(self.root); win.title("CONNECTION REPORT")
        win.configure(bg=BG_BASE)
        tk.Frame(win,bg=ORANGE,height=2).pack(fill=tk.X)
        body=tk.Frame(win,bg=BG_PANEL,padx=0,pady=0)
        body.pack(fill=tk.BOTH,expand=True)
        tk.Label(body,text=f"  CONNECTION REPORT  ──  {banda['nombre']}",
                 bg=BG_PANEL,fg=ORANGE,font=FONT_TITLE,anchor="w"
                 ).pack(fill=tk.X,pady=(10,6),padx=12)
        text=tk.Text(win,bg=BG_WIDGET,fg=TEXT_MAIN,font=FONT_MONO,
                     relief="flat",padx=12,pady=8,insertbackground=ORANGE,
                     width=62,height=24)
        text.pack(fill=tk.BOTH,expand=True,padx=12,pady=(0,8))
        if conexiones:
            for pnom in sorted(conexiones.keys()):
                text.insert(tk.END,f"\n◈ {pnom}\n")
                text.insert(tk.END,"\n".join(sorted(conexiones[pnom]))+"\n")
        else:
            text.insert(tk.END,"  No assignments found.")
        text.configure(state="disabled")
        tk.Button(win,text="CLOSE",bg=BORDER,fg=TEXT_MAIN,font=FONT_MONO_B,
                  relief="flat",cursor="hand2",padx=20,pady=4,
                  command=win.destroy).pack(pady=(0,10))


if __name__ == "__main__":
    root = tk.Tk()
    app  = AplicacionAudioEscenario(root)
    root.mainloop()
