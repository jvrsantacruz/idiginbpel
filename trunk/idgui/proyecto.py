# Clase de Proyecto Interfaz
# -*- coding: utf-8 -*-

import os.path as path
import sys
import pygtk
pygtk.require("2.0")
import gtk

from idg.proyecto import *
import lang

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

        idgui.estado(_("Iniciando el proyecto"))
        # Crear el proyecto
        try:
            error = ""
            ## Referencia a la instancia del Proyecto actual
            self.proy = Proyecto(nombre,idg,bpel)
            self.idg.proyecto = self.proy
        except (ProyectoRecuperable) as e:
            # Mostrar las recuperables en los errores en la interfaz.
            print e
            idgui.estado(e)
        except:
            print _("Excepción irrecuperable al crear el proyecto")
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

        idgui.estado(_("Proyecto iniciado correctamente."))

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

        print ldep
        print ldep_miss

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
        except ProyectoError:
            self.error(_("Error al instrumentar."))
            self.idgui.estado(_("Error al instrumentar."))
        else:
            self.idgui.estado(_("Instrumentación correcta."))
            #self.mensaje(_("Instrumentación correcta."))

    def on_proy_config_dep_buscar_boton(self,widget):
        """@brief Callback de pulsar el botón de buscar dependencias
        @param widget Botón"""
        try:
            from idg.proyecto import ProyectoError
            print self.proy.bpel_o
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

    def add_bpts_tree(self):
        """@brief Cargar ficheros btps al treeview."""
        # Map fichero [caso1, caso2 ... ]

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
            print sys.exc_type, sys.exc_value
        else:
            self.idgui.estado(_("Añadido fichero bpts: ") + path.basename(bpts) )
            self.bpts_fichero.unselect_all()
    ##@}


