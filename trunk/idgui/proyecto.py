# Clase de Proyecto Interfaz
# -*- coding: utf-8 -*-

import os.path as path
import sys
import pygtk
pygtk.require("2.0")
import gtk

import util.logger
log = util.logger.getlog('idgui.proyecto')

from idg.proyecto import Proyecto, ProyectoError, ProyectoRecuperable, \
ProyectoIrrecuperable
from instrum import Comprobador

class ProyectoUI:
    """@brief Manejo de la interfaz de usuario del proyecto."""

    def __init__(self,idg,idgui,nombre,bpel=""):
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

        # Estado de la barra inferior
        idgui.estado(_("Iniciando el proyecto"))

        # Crear el proyecto
        try:
            error = ""
            ## Referencia a la instancia del Proyecto actual
            self.proy = Proyecto(nombre,idg,bpel)
            self.idg.proyecto = self.proy
        except (ProyectoRecuperable) as e:
            # Mostrar las recuperables en los errores en la interfaz.
            log.error(str(e))
            idgui.estado(e)
        except:
            log.error(_("Excepción irrecuperable al crear el proyecto"))
            raise

        # Cargar el glade del proyecto
        self.gtk.add_from_file(path.join(self.idg.share,"ui/proyecto_base.glade"))

        # Obtener los elementos de la gui

        ## Contenedor de la gui 
        self.principal = self.gtk.get_object("principal")
        ## Base del proyecto
        self.proyecto_base = self.gtk.get_object("proy_base_contenedor")
        ## Notebook en el que está contenido el proyecto
        self.proyecto_notebook = self.gtk.get_object("proy_base_cuaderno")

        ## Label indicador de errores y dejarlo vacío
        self.error_label = self.gtk.get_object("proy_base_errores_label")
        self.error(error)

        self.__init_config()
        self.__init_casos()

        # Conectar todas las señales
        self.gtk.connect_signals(self)

        # Situar en el contenedor y mostrar
        self.proyecto_base.reparent(self.principal)
        self.proyecto_base.show()

        self.mensaje("")
        idgui.estado(_("Proyecto iniciado correctamente."))

    def __del__(self):
        """@brief Destructor del Proyecto"""
        self.dep_list.clear()

    def error(self,msg):
        self.error_label.set_markup('<span color="red">'+msg+'</span>')

    def mensaje(self,msg):
        self.error_label.set_markup('<span color="black">'+msg+'</span>')

    ## @name Callbacks
    ## @{

    def proy_notebook_next(self,widget=None):
        """@brief Callback de pulsar el botón siguiente en el proyecto."""
        self.proyecto_notebook.next_page()
    ## @}

    ## @name Config
    ## @{

    def __init_config(self):
        """@brief Inicializar la pantalla de configuración."""
        ## Nombre del proyecto
        self.nombre_label = self.gtk.get_object("proy_config_nombre_label")

        self.nombre_label.set_text(self.proy.nombre)

        # Configuración del servidor
        ## Texto Url de conexión del servidor Active Bpel
        self.svr_texto = self.gtk.get_object("proy_config_svr_texto")
        self.svr_texto.set_text(self.proy.svr)

        ## Texto Puerto de conexión del servidor Active Bpel
        self.port_texto = self.gtk.get_object("proy_config_port_texto")
        self.port_texto.set_text(self.proy.port)

        # Dependencias
        ## Label con el número total de dependencias
        self.dep_totales_label = self.gtk.get_object("proy_config_dep_totales_label")
        ## Label con el número de dependencias rotas
        self.dep_rotas_label = self.gtk.get_object("proy_config_dep_rotas_label")

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
                l = [ buena, path.basename(d), _("Dentro del proyecto") ]
            self.dep_list.append(l)

    def listar_dependencias_config(self):
        """@brief Actualiza la lista de dependencias en el tree de config"""
        pass
    ## @}

    ## @name Callbacks Config
    ## @{

    def on_proy_config_dep_inst_boton(self,widget):
        """@brief Callback de pulsar el botón de instrumentar.
        @param widget Botón"""

        self.idgui.estado(_("Instrumentando..."))
        try:
            from idg.proyecto import ProyectoError
            self.proy.instrumentar()
            c = Comprobador(self.proy,self,2)
            c.start()
        except ProyectoError:
            self.error(_("Error al instrumentar."))
            self.idgui.estado(_("Error al instrumentar."))
            #self.mensaje(_("Instrumentación correcta."))

    def on_proy_config_dep_buscar_boton(self,widget):
        """@brief Callback de pulsar el botón de buscar dependencias
        @param widget Botón"""
        try:
            from idg.proyecto import ProyectoError
            log.info("Bpel original: " + self.proy.bpel_o)
            self.proy.buscar_dependencias(self.proy.bpel_o)
        except ProyectoError:
            self.error(_("Se ha producido un error durante la búsqueda."))

        self.actualizar_pantalla_config()
        self.idgui.estado(_("Dependencias encontradas: ") + \
                          str(len(self.proy.deps)))

    def on_proy_config_guardar_boton(self,widget):
        """@brief Callback de pulsar el botón de guardar en la pantalla de
        configuración de un proyecto."""
        # Recolectar información de los labels
        self.proy.svr = self.svr_texto.get_text()
        self.proy.port = self.port_texto.get_text()
        # Guardar el proyecto
        self.proy.guardar()
        self.idgui.estado(_("Proyecto guardado."))

    ## @}

    ## @name Casos
    ## @{

    def __init_casos(self):
        """@brief Inicializar la pantalla de casos de prueba."""
        # Configurar el filtro de ficheros btps
        self.gtk.get_object("proy_casos_bpts_filtro").add_pattern("*.bpts")
        ## Selector de ficheros bpts
        self.bpts_fichero = self.gtk.get_object("proy_casos_btps_fichero")
        ## TreeStore de los casos de prueba
        self.bpts_tree = self.gtk.get_object("proy_casos_tree")
        ## TreeView de los casos de prueba
        self.bpts_view = self.gtk.get_object("proy_casos_view")

        # Actualizar los casos en la vista
        self.actualizar_bpts_tree()

        # Información sobre el caso
        self.bpts_nombre_label = self.gtk.get_object("proy_casos_info_nombre_label")
        self.bpts_n_label = self.gtk.get_object("proy_casos_info_n_label")
        self.bpts_nsel_label = self.gtk.get_object("proy_casos_info_nsel_label")

    def actualizar_bpts_tree(self):
        """@brief Actualiza los ficheros btps en el treeview."""
        # Iconos de fichero y de caso
        #imgfich = self.dep_view.render_icon(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        #imgcaso = self.dep_view.render_icon(gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU)
        # Map fichero [caso1, caso2 ... ]
        # Desconectar la vista
        self.bpts_view.set_model(None)

        # Limpiar el modelo
        self.bpts_tree.clear()
        for fich,casos in self.proy.casos.iteritems() :
            log.info('Fichero bpts seleccionado: ' + fich)
            iter = self.bpts_tree.append(None, [ fich, gtk.STOCK_OPEN, True])
            for c in casos :
                log.info('\tCaso: ' + c)
                self.bpts_tree.append(iter, [ c , gtk.STOCK_FILE, True])

        # Conectar la vista de nuevo
        self.bpts_view.set_model(self.bpts_tree)

    def info_bpts_fichero(self,fichero):
        """@brief Establece la información sobre un fichero de casos de prueba
        seleccionado.
        @param fichero Nombre del fichero de prueba"""
        if fichero not in self.proy.casos :
            self.error(_("No existe el fichero en el proyecto"))
        else:
            self.bpts_nombre_label.set_text(fichero)
            self.bpts_n_label.set_text(str(len(self.proy.casos[fichero])))
            self.bpts_nsel_label.set_text(str(""))

    def add_casos(self):
        """@brief Añade los ficheros seleccionados para ser ejecutados""" 
        # Vaciar los casos seleccionados anteriormente
        self.proy.vaciar_bpts(self.proy.test)

        # Recorremos el modelo árbol mirando que casos y ficheros están seleccionados
        m = self.bpts_tree # Acortar el nombre al tree

        f = m.get_iter_root()   # El primer fichero
        # Recorremos todos los ficheros 
        while not f is None:
            # Si está marcado, miramos los casos hijos
            if m.get_value(f, 2) :
                fnom = m.get_value(f, 0)    # Nombre del fichero
                c = m.iter_children(f)      # El primer hijo
                log.debug(_("Marcando como seleccionado el fichero: ") + fnom)

                casos = []

                # Recorremos todos los casos hijos de fichero 
                # y los metemos en casos
                while not c is None:
                    # Añadimos el nombre del fichero y del caso si este está activo
                    if m.get_value(c,2) :
                        cnom = m.get_value(c, 0)
                        casos.append(cnom) # Nombre del caso
                        log.debug(_("\t add el caso: ") + cnom)
                    # Siguiente caso
                    c = m.iter_next(c)

                self.proy.add_casos(fnom,casos)

            # Siguiente fichero
            f = m.iter_next(f)
    ## @}

    ## @name Callbacks Casos
    ## @{

    def on_proy_casos_bpts_fichero(self,widget):
        """@brief Callback de seleccionar un fichero bpts."""
        self.idgui.estado(_("Añadiendo fichero de casos de prueba"))
        bpts = self.bpts_fichero.get_filename()
        try:
            self.proy.add_bpts(bpts)
        except(ProyectoRecuperable):
            self.idgui.estado(_("Error al añadir fichero de casos de prueba"))
            log.error(str(sys.exc_type) + str(sys.exc_value))
        else:
            self.idgui.estado(_("Añadido fichero bpts: ") + path.basename(bpts) )
            self.bpts_fichero.set_filename("")
            self.actualizar_bpts_tree()

    def on_bpts_view_check_toggle(self,render,path):
        # Obtenemos el modelo y el iterador
        model = self.bpts_tree
        it = model.get_iter_from_string(path)

        # Cambiar el valor booleano
        if not it is None:
            # Cambiamos el valor que tiene ahora mismo
            val = not (model.get_value(it, 2))
            model.set_value(it, 2, val)

            # Si es un fichero, cambiar también sus hijos
            # Y mostrar su información
            if model.get_value(it, 1) == gtk.STOCK_OPEN :
                self.info_bpts_fichero(model.get_value(it,0))
                child = model.iter_children(it)
                while not child is None:
                    model.set_value(child, 2, val)
                    child = model.iter_next(child)

    def on_proy_casos_ejec_ana_boton(self, widget):
        self.add_casos()

    def on_proy_casos_ejec_boton(self, widget):
        self.add_casos()
    ##@}


