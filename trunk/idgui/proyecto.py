# Clase de Proyecto Interfaz
# -*- coding: utf-8 -*-

import os.path as path
import pygtk
pygtk.require("2.0")
import gtk

from idg.proyecto import Proyecto,ProyectoError
import lang

class ProyectoUI:
    """@brief Manejo de la interfaz de usuario del proyecto."""

    def __init__(self,idg,builder,nombre,bpel=""):
        """@brief Clase que maneja la interfaz de un proyecto. Lo carga o crea
        al instanciarse.
           @param idg Instancia de la clase de control
           @param builder Instancia del tipo gtkbuilder
           @param nombre Nombre del proyecto a cargar/crear
           @param bpel (Opcional) Ruta al bpel para crear el proyecto.
           """

        ## Instancia de idg
        self.idg = idg

        # Crear el proyecto
        try:
            ## Referencia a la instancia del Proyecto actual
            self.proy = Proyecto(nombre,idg,bpel)
            self.idg.proyecto = self.proy
        except:
            # Por ahora cualquier excepción al crear el proyecto, lo manda todo
            # a tomar por saco.
            # TODO: Hacer excepciones recuperables y no recuperables.
            # Mostrar las recuperables en los errores en la interfaz.
            print _("Excepción [recuperable o no] al crear el proyecto")
            raise Exception()

        ## Objeto gtkbuilder de idgui
        self.gtk = builder

        # Cargar el glade del proyecto
        self.gtk.add_from_file(path.join(self.idg.share,"ui/proyecto_base.glade"))

        # Obtener los elementos importantes

        ## Contenedor de la gui 
        self.principal = self.gtk.get_object("principal")
        ## Base del proyecto
        self.proyecto_base = self.gtk.get_object("proy_base_contenedor")
        ## Cuaderno del proyecto
        self.proyecto_tab = self.gtk.get_object("proy_base_cuaderno")

        ## Label indicador de errores y dejarlo vacío
        self.error_label = self.gtk.get_object("proy_base_errores_label")
        self.error("")

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
        ## Label con el número de dependencias encontradas
        self.dep_buenas_label = self.gtk.get_object("proy_config_dep_buenas_label")
        ## Label con el número de dependencias rotas
        self.dep_rotas_label = self.gtk.get_object("proy_config_dep_rotas_label")

        ## Lista de depencencias Modelo Datos 
        self.dep_list = self.gtk.get_object("proy_config_dep_list")
        ## Lista de dependencias TreeView
        self.dep_view = self.gtk.get_object("proy_config_dep_view")

        # Actualizar la información de la configuración
        self.actualizar_pantalla_config()

        # Conectar todas las señales
        self.gtk.connect_signals(self)

        # Situar en el contenedor y mostrar
        self.proyecto_base.reparent(self.principal)
        self.proyecto_base.show()

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
        self.dep_buenas_label.set_text(str(ldep))
        self.dep_rotas_label.set_text(str(ldep_miss))

        # Iconos
        roto = self.dep_view.render_icon(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        buena = self.dep_view.render_icon(gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU)

        # Limpiar la lista de dependencias y añadir las nuevas
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

    def error(self,msg):
        self.error_label.set_markup('<span color="green">'+msg+'</span>')

    def mensaje(self,msg):
        self.error_label.set_markup('<span color="black">'+msg+'</span>')

    # Callbacks ##############################

    def on_proy_config_dep_inst_boton(self,widget):
        """@brief Callback de pulsar el botón de buscar dependencias
        @param widget Botón"""
        try:
            from idg.proyecto import ProyectoError
            self.proy.instrumentar()
        except ProyectoError:
            self.error(_("Error al instrumentar."))
        else:
            self.mensaje(_("Instrumentación correcta."))

    def on_proy_config_dep_buscar_boton(self,widget):
        """@brief Callback de pulsar el botón de instrumentado
        @param widget Botón"""
        try:
            from idg.proyecto import ProyectoError
            print self.proy.bpel_o
            self.proy.buscar_dependencias(self.proy.bpel_o)
        except ProyectoError:
            self.error(_("Se ha producido un error durante la búsqueda."))

        self.actualizar_pantalla_config()

