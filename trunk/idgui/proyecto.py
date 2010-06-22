# Clase de Proyecto Interfaz
# -*- coding: utf-8 -*-

import os.path as path
import sys

import pygtk
pygtk.require("2.0")
import gtk

import util.clock 
import util.logger
log = util.logger.getlog('idgui.proyect')

from idg.proyecto import Proyecto, ProyectoError, ProyectoRecuperable, \
ProyectoIrrecuperable
from instrum import Comprobador
from ejecucion import Ejecucion
from analisis import Analisis

class ProyectoUI(object):
    """@brief Manejo de la interfaz de usuario del proyecto."""

    def __init__(self, idg, idgui, nombre, bpel=""):
        """@brief Clase que maneja la interfaz de un proyecto. Lo carga o crea
        al instanciarse.
           @param idg Instancia de la clase de control
           @param idgui Instancia de la clase de control de la gui
           @param nombre Nombre del proyecto a cargar/crear
           @param bpel (Opcional) Ruta al bpel para crear el proyecto.
           """

        ## Instancia de idg
        self.idg = idg
        ## Instancia de idgui
        self.idgui = idgui
        ## Objeto gtkbuilder de idgui
        self.gtk = idgui.builder
        ## Objeto de opciones
        self.opts = self.idg.opt

        # Estado de la barra inferior
        idgui.estado(_("idgui.proyect.init.proyect"))

        # Crear el proyecto
        try:
            error = ""
            ## Referencia a la instancia del Proyecto actual
            self.proy = Proyecto(nombre, idg, bpel)
            self.idg.proy = self.proy
        except (ProyectoRecuperable) as e:
            # Mostrar las recuperables en los errores en la interfaz.
            log.error(str(e))
            idgui.estado(e)
        except:
            log.error(_("idgui.proyect.fatal.exception.at.proyect.creation"))
            raise

        # Cargar el glade del proyecto
        self.gtk.add_from_file(path.join(self.idg.share,"ui/proy.glade"))

        # Obtener los elementos de la gui

        ## Contenedor de la gui 
        self.principal = self.gtk.get_object("principal")
        ## Base del proyecto
        self.proyecto_base = self.gtk.get_object("proy_container")
        ## Notebook en el que está contenido el proyecto
        self.proyecto_notebook = self.gtk.get_object("proy_notebook")

        ## Label indicador de errores y dejarlo vacío
        self.error_label = self.gtk.get_object("proy_error_label")
        self.error(error)

        self.__init_config()
        self.__init_casos()
        self.__init_ejec()
        self.__init_trz()
        self.__init_anl()
        self.__init_inv()

        # Conectar todas las señales
        self.gtk.connect_signals(self)

        # Situar en el contenedor y mostrar
        self.proyecto_base.reparent(self.principal)
        self.proyecto_base.show()

        self.mensaje("")
        idgui.estado(_("idgui.proyect.created.succesfully"))

    def __del__(self):
        """@brief Destructor del Proyecto"""
        self.dep_list.clear()
        # Cancelamos la ejecución si hay alguna activa.
        self.proy.cancelar_ejecucion()

    def error(self,msg):
        self.error_label.set_markup('<span color="red">'+msg+'</span>')

    def mensaje(self,msg):
        self.error_label.set_markup('<span color="black">'+msg+'</span>')

    def cerrar(self):
        """@Brief realiza comprobaciones y cierra el proyectoUI"""
        # TODO preguntar si cerrar el proyecto.
        # Cerramos el proyecto que tenemos abierto
        self.proy.cerrar()

    ## @name Callbacks
    ## @{

    def proy_notebook_next(self,widget=None):
        """@brief Callback de pulsar el botón siguiente en el proyecto."""
        self.proyecto_notebook.next_page()


    def on_proy_notebook_switch_page(self, notebook, page, pagenum):
        """@brief Actualiza la pestaña de trazas"""
        # Actualizar trazas al entrar en la pestaña de trazas
        if pagenum == 2 :
            self.load_exe_tree()
        elif pagenum == 3 :
            self.actualizar_trazas()
        elif pagenum == 4 :
            self.anl_actualizar_info()
            self.anl_seleccionar_trazas()
    ## @}

    ## @name Config
    ## @{

    def __init_config(self):
        """@brief Inicializar la pantalla de configuración."""
        # Cargar el glade de esta parte
        self.gtk.add_from_file(path.join(self.opts.get('share'),
                                         "ui/proy_config.glade"))
        # Obtener el contenedor de esa parte y añadirlo al notebook
        self.config_cont = self.gtk.get_object('proy_config_container')
        self.config_cont.reparent(self.gtk.get_object('proy_nb_config_dummy_box'))


        ## Nombre del proyecto
        self.nombre_label = self.gtk.get_object("proy_config_name_label")
        self.nombre_label.set_text(self.proy.nombre)

        # Configuración del servidor


        # Dependencias
        ## Label con el número total de dependencias
        self.dep_totales_label = self.gtk.get_object("proy_config_dep_total_label")
        ## Label con el número de dependencias rotas
        self.dep_rotas_label = self.gtk.get_object("proy_config_dep_broken_label")

        ## Lista de depencencias Modelo Datos 
        self.dep_list = self.gtk.get_object("proy_config_dep_list")
        ## Lista de dependencias TreeView
        self.dep_view = self.gtk.get_object("proy_config_dep_view")

        # Actualizar la información de la configuración
        self.actualizar_pantalla_config()

    def actualizar_pantalla_config(self):
        """@brief Actualiza las variables y los datos de la pantalla config."""
        # Número de dependencias y dependencias rotas
        ldep = len(self.proy.deps)
        ldep_miss = len(self.proy.dep_miss)

        log.debug("Dependencias " + str(ldep))
        log.debug("Dependencias no encontradas " + str(ldep_miss))

        # Mostrar error si hay dependencias rotas
        if len(self.proy.dep_miss) > 0 :
            self.error("%d dependencias rotas" % len(self.proy.dep_miss))

        self.dep_totales_label.set_text(str(ldep+ldep_miss))
        self.dep_rotas_label.set_text(str(ldep_miss))

        # Iconos
        roto = self.dep_view.render_icon(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        buena = self.dep_view.render_icon(gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU)

        # Limpiar la lista de dependencias y actualizarlas 
        self.dep_list.clear()
        for d in self.proy.deps + self.proy.dep_miss :
            if d in self.proy.dep_miss:
                l = [ roto , path.basename(d), d ]
            else:
                l = [ buena, path.basename(d), _("idgui.proyect.into.proyect") ]
            self.dep_list.append(l)

    ## @}

    ## @name Callbacks Config
    ## @{

    def on_proy_config_dep_inst_button(self,widget):
        """@brief Callback de pulsar el botón de instrumentar.
        @param widget Botón"""

        self.idgui.estado(_("idgui.proyect.running.instrumentation"))
        try:
            self.proy.instrumentar()
            c = Comprobador(self.proy,self,2)
            c.start()
        except ProyectoError:
            self.error(_("idgui.proyect.instrumentation.error"))
            self.idgui.estado(_("idgui.proyect.instrumentation.error"))
            #self.mensaje(_("Instrumentación correcta."))

    def on_proy_config_dep_search_button(self,widget):
        """@brief Callback de pulsar el botón de buscar dependencias
        @param widget Botón"""
        try:
            log.info("Bpel original: " + self.proy.bpel_o)
            self.proy.buscar_dependencias(self.proy.bpel_o)
        except ProyectoError:
            self.error(_("idgui.proyect.error.at.dependence.search"))

        self.actualizar_pantalla_config()
        self.idgui.estado(_("idgui.proyect.founded.dependences") + \
                          str(len(self.proy.deps)))

    def on_proy_config_save_button(self,widget):
        """@brief Callback de pulsar el botón de guardar en la pantalla de
        configuración de un proyecto."""
        # Guardar el proyecto
        self.proy.guardar()
        self.idgui.estado(_("idgui.proyect.saved"))

    ## @}

    ## @name Casos
    ## @{

    def __init_casos(self):
        """@brief Inicializar la pantalla de casos de prueba."""
        # Cargar el glade correspondiente 
        self.gtk.add_from_file(path.join(self.opts.get('share'),
                                         "ui/proy_cases.glade"))
        # Obtener el contenedor de esa parte y añadirlo al notebook
        self.cases_cont = self.gtk.get_object('proy_cases_container')
        self.cases_cont.reparent(self.gtk.get_object('proy_nb_cases_dummy_box'))


        # Configurar el filtro de ficheros btps
        self.gtk.get_object("proy_cases_bpts_filter").add_pattern("*.bpts")
        ## Selector de ficheros bpts
        self.bpts_fichero = self.gtk.get_object("proy_cases_btps_file")
        ## TreeStore de los casos de prueba
        self.bpts_tree = self.gtk.get_object("proy_cases_tree")
        ## TreeView de los casos de prueba
        self.bpts_view = self.gtk.get_object("proy_cases_view")

        # Actualizar los casos en la vista
        self.cargar_bpts_tree()
        # Marcar los casos que estén en el test.bpts 
        self.marcar_bpts_tree()

        ## Última ruta de bpts añadida
        self.last_path = ""

        # Información sobre el caso
        self.bpts_nombre_label =  \
                self.gtk.get_object("proy_cases_info_name_label")
        self.bpts_n_label = self.gtk.get_object("proy_cases_info_n_label")
        self.bpts_nsel_label = self.gtk.get_object("proy_cases_info_nsel_label")

    def marcar_bpts_tree(self):
        """@brief Marca o desmarca la selección con respecto a los casos metidos en test.bpts"""
        casos = self.proy.list_bpts(self.proy.test_path)

        def aux_foreach(m, path, iter, casos) :
            """@brief Función auxiliar para recorrer el modelo marcándolo"""
            # Profundidad de la fila en el árbol
            # 0: ficheros
            # 1: casos
            lv = m.iter_depth(iter)

            if lv == 0 :
                fnom = m.get_value(iter, 0) # Nombre del fichero
                m.set_value(iter, 2, False) # Marcarlo como no seleccionado

            else : # lv == 1
                parent = m.iter_parent(iter)
                fnom = m.get_value(parent, 0)   # Nombre del fichero
                cnom = m.get_value(iter, 0)     # Nombre del caso
                name = "%s:%s" % (fnom, cnom)   # Nombre en el test.bpts

                # Marcarlo a el y a su padre si está en los casos 
                if name in casos :
                    m.set_value(iter, 2, True) 
                    m.set_value(parent, 2, True)
                else:
                    m.set_value(iter, 2, False) 

        # Desconectar la vista
        self.bpts_view.set_model(None)

        # Marcar los que están en casos y desmarcar los que no
        self.bpts_tree.foreach(aux_foreach, casos)

        # Conectar la vista de nuevo
        self.bpts_view.set_model(self.bpts_tree)

    def cargar_bpts_tree(self):
        """@brief Carga el contenido del diccionario de casos  en el tree store
        de casos"""
        # Disconnect the view from the model and clear the model.
        self.bpts_view.set_model(None)
        self.bpts_tree.clear()

        # Get Bptsfiles and sort it by file name
        bptsfiles = self.proy.bptsfiles.values()
        bptsfiles.sort(lambda a, b : cmp(a.name(), b.name()))

        # Add files and cases to the treestore
        for bpts in bptsfiles:
            # Add parent row with the name of the file
            parent = self.bpts_tree.append(None,\
                                         [bpts.name(), gtk.STOCK_OPEN, True])
            # Add cases
            for case in bpts.get_cases():
                self.bpts_tree.append(parent, [case.name('short'),\
                                               gtk.STOCK_FILE, True])

        # Connect the view with the model again
        self.bpts_view.set_model(self.bpts_tree)

    def info_bpts_fichero(self, name, count):
        """@brief Establece la información sobre un fichero de casos de prueba
        seleccionado.

        @param name Nombre del fichero bpts
        @param count número de hijos marcados.
        """
        bpts = self.proy.get_bpts(name)

        if bpts is None:
            self.error(_("idgui.proyect.file.dont.exist.into.proyect"))
        else:
            self.bpts_nombre_label.set_text(bpts.name())
            self.bpts_n_label.set_text(str(len(bpts.get_cases())))
            self.bpts_nsel_label.set_text(str(count))

    def add_casos(self):
        """@brief Toma del treeview los ficheros seleccionados para ejecución y
        los introduce en el proyecto para su procesado. 
        """ 
        # Los metemos todos en un diccionario tipo casos[fichero] = [caso1,
        # caso2, ..] y se lo pasamos al proyecto.

        def aux_foreach(m, path, iter, casos):
            """@brief Añadir los ficheros seleccionados del treestore a casos 
            Se llama para cada fila del treestore.
            """
            if m.get_value(iter, 2) : 
                # Profundidad de la fila en el árbol
                # 0: ficheros
                # 1: casos
                lv = m.iter_depth(iter)

                if lv == 0 :
                    fnom = m.get_value(iter, 0)    # Nombre del fichero
                    log.debug(_("idgui.proyect.marking.file.as.selected") + fnom)

                    # Si no estaba en casos, lo añadimos
                    if fnom not in casos :
                        casos[fnom] = []

                else: # lv == 1
                    parent = m.iter_parent(iter)    # Fichero padre del caso
                    fnom = m.get_value(parent, 0)   # Nombre del fichero
                    cnom = m.get_value(iter, 0)     # Nombre del caso

                    log.debug(_("\t add case: ") + cnom)
                    casos[fnom].append(cnom)

        # Recorremos el modelo árbol mirando que casos y ficheros están seleccionados

        # Desconectamos el modelo
        self.bpts_view.set_model(None)

        # Metermos los casos en un diccionario casos[fnom] = cnom
        casos = {}

        # Ejecutamos la función 
        self.bpts_tree.foreach(aux_foreach, casos)

        # Conectar el modelo de nuevo
        self.bpts_view.set_model(self.bpts_tree) 

        # Los añadimos al test.bpts general para su ejecución
        self.proy.add_casos(casos)
        
    ## @}

    ## @name Callbacks Casos
    ## @{

    def on_proy_cases_bpts_file(self, widget):
        """@brief Callback for select a bpts file."""
        self.idgui.estado(_("idgui.proyect.adding.testcase.file"))

        if self.last_path :
            self.bpts_fichero.set_current_folder(self.last_path)

        bpts = self.bpts_fichero.get_filename()
        self.last_path = path.dirname(bpts)

        log.debug("Last Path: " + self.last_path)
        try:
            # Vaciamos primero el test.bpts general para evitar casos repetidos
            self.proy.empty_test()
            self.proy.add_bpts(bpts)
        except(ProyectoRecuperable):
            self.idgui.estado(_("idgui.proyect.error.adding.testcase.file"))
            log.error(str(sys.exc_type) + str(sys.exc_value))
        else:
            self.idgui.estado(_("idgui.proyect.added.testcase.file") + path.basename(bpts) )
            self.bpts_fichero.set_filename("")
            self.cargar_bpts_tree()

    def on_bpts_view_check_toggle(self,render,path):
        """@brief Callback de marcar un caso para ejecución en el tree de la
        parte de casos.
        """
        # Obtenemos el modelo y el iterador del tree
        model = self.bpts_tree
        it = model.get_iter_from_string(path)
        count = 0

        # El comportamiento es:
        # Si se marca/desmarca un fichero, marcar/desmarcar todos sus casos
        # Si se marca un caso de un fichero sin ninguno, marcar el fichero
        # Si se desmarca un caso de un fichero y se queda vacio, desmarcar el
        # fichero
        if not it is None:
            # Cambiamos el valor que tiene ahora mismo
            val = not (model.get_value(it, 2))
            model.set_value(it, 2, val)
            parent = model.iter_parent(it) # Padre

            # Si es un fichero, cambiar también sus hijos
            # Sabemos que es un fichero si su padre es None
            # Mostrar su información en la gui, del fichero
            if parent is None :
                child = model.iter_children(it)
                # Recorrer los casos y marcarlos igualmente, 
                # contarlos si están marcados.
                while not child is None:
                    model.set_value(child, 2, val)
                    child = model.iter_next(child)
                    count += 1 if val else 0

            # Si lo que estamos marcando/desmarcando es un caso
            else :
                # Si lo marcamos y el padre estaba desmarcado, marcarlo
                if val == True :
                    model.set_value(parent, 2, val)

                # Desmarcar el padre si se queda vacio. Contar los casos.
                vacio = True
                # Recorremos los hijos de parent mirando si hay alguno marcado
                child = model.iter_children(parent)
                while child is not None:
                    if model.get_value(child, 2):
                        vacio = False
                        count += 1
                    child = model.iter_next(child) # Siguiente

                    # Si el fichero se ha quedado vacio, lo desmarcamos
                if vacio :
                    model.set_value(parent, 2, False)

            # Actualizar la información del fichero en la interfaz
            fileiter = parent if parent is not None else it
            self.info_bpts_fichero(model.get_value(fileiter, 0), count)

    def on_proy_cases_exec_anl_button(self, widget):
        # Pasamos a la página de la ejecución
        self.proyecto_notebook.next_page()
        # Y comenzamos la ejecución
        self.ejecutar()

    def on_proy_cases_exec_button(self, widget):
        # Pasamos a la página de la ejecución
        self.proyecto_notebook.next_page()
        # Y comenzamos la ejecución
        self.ejecutar()

    ##@}

    ## @name Ejecución
    ## @{

    def __init_ejec(self):
        """@brief Inicializa la parte de ejecución. """
        # Cargar el glade correspondiente
        self.gtk.add_from_file(path.join(self.opts.get('share'),
                                         "ui/proy_exec.glade"))
        # Obtener el contenedor de esa parte y añadirlo al notebook
        self.exec_cont = self.gtk.get_object('proy_exec_container')
        self.exec_cont.reparent(self.gtk.get_object('proy_nb_exec_dummy_box'))
        self.exec_cont.show_all()

        # Obtenemos los objetos que empleamos
        # Texto del log
        self.ejec_log_buffer = self.gtk.get_object('proy_exec_log_buffer')
        self.ejec_log_text = self.gtk.get_object('proy_exec_log_text')
        # Label de estado
        self.ejec_estado_label = self.gtk.get_object('proy_exec_svr-state_label') 
        ## TreeStore de casos
        self.ejec_tree = self.gtk.get_object('proy_exec_tree')
        ## TreeView de casos
        self.ejec_view = self.gtk.get_object('proy_exec_view')
        ## Botón de empezar y detener
        self.ejec_control_boton = \
        self.gtk.get_object('proy_exec_control_exec_button')
        ## Boton de analizar desde la pantalla de ejecución
        self.ejec_control_analisis = \
        self.gtk.get_object('proy_exec_control_anl_button')
        # Label del tiempo de ejecución
        self.ejec_control_tiempo_label = \
        self.gtk.get_object('proy_exec_control_time_label')
        # Barra de progreso
        self.ejec_barra = self.gtk.get_object('proy_exec_control_bar')

        # Comprobamos el servidor abpel y ponemos el mensaje correspondiente
        self.comprobar_servidor_abpel()

        ## Diccionario con los casos listados y sus rutas
        ## de la forma exe_path_cases[fichero:caso] = path
        self.exe_path_cases = {}

        ## Lista con los iconos para los diferentes niveles
        self.ejec_iconos = [ gtk.STOCK_OPEN, 
                            gtk.STOCK_REFRESH,
                            gtk.STOCK_EXECUTE,
                            gtk.STOCK_YES,
                            gtk.STOCK_CANCEL ]

    def load_exe_tree(self):
        """@brief Lee los casos que van a entrar en ejecución y actualiza el
        tree de la parte de ejecución con ellos.
        """

        # Group test.bpts cases by original file
        # filecases[file] = [case1, case2 ..]
        filecases = {}
        for case in self.proy.test.get_cases():
            file = case.name('file')
            log.debug('reading: ' + case.name())
            if file not in filecases:
                filecases[file] = []
            filecases[file].append(case)

        # Dissociate view/model and clean model
        self.ejec_view.set_model( None )
        m = self.ejec_tree
        m.clear()

        # Insert cases by file into the treestore model
        # Save case treeview paths into self.exe_path_cases[fnom:cnom] = path
        self.exe_path_cases = {}
        for file in filecases.keys():
            # Insert file as parent row
            parent = m.append( None, [file, gtk.STOCK_OPEN, 0] )

            # Add children and save the case treeview path
            for case in filecases[file]:
                child = self.ejec_tree.append(parent, [case.name('short'), gtk.STOCK_FILE, 0] )
                self.exe_path_cases[case.name('long')] = m.get_path(child)

        # Connect again view/model
        self.ejec_view.set_model(self.ejec_tree)

        # Expand all before execution
        self.ejec_view.expand_all()

    def lista_casos_dict(self, list):
        """@brief Transforma una lista de casos de la forma fichero:caso en un
        diccionario dict[file] = [case1, case2 ..]
        """
        casos = {}
        for caso in list:
            fnom, cnom = caso.split(':') # file:case
            if fnom not in casos :
                casos[fnom] = []
            casos[fnom].append(cnom)

        return casos

    def activar_ejec_caso(self, caso, nivel):
        """@brief Actualiza el estado de un caso en el treeview.
        Pone los iconos correspondientes y el estado de un caso en el TreStore.
        Expande y colapsa los ficheros según vayan ejecutándose.
        @param caso El nombre del caso de la forma fichero:caso.
        @param nivel El nivel al que se va a poner el caso.
            0 Normal
            1 En espera
            2 En ejecución
            3 OK
            4 Error
        """
        # Comprobar que tenemos la ruta del caso
        if caso not in self.exe_path_cases :
            log.warning(_("idgui.proyect.testcase.not.found.in.treeview") + caso)
            return

        # Comprobar que el nivel es el adecuado
        if nivel < 0 or  nivel >= len(self.ejec_iconos) :
            log.warning(_("idgui.proyect.no.icon.for.this.level") + str(nivel))
            return 

        # Acortar el nombre del treeStore (modelo)
        m = self.ejec_tree
        # Acortar el nombre del TreeView (vista)
        v = self.ejec_view
        # Icono correspondiente al nivel actual
        icono = self.ejec_iconos[nivel]
        # Iterador del caso en el TreeView a partir de la ruta
        path = self.exe_path_cases[caso]
        iter = m.get_iter(path)

        # Actualizar el valor del nivel
        m.set_value(iter, 2, nivel)
        # Icono para el nivel 
        m.set_value(iter, 1, icono)

        # Obtenemos el padre del caso 
        padre = m.iter_parent(iter)
        # Expandimos al padre en el view
        v.expand_to_path(path)

        # Actualizar los iconos y el nivel de los ficheros y casos

        # Si nivel es 0, actualizar al padre con gtk.STOCK_OPEN
        # Si nivel es 2 o 3 actualizar al padre con nivel y su icono
        if 0 <= nivel and nivel <= 2 :
            m.set_value(padre, 1, icono if nivel != 0 else gtk.STOCK_OPEN)
            m.set_value(padre, 2, nivel)

        # Si nivel es 3 o 4 y todos los casos tienen nivel 3 o 4
        #  actualizar a padre con 3 si todos son 3, o con 4 si hay algún 4
        elif 3 <= nivel and nivel <= 4 :
            # Flags para la búsqueda
            have4 = False
            have_other = False
            all3 = True
            # Recorremos los hijos
            child = m.iter_children(padre)
            while not child is None :
                child_nv = m.get_value(child, 2)
                # ¿Hay alguno distinto de 3 o 4? Entonces fuera
                have_other = child_nv != 3 and child_nv != 4
                if have_other :
                    break
                else :
                    # Realizar las comprobaciones
                    have4 = child_nv == 4 or have4  # ¿Hay algún 4?
                    all3 = child_nv == 3 and all3   # ¿Todos son 3?
                    child = m.iter_next(child) # Siguiente

            # Ahora ponemos el estado del padre mirando los flags
            # Si todos son 3-4
            if not have_other :
                # Si todos son 3, ponemos el padre a 3
                if all3 :
                    m.set_value(padre, 1, icono)
                    m.set_value(padre, 2, 3)
                # Si alguno es 4 ponemos el padre a 4
                elif have4 :
                    m.set_value(padre, 1, self.ejec_iconos[4])
                    m.set_value(padre, 2, 4)

                # Colapsamos el fichero (todos), pues se ha terminado la ejecución
                #  de todos sus casos
                v.collapse_all()

    def actualizar_ejec_iconos(self, nivel, path="", recursivo=True):
        """@brief Actualiza el estado de los iconos del treeview de la parte de
        ejecución.
        @param nivel Nivel al que se pone el caso: 
             0 Normal
             1 En espera
             2 En ejecución
             3 OK
             4 Error
        @param path (Opcional) Ruta a cambiar. (Por defecto todo el view)
        @param recursivo (Opcional) Si es un fichero, sus casos también.
        """
        # Acortar el nombre del modelo treeStore
        m  = self.ejec_tree 
        # Iterador al elemento que vamos a cambiar
        iter = m.get_iter(path) if path else m.get_iter_root()
        # Icono a colocar
        icono = self.ejec_iconos[nivel] 

        # Comprobar el valor del nivel
        if 4 < nivel or 0 > nivel :
            log.warning(_("idgui.proyect.level.out.of.range"))
            return

        # Cambiar los iconos y los estados
        hijo = False  # Primer nivel, no es un hijo
        while not iter is None:
            m.set_value(iter, 1, icono)
            m.set_value(iter, 2, nivel)

            # Si recursivo, seguir con sus hijos
            if recursivo :
                iter = m.iter_next(iter) if hijo else m.iter_children(iter) 
                hijo = True

    def ejec_conexion_error(self):
        """@brief Indica un error de conexión al intentar la ejecución."""
        self.idgui.estado(_("idgui.proyect.cant.run.tests.if.server.is.offline"))
        self.ejec_control_boton.set_label(_("idgui.proyect.run"))
        self.ejec_control_analisis.set_sensitive(True)

    def ejec_terminar(self):
        """@brief Termina la ejecución y establece los mensajes
        correspondientes.
        """
        # Si la ejecución está en curso, se cancelará
        # Devuelve true si ha matado abruptamente el subproceso
        kill = self.proy.cancelar_ejecucion()

        log.debug("Terminando ejecución: " + str(kill) )

        # Poner el estado en ejecución terminada
        if kill :
            self.idgui.estado(_("idgui.proyect.test.canceled"))
        else:
            self.idgui.estado(_("idgui.proyect.test.finished"))

        # Pone el botón de Detener en Ejecutar
        self.ejec_control_boton.set_label(_("idgui.proyect.run"))
        self.ejec_control_analisis.set_sensitive(True)

    def ejecutar(self):
        # Añadimos los casos seleccionados
        self.add_casos()
        # Actualizamos el tree de la parte de ejecución
        self.load_exe_tree()

        # Comprobar que el servidor Abpel esté en condiciones
        if not self.comprobar_servidor_abpel() :
            self.ejec_conexion_error()
            return

        # Cambiar el botón de ejecutar por el de cancelar
        self.ejec_control_boton.set_label(_("idgui.proyect.stop"))
        self.ejec_control_analisis.set_sensitive(False)
        # Colapsar todos los casos
        self.ejec_view.collapse_all()
        # Ponerles a todos los casos y ficheros el icono de esperando
        self.actualizar_ejec_iconos(1)
        # Poner el estado del servidor
        # Ejecutar los tests
        try:
            self.proy.ejecutar()
        except ProyectoRecuperable, e:
            self.error(str(e))
            self.estado(str(e))
            return

        # Thread de comprobación, lo hará cada segundo.
        e = Ejecucion(self.proy,self,1)
        e.start()

    ## @}

    ## @name Ejecución Callbacks
    ## @{

    def comprobar_servidor_abpel(self, widget=None):
        """@brief Comprueba el servidor abpel y actualiza la gui con el
        resultado.
        @returns True si está activo, False si no lo está.
        # Label de estado del servidor
        """
        status = ""
        if self.proy.comprobar_abpel() :
            status = "Online"
        else:
            status = "Offline"

        # Ponemos el mensaje en el label con el status
        self.ejec_estado_label.set_text(status)
        self.idgui.estado( _("idgui.proyect.connection.with.abpel.server") + \
                          status)

        return status == "Online"

    def on_proy_exec_control_button(self, widget):
        """@brief Callback de pulsar el botón de ejecución en la pantalla de
        ejecución.
        """
        if widget.get_label() == _("idgui.proyect.stop") :
            self.ejec_terminar()
        else:
            self.ejecutar()

    def on_proy_exec_control_anl_button(self, widget):
        """@brief Callback de pulsar el botón de análisis en la pantalla de
        ejecución."""
        pass
        #self.actualizar_trazas()
        #self.analizar()

    ## @}

    ## @name Trazas
    ## @{

    def __init_trz(self):
        """@brief Inicializa las variables propias de la parte de análisis."""
        # Cargar el glade de trazas
        self.gtk.add_from_file(path.join(self.opts.get('share'),
                                         "ui/proy_traces.glade"))
        # Obtener el contenedor de esa parte y añadirlo al notebook
        self.trz_cont = self.gtk.get_object('proy_trz_container')
        self.trz_cont.reparent(self.gtk.get_object('proy_nb_trz_dummy_box'))

        ## Vista en árbol de las trazas disponibles
        self.trz_view = self.gtk.get_object('proy_trz_view')
        ## Almacenamiento en árbol de las trazas disponibles
        self.trz_tree = self.gtk.get_object('proy_trz_tree')

        ## Combo selector de los tipos de aplanado
        self.anl_aplanado_combo = \
                self.gtk.get_object('proy_trz_opt_flat_combo')
        # Activar por defecto --index-flattening
        self.anl_aplanado_combo.set_active(0)

        ## Check de empleo de simplify
        self.anl_simplify_check = \
                self.gtk.get_object('proy_trz_opt_simplify_check')

        ## Botón de ejecución
        self.anl_ejecutar_boton = \
                self.gtk.get_object('proy_trz_anl_boton')

        self.actualizar_trazas()

    def anl_seleccionar_trazas(self):
        """@brief Toma la selección de trazas que hay en el treeview de trazas
        y las devuelve en un diccionario. Solo un fichero de traza por caso.
        Los casos que tienen varias vueltas en ejecución (Rounds), cada round
        pasan como un caso distinto.
        @retval Devuelve una estructura tipo trz[file][case] = tfile
        """

        def aux_foreach(m, path, iter, trz):
            """@brief Función auxiliar al recorrer el modelo. Se llama en cada
            fila del treeview."""

            # Solo lo evaluamos si está seleccionado
            if m.get_value(iter, 5) :
                # Profundidad de la fila en el árbol
                # 0: ficheros
                # 1: casos
                # 2: trace file
                if m.iter_depth(iter) == 2 :
                    # Get parents (file and cases)
                    iter_case = m.iter_parent(iter)
                    iter_file = m.iter_parent(iter_case)

                    # Get names (trace file, case and file)
                    nom = m.get_value(iter, 0)
                    cnom = m.get_value(iter_case, 0)
                    fnom = m.get_value(iter_file, 0)

                    # Check the dict
                    if fnom not in trz :
                        trz[fnom] = {}

                    # Is an error to have two trace files for the same case
                    if cnom in trz[fnom] :
                        # If we return True, the foreach ends, so we return
                        # False, to end the function and continue the
                        # iteration.
                        return False 

                    # Add to the dict
                    trz[fnom][cnom] = nom

        # Diccionario en el que almacenaremos los ficheros de traza
        trz = {}

        # Desconectar el modelo
        self.trz_view.set_model(None)

        # Actualizar el tree 
        self.trz_tree.foreach(aux_foreach, trz)

        # Conectarlo de nuevo
        self.trz_view.set_model(self.trz_tree)

        return trz

    def actualizar_trazas(self):
        """@brief Actualiza en el tree de trazas , las trazas disponibles."""
        # Acortar nombres de vista y modelo
        m = self.trz_tree
        v = self.trz_view

        # Desconectar la vista del modelo
        v.set_model(None)

        # Limpiar el árbol
        m.clear()

        # Obtener todas las trazas en un diccionario
        #log.debug(self.proy.trazas_disponibles())
        trz = self.proy.trazas_disponibles()
        #log.debug(trz)

        # Añadir al tree el diccionario trz[fichero][caso] = [ficheros...]
        # El tree tiene filas del tipo: nombre, fichero, caso, timestamp, icono
        # La fila del modelo tiene los siguientes campos:
        # [name, file, case, timestamp, icon, selected, is_radio, pretty_name]
        for f, casos in trz.items() :
            f_iter = m.append(None, \
                              [f, f, "", "", gtk.STOCK_OPEN, True, False, f])
            for c, fichs in casos.items() :
                c_iter = m.append(f_iter, \
                                  [c, f, c, "", gtk.STOCK_OPEN, True, False, c])

                first = True
                for fich in fichs :
                    # casesfile.bpts:casename:timestamp.log
                    try: time = fich.rsplit(':',1)[1].rsplit('.',1)[0]
                    except: time = "0.0"

                    # Conseguir un nombre bonito con solo la hora
                    ftime = util.clock.min_format(float(time))

                    # Añadirlo 
                    fi_iter = m.append(c_iter, 
                                       [fich, f, c, time, gtk.STOCK_OPEN,
                                        False, True, ftime])

                    # Seleccionar al padre y ponerle el nombre con la fecha del
                    # primer hijo.
                    if first :
                        m.set_value(fi_iter, 5, True) 
                        m.set_value(c_iter, 7, "%s (%s)" % (c, ftime))
                        m.set_value(c_iter, 3, time)
                        first = False

        # Conectar la vista y el modelo de nuevo.
        v.set_model(m)

    def trz_view_toggle_child_lv0(self, it, val):
        """@brief Marcar/desmarcar en el treeview de análisis los ficheros
        completos y a todos sus hijos.
        @param iter Iterador al fichero.
        @param val El valor del check DESPUÉS de pulsarlo.
        """
        # Acortamos nombres de árbol y vista
        m = self.trz_tree
        v = self.trz_view

        # Nos marcamos/desmarcamos
        m.set_value(it, 5, val)

        # Si lo marcamos, marcamos todos los casos y sus primeros hijos
        # Si lo desmarcamos, desmarcamos todos los casos y todos sus hijos
        c = m.iter_children(it) # El primer hijo
        if val :
            while c is not None :
                self.trz_view_toggle_child_lv1(c, True)
                c = m.iter_next(c)
        else :
            while c is not None :
                self.trz_view_toggle_child_lv1(c, False, it)
                c = m.iter_next(c)

    def trz_view_toggle_child_lv1(self, it, val, p = None) :
        """@brief Marcar/desmarcar en el treeview de análisis los casos
        completos y a todos sus hijos.
        @param iter Iterador al caso padre.
        @param val El valor del check DESPUÉS de pulsarlo.
        @param p Iterador al padre (Opcional).
        """
        # Acortamos nombres de árbol y vista
        m = self.trz_tree
        v = self.trz_view

        # Si lo marcamos, marcamos también al primer hijo.
        # Si lo desmarcamos, desmarcamos todos los hijos.

        c = m.iter_children(it) # El primer hijo

        if not val :
            # Desmarcar todos los hijos
            while c is not None :
                m.set_value(c, 5, False)
                c = m.iter_next(c)

            # Marcarnos a nosotros mismos
            m.set_value(it, 5, val)

        # Si no tiene ningún hermano marcado, marcar/desmarcar al padre también.
        # Si lo llamamos desde el padre no lo hacemos porque el padre ya tendrá
        # su valor correspondiente.
        if p is None :
            p = m.iter_parent(it) 
            b = m.iter_children(p) # Primer hermano
            todos = True           # Flag de todos desmarcados.
            dummy = m.get_value(b, 5) # Dummy para acumular el valor

            # Recorremos todos los hermanos mirando si están todos en la misma
            # posición. Todos marcados o todos desmarcados.
            while b is not None :
                if dummy != m.get_value(b, 5) :
                    todos = False
                    break
                else :
                    b = m.iter_next(b)

            # Si están todos los hermanos igual, darle al padre el mismo valor
            if todos :
                m.set_value(p, 5, val)

        if val :
            # Marcar el primer hijo
            self.trz_view_toggle_child_lv2(c, True)
            # Marcarnos a nosotros mismos
            m.set_value(it, 5, val)

    def trz_view_toggle_child_lv2(self, it, val):
        """@brief Marcar/desmarcar en el treeview de análisis los casos
        concretos teniendo en cuenta a todos sus hermanos.
        @param iter Iterador al caso.
        @param val El valor del check DESPUÉS de pulsarlo.
        """
        # Acortamos nombres de árbol y vista
        m = self.trz_tree
        v = self.trz_view

        # Si lo marcamos, desmarcar a los hermanos y actualizar la
        # información del padre.
        # Si lo desmarcamos, nada.
        if val :
            p = m.iter_parent(it) # El padre es lv1
            c = m.iter_children(p) # El primer hijo
            # Recorremos todos los hijos de su padre desmarcándolos
            while c is not None :
                m.set_value(c, 5, False)
                c = m.iter_next(c)

            # Actualizar la info del padre con el timestamp del hijo
            pnom = m.get_value(p, 2) # El nombre del padre
            time = m.get_value(it, 3) # timestamp del hijo
            m.set_value(it, 3, time) # timestamp del padre
            time = util.clock.min_format(float(time)) # En formato cadena
            pnom = "%s (%s)" % (pnom,time) # Formato nombre padre
            m.set_value(p, 7, pnom)

            # Marcamos el valor para él y para el padre
            m.set_value(it, 5, val)
            m.set_value(p, 5, val)

    def trz_get_info(self):
        """@brief Obtiene información sobre el análisis desde la interfaz y la
        establece
        """
    ## @}

    ## @name Callbacks Trazas
    ## @{

    def on_trz_tree_toggle(self, render, path):
        # Acortamos nombres de árbol y vista
        m = self.trz_tree
        v = self.trz_view
        # Obtenemos un iterador a esa fila
        it = m.get_iter_from_string(path)
        # Averiguamos que profundidad hay
        lv = m.iter_depth(it)

        # Cambiamos el estado de lo que se ha pulsado
        val = not m.get_value(it, 5)
        #m.set_value(it, 5, val)

        # Si es de nivel 0 marcar/desmarcar todos los hijos nv 1
        # Si es de nivel 1 desmarcarlos todos, o marcar a él y al primer hijo
        # Si es de nivel 2 desmarcarlo, o marcarlo a el y desmarcar a sus
        # hermanos
        if lv == 0:
            self.trz_view_toggle_child_lv0(it, val)
        elif lv == 1:
            self.trz_view_toggle_child_lv1(it, val)
        else:
            self.trz_view_toggle_child_lv2(it, val)

    def on_trz_anl_button(self, widget):
        """Callback de pulsar el botón de analizar con Daikon."""
        # Siguiente página 
        self.proy_notebook_next()

        # Analizar
        self.analizar()


    def on_trz_opt_flat_combo(self, widget):
        """@brief Callback de cambiar la selección del combo."""
        self.proy.set_flattening(self.anl_aplanado_combo.get_active_text())

    def on_trz_opt_simplify_check(self, widget):
        """@brief Callback de cambiar el check de simplify."""
        self.proy.set_simplify(self.anl_simplify_check.get_active())

    ## @}

    ## @name Análisis
    ## @{

    def __init_anl(self):
        """Inicializa la parte de análisis"""
        # Cargar el glade de analisis
        self.gtk.add_from_file(path.join(self.opts.get('share'),
                                         "ui/proy_anl.glade"))
        # Obtener el contenedor y añadirlo al notebook
        self.anl_cont = self.gtk.get_object('proy_anl_container')
        self.anl_cont.reparent(self.gtk.get_object('proy_nb_anl_dummy_box'))

        ## Modelo con las trazas que van a entrar en análisis
        self.anl_tree = self.gtk.get_object('proy_anl_tree')
        ## Vista del treeview con las trazas que van a entrar en análisis
        self.anl_view = self.gtk.get_object('proy_anl_view')

        ## Label de aplanado
        self.anl_flat_label = self.gtk.get_object('proy_anl_data_flat_label')
        ## Label de simplify
        self.anl_sim_label = self.gtk.get_object('proy_anl_data_simplify_label')

        self.anl_listar_trazas()
        self.anl_actualizar_info()

        ## Combo de aplanado

    def analizar(self):
        """@brief Acciones a realizar al iniciar el ańalisis."""

        self.anl_listar_trazas()
        self.anl_actualizar_info()

        # Tomar las trazas seleccionadas en el treeview y añadirlas al
        # directorio de trazas a analizar.
        trz = self.anl_seleccionar_trazas()
        # Crear el thread con el análisis
        self.proy.analizar(trz)
        # Crear una instancia del thread de análisis
        thread = Analisis(self.proy,self,1)
        thread.start()
        log.debug(thread.isAlive())

    def anl_listar_trazas(self):
        """Establece en la lista de trazas de análisis, las trazas que van a
        entrar en Daikon."""

        # Toma las trazas seleccionadas en la pantalla de trazas
        trz = self.anl_seleccionar_trazas()

        # Las metemos en la lista de análisis
        # Desconectar el modelo
        self.anl_view.set_model(None) 

        # Vaciar el modelo 
        self.anl_tree.clear()

        # Función lambda para insertar los hijos
        insert = lambda x : self.anl_tree.insert(parent, 0, [x, ''])

        # Insertar los ficheros y sus hijos (casos)
        # [ Nombre, Icono ]
        for file, cases in trz.iteritems() :
            parent = self.anl_tree.insert(None, 0, [file, ''])
            map(insert, cases)

        # Volver a conectar el modelo
        self.anl_view.set_model(self.anl_tree)
        self.anl_view.expand_all()

    def anl_actualizar_info(self):
        """Actualiza la información sobre el análisis"""
        self.anl_flat_label.set_text(self.proy.get_flattening())
        self.anl_sim_label.set_text(str(self.proy.simplify))

    ## @}

    ## @name Callbacks Análisis
    ## @{

    def on_anl_exec_boton(self, widget):
        """@brief Callback de pulsar el botón de analizar en la parte de
        análisis
        """
        log.debug('Analizando')
        # Comenzar el análisis
        self.analizar()

    ## @}

    ## @name Invariantes
    ## @{

    def __init_inv(self):
        """Inicializa la parte de invariantes"""

        # Cargar el glade de invariantes
        self.gtk.add_from_file(path.join(self.opts.get('share'),
                                         "ui/proy_inv.glade"))
        # Obtener el contenedor y añadirlo al notebook
        self.inv_cont = self.gtk.get_object('proy_inv_container')
        self.inv_cont.reparent(self.gtk.get_object('proy_nb_inv_dummy_box'))

        self.inv_text_buffer = self.gtk.get_object('proy_inv_text_buffer')
        self.inv_data_time = self.gtk.get_object('proy_inv_data_time')
        self.inv_data_ninv = self.gtk.get_object('proy_inv_data_ninv')

    def inv_cargar(self):
        """@brief Carga el último fichero de invariantes en el buffer de invariantes"""
        inv = self.proy.inv_ultimo()
        if inv :
            finv = open(inv, 'r')
            self.inv_text_buffer.set_text(finv.read())
            finv.close()
        else:
            log.warning('Se intentó cargar un invariante, pero no hay.')

    ## @}
