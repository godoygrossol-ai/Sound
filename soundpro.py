import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import math
import json
from collections import defaultdict

class AplicacionAudioEscenario:
    def __init__(self, root):
        self.root = root
        self.root.title("Pach Pro  1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.ancho_escenario = 10
        self.profundidad_escenario = 6
        self.pacheras = []
        self.bandas = []  # Lista de bandas
        self.banda_actual = 0  # Índice de la banda actual
        self.posiciones_predefinidas = []
        self.pachera_seleccionada = None
        self.canal_seleccionado = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.zoom_level = 1.0
        self.pan_start = None
        self.ultimo_canal_global = 0  # Contador global de canales
        self.remember_pach = False  # Variable para Remember Pach

        self.configurar_estilos()
        self.crear_menu()
        self.crear_widgets_principal()
        self.crear_formulario_pacheras()
        self.crear_formulario_canales()
        self.crear_mapa()
        self.crear_lista_canales()
        self.crear_botones_acciones()
        self.generar_posiciones_predefinidas()
        
        # Crear banda inicial
        self.crear_nueva_banda("Banda 1")

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabelFrame", background="#dfeaf2", borderwidth=2, relief="groove")
        style.configure("TButton", background="#4a90e2", foreground="white", font=('Arial', 9, 'bold'))
        style.configure("TLabel", background="#dfeaf2", font=('Arial', 9))
        style.configure("Treeview", font=('Arial', 9), rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 9, 'bold'))
        style.map("TButton", background=[('active', '#3a7bc8')])
        style.configure("BotonImportante.TButton", background="#2ecc71", foreground="white")
        style.configure("BotonPeligro.TButton", background="#e74c3c", foreground="white")
        style.configure("BotonRemember.TButton", background="#f39c12", foreground="white")  # Estilo para Remember activo
        style.configure("BandaActual.TButton", background="#2c3e50", foreground="white")  # Estilo para banda actual

    def crear_menu(self):
        barra_menu = tk.Menu(self.root)
        self.root.config(menu=barra_menu)
        archivo_menu = tk.Menu(barra_menu, tearoff=0)
        archivo_menu.add_command(label="Nueva", command=self.nueva_configuracion)
        archivo_menu.add_command(label="Guardar Configuración", command=self.guardar_configuracion)
        archivo_menu.add_command(label="Cargar Configuración", command=self.cargar_configuracion)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        barra_menu.add_cascade(label="Archivo", menu=archivo_menu)
        analisis_menu = tk.Menu(barra_menu, tearoff=0)
        analisis_menu.add_command(label="Mostrar Estadísticas", command=self.mostrar_estadisticas)
        analisis_menu.add_command(label="Ver Conexiones", command=self.mostrar_conexiones)
        barra_menu.add_cascade(label="Análisis", menu=analisis_menu)

    def crear_botones_acciones(self):
        frame_botones = ttk.Frame(self.main_frame)
        frame_botones.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        for i in range(4): frame_botones.grid_columnconfigure(i, weight=1)
        
        ttk.Button(frame_botones, text="Calcular Automático", command=self.calcular_conexiones_mejorado, style="BotonImportante.TButton").grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(frame_botones, text="Cancelar Asignaciones", command=self.cancelar_asignaciones, style="BotonPeligro.TButton").grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame_botones, text="Limpiar Todo", command=self.limpiar_todo, style="BotonPeligro.TButton").grid(row=0, column=2, padx=5, sticky="ew")
        
        # Botón Remember Pach que cambia de estilo cuando está activo
        self.btn_remember = ttk.Button(
            frame_botones, 
            text="Remember Pach: OFF", 
            command=self.toggle_remember_pach,
            style="TButton"
        )
        self.btn_remember.grid(row=0, column=3, padx=5, sticky="ew")

    def toggle_remember_pach(self):
        """Alterna el estado de Remember Pach"""
        self.remember_pach = not self.remember_pach
        if self.remember_pach:
            self.btn_remember.configure(text="Remember Pach: ON", style="BotonRemember.TButton")
        else:
            self.btn_remember.configure(text="Remember Pach: OFF", style="TButton")

    def cancelar_asignaciones(self):
        if messagebox.askyesno("Cancelar Asignaciones", "¿Está seguro de cancelar todas las asignaciones?"):
            if self.banda_actual < len(self.bandas):
                # Reiniciar utilización de pacheras para la banda actual
                for pachera_nombre in self.bandas[self.banda_actual]["pacheras_utilizacion"]:
                    self.bandas[self.banda_actual]["pacheras_utilizacion"][pachera_nombre] = {
                        "canales_asignados": [],
                        "entradas": {}
                    }
                
                # Reiniciar asignaciones de canales para la banda actual
                for canal in self.bandas[self.banda_actual]["canales"]:
                    canal["pachera_asignada"] = None
                    canal["input_pach"] = None
                
                self.actualizar_lista_canales()
                self.dibujar_escenario()
                messagebox.showinfo("Éxito", "Asignaciones canceladas para la banda actual")

    def limpiar_todo(self):
        if messagebox.askyesno("Limpiar Todo", "¿Está seguro de eliminar todos los canales y pacheras?"):
            self.pacheras = []
            self.bandas = [{"nombre": "Banda 1", "canales": [], "pacheras_utilizacion": {}}]
            self.banda_actual = 0
            self.ultimo_canal_global = 0
            self.actualizar_pestanas_bandas()
            self.dibujar_escenario()
            self.actualizar_lista_canales()
            messagebox.showinfo("Éxito", "Todos los datos han sido eliminados")

    def nueva_configuracion(self):
        if messagebox.askyesno("Nueva Configuración", "¿Está seguro de crear una nueva configuración? Se perderán los datos no guardados."):
            self.pacheras = []
            self.bandas = [{"nombre": "Banda 1", "canales": [], "pacheras_utilizacion": {}}]
            self.banda_actual = 0
            self.ultimo_canal_global = 0
            self.pachera_nombre_entry.delete(0, tk.END)
            self.pachera_cantidad_entry.delete(0, tk.END)
            self.canal_num_entry.delete(0, tk.END)
            self.instrumento_entry.delete(0, tk.END)
            self.microfono_entry.delete(0, tk.END)
            self.actualizar_pestanas_bandas()
            self.dibujar_escenario()
            self.actualizar_lista_canales()
            messagebox.showinfo("Nueva Configuración", "Configuración reiniciada correctamente")

    def guardar_configuracion(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title="Guardar configuración como")
        if not file_path: return
        config = {
            "pacheras": self.pacheras, 
            "bandas": self.bandas, 
            "ancho_escenario": self.ancho_escenario, 
            "profundidad_escenario": self.profundidad_escenario, 
            "posiciones_predefinidas": self.posiciones_predefinidas, 
            "ultimo_canal_global": self.ultimo_canal_global,
            "remember_pach": self.remember_pach
        }
        try:
            with open(file_path, 'w') as f: json.dump(config, f, indent=4)
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
        except Exception as e: messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")

    def cargar_configuracion(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title="Seleccionar archivo de configuración")
        if not file_path: return
        try:
            with open(file_path, 'r') as f: config = json.load(f)
            self.pacheras = config.get("pacheras", [])
            self.bandas = config.get("bandas", [{"nombre": "Banda 1", "canales": [], "pacheras_utilizacion": {}}])
            self.banda_actual = 0
            self.ancho_escenario = config.get("ancho_escenario", 10)
            self.profundidad_escenario = config.get("profundidad_escenario", 6)
            self.posiciones_predefinidas = config.get("posiciones_predefinidas", [])
            self.ultimo_canal_global = config.get("ultimo_canal_global", 0)
            self.remember_pach = config.get("remember_pach", False)
            
            # Actualizar botón Remember Pach
            if self.remember_pach:
                self.btn_remember.configure(text="Remember Pach: ON", style="BotonRemember.TButton")
            else:
                self.btn_remember.configure(text="Remember Pach: OFF", style="TButton")
            
            # Asegurar que cada banda tenga la estructura de pacheras_utilizacion
            for banda in self.bandas:
                if "pacheras_utilizacion" not in banda:
                    banda["pacheras_utilizacion"] = {p["nombre"]: {"canales_asignados": [], "entradas": {}} for p in self.pacheras}
                else:
                    # Actualizar con nuevas pacheras si las hay
                    for pachera in self.pacheras:
                        if pachera["nombre"] not in banda["pacheras_utilizacion"]:
                            banda["pacheras_utilizacion"][pachera["nombre"]] = {"canales_asignados": [], "entradas": {}}
            
            if self.posiciones_predefinidas:
                self.ubicacion_combo['values'] = [p['nombre'] for p in self.posiciones_predefinidas]
                self.ubicacion_combo.current(0)
            
            self.actualizar_pestanas_bandas()
            self.dibujar_escenario()
            self.actualizar_lista_canales()
            messagebox.showinfo("Éxito", "Configuración cargada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar: {str(e)}")
            self.generar_posiciones_predefinidas()

    def crear_widgets_principal(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)  # Formulario pacheras
        self.main_frame.grid_rowconfigure(1, weight=0)  # Formulario canales
        self.main_frame.grid_rowconfigure(2, weight=1)  # Mapa y lista
        self.main_frame.grid_rowconfigure(3, weight=0)  # Botones acciones

    def crear_formulario_pacheras(self):
        self.form_pachera_frame = ttk.LabelFrame(self.main_frame, text="Agregar Pachera", padding="10")
        self.form_pachera_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")
        for i in range(8): self.form_pachera_frame.grid_columnconfigure(i, weight=1 if i in [1,3,6] else 0)
        ttk.Label(self.form_pachera_frame, text="Nombre").grid(row=0, column=0, padx=5, sticky="e")
        self.pachera_nombre_entry = ttk.Entry(self.form_pachera_frame, width=15)
        self.pachera_nombre_entry.grid(row=0, column=1, sticky="ew")
        ttk.Label(self.form_pachera_frame, text="Cantidad de Canales").grid(row=0, column=2, padx=5, sticky="e")
        self.pachera_cantidad_entry = ttk.Entry(self.form_pachera_frame, width=5)
        self.pachera_cantidad_entry.grid(row=0, column=3, sticky="w")
        self.boton_agregar_pachera = ttk.Button(self.form_pachera_frame, text="Agregar Pachera", command=self.agregar_pachera_manual, style="TButton")
        self.boton_agregar_pachera.grid(row=0, column=6, columnspan=2, padx=5, sticky="e")

    def agregar_pachera_manual(self):
        nombre = self.pachera_nombre_entry.get().strip()
        try:
            capacidad = int(self.pachera_cantidad_entry.get())
            if not nombre: raise ValueError("El nombre no puede estar vacío")
            if capacidad <= 0: raise ValueError("La capacidad debe ser mayor que 0")
            if any(p["nombre"].lower() == nombre.lower() for p in self.pacheras): raise ValueError("Ya existe una pachera con ese nombre")
        except ValueError as e:
            messagebox.showerror("Error", f"Datos inválidos: {e}")
            return
        
        # Agregar pachera a la lista general
        self.pacheras.append({
            "nombre": nombre, 
            "x": self.ancho_escenario / 2, 
            "y": self.profundidad_escenario / 2, 
            "capacidad": capacidad
        })
        
        # Agregar la pachera a la utilización de cada banda
        for banda in self.bandas:
            banda["pacheras_utilizacion"][nombre] = {"canales_asignados": [], "entradas": {}}
        
        self.pachera_nombre_entry.delete(0, tk.END)
        self.pachera_cantidad_entry.delete(0, tk.END)
        self.dibujar_escenario()

    def crear_formulario_canales(self):
        self.form_frame = ttk.LabelFrame(self.main_frame, text="Agregar Canal", padding="10")
        self.form_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")
        for i in range(8): self.form_frame.grid_columnconfigure(i, weight=1 if i in [1,3,5,7] else 0)
        
        ttk.Label(self.form_frame, text="Canal #").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.canal_num_entry = ttk.Entry(self.form_frame, width=5)
        self.canal_num_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(self.form_frame, text="Auto", command=self.autoasignar_numero_canal, width=4).grid(row=0, column=2, padx=2, sticky="w")
        ttk.Label(self.form_frame, text="Instrumento").grid(row=0, column=3, padx=5, sticky="e")
        self.instrumento_entry = ttk.Entry(self.form_frame, width=15)
        self.instrumento_entry.grid(row=0, column=4, sticky="ew")
        ttk.Label(self.form_frame, text="Micrófono").grid(row=0, column=5, padx=5, sticky="e")
        self.microfono_entry = ttk.Entry(self.form_frame, width=15)
        self.microfono_entry.grid(row=0, column=6, sticky="ew")
        ttk.Label(self.form_frame, text="Ubicación").grid(row=0, column=7, padx=5, sticky="e")
        self.ubicacion_combo = ttk.Combobox(self.form_frame, values=[], state="readonly", width=15)
        self.ubicacion_combo.grid(row=0, column=8, sticky="ew")
        self.agregar_canal_btn = ttk.Button(self.form_frame, text="Agregar Canal", command=self.agregar_canal, style="TButton")
        self.agregar_canal_btn.grid(row=0, column=9, padx=5, sticky="e")

    def autoasignar_numero_canal(self):
        """Autoasigna el siguiente número de canal disponible (global)"""
        self.ultimo_canal_global += 1
        self.canal_num_entry.delete(0, tk.END)
        self.canal_num_entry.insert(0, str(self.ultimo_canal_global))
        self.instrumento_entry.focus()

    def generar_posiciones_predefinidas(self):
        posiciones = []
        secciones = ["Adelante", "Medio", "Atrás"]
        for seccion in secciones:
            for i in range(1, 7):
                pos = {"nombre": f"{seccion} {i}", "x": i, "y": 1 if seccion=="Adelante" else 3 if seccion=="Medio" else 5}
                posiciones.append(pos)
        self.posiciones_predefinidas = posiciones
        self.ubicacion_combo['values'] = [pos["nombre"] for pos in posiciones]
        if posiciones: self.ubicacion_combo.current(0)

    def agregar_canal(self):
        try:
            if not self.canal_num_entry.get(): self.autoasignar_numero_canal()
            numero = int(self.canal_num_entry.get())
            instrumento = self.instrumento_entry.get().strip()
            microfono = self.microfono_entry.get().strip()
            ubicacion_nombre = self.ubicacion_combo.get()
            if numero < 1 or numero > 100: raise ValueError("El número de canal debe estar entre 1 y 100")
            if not all([numero, instrumento, microfono, ubicacion_nombre]): raise ValueError("Todos los campos son requeridos")
            
            # Verificar si el canal ya existe en la banda actual
            if self.banda_actual < len(self.bandas):
                if any(c["numero"] == numero for c in self.bandas[self.banda_actual]["canales"]): 
                    raise ValueError(f"El canal {numero} ya existe en {self.bandas[self.banda_actual]['nombre']}")
            
            ubicacion = next(pos for pos in self.posiciones_predefinidas if pos["nombre"] == ubicacion_nombre)
            
            nuevo_canal = {
                "numero": numero, 
                "instrumento": instrumento, 
                "microfono": microfono, 
                "x": ubicacion["x"], 
                "y": ubicacion["y"], 
                "pachera_asignada": None, 
                "input_pach": None, 
                "posicion_predefinida": ubicacion_nombre
            }
            
            if self.banda_actual < len(self.bandas):
                self.bandas[self.banda_actual]["canales"].append(nuevo_canal)
            
            if numero > self.ultimo_canal_global: self.ultimo_canal_global = numero
            self.canal_num_entry.delete(0, tk.END)
            self.instrumento_entry.delete(0, tk.END)
            self.microfono_entry.delete(0, tk.END)
            self.instrumento_entry.focus()
            self.dibujar_escenario()
            self.actualizar_lista_canales()
        except ValueError as e: messagebox.showerror("Error", f"Datos inválidos: {e}")
        except StopIteration: messagebox.showerror("Error", "Ubicación no válida")

    def crear_mapa(self):
        self.mapa_frame = ttk.LabelFrame(self.main_frame, text="Mapa del Escenario", padding="10")
        self.mapa_frame.grid(row=2, column=0, pady=10, sticky="nsew")
        self.mapa_frame.grid_rowconfigure(0, weight=1)
        self.mapa_frame.grid_columnconfigure(0, weight=1)
        self.mapa_canvas = tk.Canvas(self.mapa_frame, bg="white", cursor="hand2")
        self.mapa_canvas.grid(row=0, column=0, sticky="nsew")
        h_scroll = ttk.Scrollbar(self.mapa_frame, orient="horizontal", command=self.mapa_canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll = ttk.Scrollbar(self.mapa_frame, orient="vertical", command=self.mapa_canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.mapa_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.mapa_canvas.bind("<Configure>", lambda e: self.dibujar_escenario())
        self.mapa_canvas.bind("<Button-1>", self.iniciar_arrastre)
        self.mapa_canvas.bind("<B1-Motion>", self.arrastrar_item)
        self.mapa_canvas.bind("<ButtonRelease-1>", self.soltar_item)
        self.mapa_canvas.bind("<MouseWheel>", self.zoom)
        self.mapa_canvas.bind("<Button-2>", self.iniciar_pan)
        self.mapa_canvas.bind("<B2-Motion>", self.pan)

    def crear_lista_canales(self):
        # Frame principal para lista de canales y pestañas de bandas
        self.lista_main_frame = ttk.Frame(self.main_frame)
        self.lista_main_frame.grid(row=2, column=1, pady=10, padx=5, sticky="nsew")
        self.lista_main_frame.grid_rowconfigure(1, weight=1)
        self.lista_main_frame.grid_columnconfigure(0, weight=1)
        
        # Frame para las pestañas de bandas (dentro del recuadro de lista de canales)
        self.pestanas_frame = ttk.Frame(self.lista_main_frame)
        self.pestanas_frame.grid(row=0, column=0, pady=(0, 5), sticky="ew")
        
        # Botón para agregar nueva banda
        ttk.Button(
            self.pestanas_frame, 
            text="+", 
            width=3,
            command=self.agregar_nueva_banda
        ).pack(side=tk.RIGHT, padx=5)
        
        # Canvas y scrollbar para pestañas
        self.canvas_pestanas = tk.Canvas(self.pestanas_frame, height=30, highlightthickness=0)
        self.scrollbar_pestanas = ttk.Scrollbar(self.pestanas_frame, orient="horizontal", command=self.canvas_pestanas.xview)
        self.frame_pestanas = ttk.Frame(self.canvas_pestanas)
        
        self.canvas_pestanas.create_window((0, 0), window=self.frame_pestanas, anchor="nw")
        self.canvas_pestanas.configure(xscrollcommand=self.scrollbar_pestanas.set)
        
        self.canvas_pestanas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.scrollbar_pestanas.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.frame_pestanas.bind("<Configure>", lambda e: self.canvas_pestanas.configure(scrollregion=self.canvas_pestanas.bbox("all")))
        
        # Frame para la lista de canales
        self.lista_frame = ttk.LabelFrame(self.lista_main_frame, text="Lista de Canales", padding="10")
        self.lista_frame.grid(row=1, column=0, sticky="nsew")
        self.lista_frame.grid_rowconfigure(0, weight=1)
        self.lista_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.lista_frame, columns=("num", "inst", "mic", "ubic", "pachera", "input_pach"), show="headings")
        columnas = [("num", "Canal", 60), ("inst", "Instrumento", 100), ("mic", "Micrófono", 100), ("ubic", "Ubicación", 100), ("pachera", "Pachera", 80), ("input_pach", "Input Pach", 80)]
        for col_id, heading, width in columnas:
            self.tree.heading(col_id, text=heading)
            self.tree.column(col_id, width=width, anchor=tk.CENTER)
        
        v_scroll = ttk.Scrollbar(self.lista_frame, orient="vertical", command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=v_scroll.set)
        
        h_scroll = ttk.Scrollbar(self.lista_frame, orient="horizontal", command=self.tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", self.editar_canal)

    def crear_nueva_banda(self, nombre):
        """Crea una nueva banda con el nombre especificado"""
        nueva_banda = {
            "nombre": nombre,
            "canales": [],
            "pacheras_utilizacion": {p["nombre"]: {"canales_asignados": [], "entradas": {}} for p in self.pacheras}
        }
        self.bandas.append(nueva_banda)
        self.banda_actual = len(self.bandas) - 1
        self.actualizar_pestanas_bandas()
        self.actualizar_lista_canales()
        self.dibujar_escenario()

    def actualizar_pestanas_bandas(self):
        """Actualiza las pestañas de bandas"""
        # Limpiar pestañas existentes
        for widget in self.frame_pestanas.winfo_children():
            widget.destroy()
        
        # Crear pestañas para cada banda
        for i, banda in enumerate(self.bandas):
            # Determinar el estilo según si es la banda actual
            estilo = "BandaActual.TButton" if i == self.banda_actual else "TButton"
            
            btn = ttk.Button(
                self.frame_pestanas,
                text=banda["nombre"],
                style=estilo,
                command=lambda idx=i: self.cambiar_banda_actual(idx)
            )
            btn.pack(side=tk.LEFT, padx=2)
            
            # Botón para eliminar banda (solo si hay más de una banda)
            if len(self.bandas) > 1:
                btn_eliminar = ttk.Button(
                    self.frame_pestanas,
                    text="×",
                    width=2,
                    command=lambda idx=i: self.eliminar_banda(idx)
                )
                btn_eliminar.pack(side=tk.LEFT, padx=(0, 5))

    def cambiar_banda_actual(self, indice):
        """Cambia la banda actual según el índice"""
        self.banda_actual = indice
        self.actualizar_pestanas_bandas()
        self.actualizar_lista_canales()
        self.dibujar_escenario()

    def agregar_nueva_banda(self):
        """Agrega una nueva banda"""
        nombre = simpledialog.askstring("Nueva Banda", "Nombre de la nueva banda:")
        if nombre:
            self.crear_nueva_banda(nombre)

    def eliminar_banda(self, indice):
        """Elimina la banda en el índice especificado"""
        if len(self.bandas) > 1:
            if messagebox.askyesno("Eliminar Banda", f"¿Está seguro de eliminar la banda '{self.bandas[indice]['nombre']}'?"):
                del self.bandas[indice]
                if self.banda_actual >= len(self.bandas):
                    self.banda_actual = len(self.bandas) - 1
                self.actualizar_pestanas_bandas()
                self.actualizar_lista_canales()
                self.dibujar_escenario()
        else:
            messagebox.showwarning("Error", "Debe haber al menos una banda")

    def editar_canal(self, event):
        if self.banda_actual >= len(self.bandas):
            return
            
        item = self.tree.selection()[0]
        canal_num = int(self.tree.item(item, "values")[0])
        canal = next(c for c in self.bandas[self.banda_actual]["canales"] if c["numero"] == canal_num)
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Editar Canal {canal_num}")
        ttk.Label(edit_win, text="Instrumento:").grid(row=0, column=0, padx=5, pady=5)
        inst_entry = ttk.Entry(edit_win)
        inst_entry.insert(0, canal["instrumento"])
        inst_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(edit_win, text="Micrófono:").grid(row=1, column=0, padx=5, pady=5)
        mic_entry = ttk.Entry(edit_win)
        mic_entry.insert(0, canal["microfono"])
        mic_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(edit_win, text="Guardar", command=lambda: self.guardar_edicion_canal(canal_num, inst_entry.get(), mic_entry.get(), edit_win)).grid(row=2, columnspan=2, pady=5)

    def guardar_edicion_canal(self, num, instrumento, microfono, ventana):
        if self.banda_actual < len(self.bandas):
            canal = next(c for c in self.bandas[self.banda_actual]["canales"] if c["numero"] == num)
            canal["instrumento"] = instrumento.strip()
            canal["microfono"] = microfono.strip()
            self.actualizar_lista_canales()
        ventana.destroy()

    def actualizar_lista_canales(self):
        for item in self.tree.get_children(): 
            self.tree.delete(item)
            
        if self.banda_actual < len(self.bandas):
            for canal in sorted(self.bandas[self.banda_actual]["canales"], key=lambda x: x["numero"]):
                ubic_nombre = canal.get("posicion_predefinida", "Personalizada")
                pachera_info = "Sin asignar"
                input_pach_info = canal.get("input_pach", "")
                
                if canal["pachera_asignada"]:
                    pachera_info = f"{canal['pachera_asignada']}"
                    input_pach_info = canal.get("input_pach", "")
                
                self.tree.insert("", "end", values=(
                    canal["numero"], 
                    canal["instrumento"], 
                    canal["microfono"], 
                    ubic_nombre, 
                    pachera_info, 
                    input_pach_info
                ))

    def dibujar_escenario(self):
        self.mapa_canvas.delete("all")
        canvas_width = self.mapa_canvas.winfo_width()
        canvas_height = self.mapa_canvas.winfo_height()
        escala_x = (canvas_width - 50) / self.ancho_escenario * self.zoom_level
        escala_y = (canvas_height - 50) / self.profundidad_escenario * self.zoom_level
        margen_x = 25
        margen_y = 25
        
        # Dibujar escenario
        self.mapa_canvas.create_rectangle(
            margen_x, margen_y,
            margen_x + self.ancho_escenario * escala_x,
            margen_y + self.profundidad_escenario * escala_y,
            outline="black", fill="lightgray"
        )
        
        # Dibujar pacheras
        for pachera in self.pacheras:
            x = margen_x + pachera["x"] * escala_x
            y = margen_y + pachera["y"] * escala_y
            
            # Calcular utilización para la banda actual
            utilizacion = 0
            if (self.banda_actual < len(self.bandas) and 
                pachera["nombre"] in self.bandas[self.banda_actual]["pacheras_utilizacion"]):
                utilizacion = len(self.bandas[self.banda_actual]["pacheras_utilizacion"][pachera["nombre"]]["canales_asignados"])
            
            self.mapa_canvas.create_oval(x-10, y-10, x+10, y+10, fill="blue", tags=f"pachera_{pachera['nombre']}")
            self.mapa_canvas.create_text(x, y-15, text=f"{pachera['nombre']} ({utilizacion}/{pachera['capacidad']})", font=("Arial", 8))
        
        # Dibujar canales de la banda actual
        if self.banda_actual < len(self.bandas):
            for canal in self.bandas[self.banda_actual]["canales"]:
                x = margen_x + canal["x"] * escala_x
                y = margen_y + canal["y"] * escala_y
                color = "green" if canal["pachera_asignada"] else "red"
                
                self.mapa_canvas.create_rectangle(x-8, y-8, x+8, y+8, fill=color, tags=f"canal_{canal['numero']}")
                self.mapa_canvas.create_text(x, y+15, text=f"C{canal['numero']}", font=("Arial", 8))
                
                # Dibujar conexiones
                if canal["pachera_asignada"]:
                    pachera = next(p for p in self.pacheras if p["nombre"] == canal["pachera_asignada"])
                    px = margen_x + pachera["x"] * escala_x
                    py = margen_y + pachera["y"] * escala_y
                    self.mapa_canvas.create_line(x, y, px, py, fill="blue", dash=(2,2), tags=f"conexion_{canal['numero']}")
        
        self.mapa_canvas.configure(scrollregion=(
            0, 0, 
            margen_x + self.ancho_escenario * escala_x + 25, 
            margen_y + self.profundidad_escenario * escala_y + 25
        ))

    def iniciar_arrastre(self, event):
        canvas_width = self.mapa_canvas.winfo_width()
        canvas_height = self.mapa_canvas.winfo_height()
        escala_x = (canvas_width - 50) / self.ancho_escenario * self.zoom_level
        escala_y = (canvas_height - 50) / self.profundidad_escenario * self.zoom_level
        margen_x = 25
        margen_y = 25
        
        # Verificar si se está arrastrando una pachera
        for pachera in self.pacheras:
            x = margen_x + pachera["x"] * escala_x
            y = margen_y + pachera["y"] * escala_y
            if (x-10 <= event.x <= x+10) and (y-10 <= event.y <= y+10):
                self.pachera_seleccionada = pachera
                self.drag_data = {"x": event.x, "y": event.y, "item": "pachera"}
                return
        
        # Verificar si se está arrastrando un canal de la banda actual
        if self.banda_actual < len(self.bandas):
            for canal in self.bandas[self.banda_actual]["canales"]:
                x = margen_x + canal["x"] * escala_x
                y = margen_y + canal["y"] * escala_y
                if (x-8 <= event.x <= x+8) and (y-8 <= event.y <= y+8):
                    self.canal_seleccionado = canal
                    self.drag_data = {"x": event.x, "y": event.y, "item": "canal"}
                    return

    def arrastrar_item(self, event):
        if self.drag_data["item"] == "pachera" and self.pachera_seleccionada:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            canvas_width = self.mapa_canvas.winfo_width()
            canvas_height = self.mapa_canvas.winfo_height()
            escala_x = (canvas_width - 50) / self.ancho_escenario * self.zoom_level
            escala_y = (canvas_height - 50) / self.profundidad_escenario * self.zoom_level
            
            self.pachera_seleccionada["x"] += dx / escala_x
            self.pachera_seleccionada["y"] += dy / escala_y
            
            # Limitar al área del escenario
            self.pachera_seleccionada["x"] = max(0, min(self.ancho_escenario, self.pachera_seleccionada["x"]))
            self.pachera_seleccionada["y"] = max(0, min(self.profundidad_escenario, self.pachera_seleccionada["y"]))
            
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.dibujar_escenario()
            
        elif self.drag_data["item"] == "canal" and self.canal_seleccionado:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            canvas_width = self.mapa_canvas.winfo_width()
            canvas_height = self.mapa_canvas.winfo_height()
            escala_x = (canvas_width - 50) / self.ancho_escenario * self.zoom_level
            escala_y = (canvas_height - 50) / self.profundidad_escenario * self.zoom_level
            
            self.canal_seleccionado["x"] += dx / escala_x
            self.canal_seleccionado["y"] += dy / escala_y
            
            # Limitar al área del escenario
            self.canal_seleccionado["x"] = max(0, min(self.ancho_escenario, self.canal_seleccionado["x"]))
            self.canal_seleccionado["y"] = max(0, min(self.profundidad_escenario, self.canal_seleccionado["y"]))
            
            # Marcar como posición personalizada
            self.canal_seleccionado["posicion_predefinida"] = "Personalizada"
            
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.dibujar_escenario()

    def soltar_item(self, event):
        self.pachera_seleccionada = None
        self.canal_seleccionado = None
        self.drag_data = {"x": 0, "y": 0, "item": None}

    def zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_level *= factor
        self.zoom_level = max(0.5, min(3.0, self.zoom_level))
        self.dibujar_escenario()

    def iniciar_pan(self, event):
        self.pan_start = (event.x, event.y)

    def pan(self, event):
        if self.pan_start:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            self.mapa_canvas.scan_dragto(-dx, -dy, gain=1)
            self.pan_start = (event.x, event.y)

    def calcular_conexiones_mejorado(self):
        if not self.pacheras or not (self.banda_actual < len(self.bandas) and self.bandas[self.banda_actual]["canales"]):
            messagebox.showwarning("Error", "Debe haber al menos una pachera y un canal")
            return
        
        # Resetear asignaciones para la banda actual
        banda = self.bandas[self.banda_actual]
        for pachera_nombre in banda["pacheras_utilizacion"]:
            banda["pacheras_utilizacion"][pachera_nombre] = {"canales_asignados": [], "entradas": {}}
        
        for canal in banda["canales"]:
            canal["pachera_asignada"] = None
            canal["input_pach"] = None

        # Si Remember Pach está activado, intentar mantener las asignaciones anteriores
        if self.remember_pach:
            # Crear un diccionario de asignaciones preferidas por instrumento
            preferencias = {}
            for otra_banda in self.bandas:
                if otra_banda != banda:  # Solo mirar otras bandas
                    for canal_otra in otra_banda["canales"]:
                        if canal_otra["pachera_asignada"] and canal_otra["input_pach"]:
                            preferencias[canal_otra["instrumento"]] = {
                                "pachera": canal_otra["pachera_asignada"],
                                "input": canal_otra["input_pach"]
                            }

            # Aplicar preferencias si es posible
            for canal in banda["canales"]:
                if canal["instrumento"] in preferencias:
                    pref = preferencias[canal["instrumento"]]
                    pachera = next((p for p in self.pacheras if p["nombre"] == pref["pachera"]), None)
                    if (pachera and 
                        pref["input"] not in banda["pacheras_utilizacion"][pachera["nombre"]]["entradas"] and 
                        len(banda["pacheras_utilizacion"][pachera["nombre"]]["canales_asignados"]) < pachera["capacidad"]):
                        
                        canal["pachera_asignada"] = pref["pachera"]
                        canal["input_pach"] = pref["input"]
                        banda["pacheras_utilizacion"][pref["pachera"]]["entradas"][pref["input"]] = canal["numero"]
                        banda["pacheras_utilizacion"][pref["pachera"]]["canales_asignados"].append(canal["numero"])

        # Asignar los canales restantes
        canales_ordenados = sorted([c for c in banda["canales"] if not c["pachera_asignada"]], key=lambda x: x["numero"])
        
        for canal in canales_ordenados:
            mejor_pachera = None
            menor_distancia = float('inf')
            
            for pachera in self.pacheras:
                # Verificar si la pachera tiene capacidad
                if len(banda["pacheras_utilizacion"][pachera["nombre"]]["canales_asignados"]) >= pachera["capacidad"]:
                    continue
                
                # Calcular distancia entre canal y pachera
                distancia = math.sqrt((canal["x"] - pachera["x"])**2 + (canal["y"] - pachera["y"])**2)
                
                if distancia < menor_distancia:
                    mejor_pachera = pachera
                    menor_distancia = distancia
            
            if mejor_pachera:
                # Asignar a la pachera
                canal["pachera_asignada"] = mejor_pachera["nombre"]
                
                # Buscar el primer canal disponible en la pachera
                for num_entrada in range(1, mejor_pachera["capacidad"] + 1):
                    if str(num_entrada) not in banda["pacheras_utilizacion"][mejor_pachera["nombre"]]["entradas"]:
                        banda["pacheras_utilizacion"][mejor_pachera["nombre"]]["entradas"][str(num_entrada)] = canal["numero"]
                        banda["pacheras_utilizacion"][mejor_pachera["nombre"]]["canales_asignados"].append(canal["numero"])
                        canal["input_pach"] = str(num_entrada)
                        break

        self.actualizar_lista_canales()
        self.dibujar_escenario()
        self.mostrar_estadisticas()

    def mostrar_estadisticas(self):
        if self.banda_actual >= len(self.bandas):
            return
            
        banda = self.bandas[self.banda_actual]
        total_canales = len(banda["canales"])
        canales_asignados = sum(1 for c in banda["canales"] if c["pachera_asignada"])
        
        utilizacion_pacheras = []
        for pachera in self.pacheras:
            utilizacion = len(banda["pacheras_utilizacion"][pachera["nombre"]]["canales_asignados"])
            utilizacion_pacheras.append(f"{pachera['nombre']}: {utilizacion}/{pachera['capacidad']}")
        
        messagebox.showinfo(
            f"Estadísticas - {banda['nombre']}", 
            f"Canales totales: {total_canales}\n"
            f"Canales asignados: {canales_asignados}\n"
            f"Canales sin asignar: {total_canales - canales_asignados}\n\n"
            f"Utilización pacheras:\n" + "\n".join(utilizacion_pacheras)
        )

    
    
    def mostrar_conexiones(self):
        if self.banda_actual >= len(self.bandas):
            return
            
        conexiones = defaultdict(list)
        banda = self.bandas[self.banda_actual]
        
        for canal in banda["canales"]:
            if canal["pachera_asignada"]:
                entrada = banda["pacheras_utilizacion"][canal["pachera_asignada"]]["entradas"].get(canal["input_pach"], "?")
                conexiones[canal["pachera_asignada"]].append(f"Canal {canal['numero']} ({canal['instrumento']}) -> Entrada {entrada}")
        
        reporte = f"Detalle de conexiones - {banda['nombre']}:\n"
        for pachera, canales in conexiones.items(): 
            reporte += f"\n{pachera}:\n  " + "\n  ".join(canales)
        
        if len(reporte) <= len(f"Detalle de conexiones - {banda['nombre']}:\n"): 
            reporte = "No hay conexiones asignadas"
        
        conexiones_win = tk.Toplevel(self.root)
        conexiones_win.title(f"Reporte de Conexiones - {banda['nombre']}")
        text = tk.Text(conexiones_win, wrap=tk.WORD, width=60, height=25)
        text.insert(tk.END, reporte)
        text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        ttk.Button(conexiones_win, text="Cerrar", command=conexiones_win.destroy).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionAudioEscenario(root)
    root.mainloop()
    
    