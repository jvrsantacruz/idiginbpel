# Clase de Proyecto Interfaz
# -*- coding: utf-8 -*-

import os.path as path
import pygtk
pygtk.require("2.0")
import gtk

from idg.proyecto import Proyecto,ProyectoError
import lang

class ProyectoUI:
    """@Brief Manejo de la interfaz de usuario del proyecto."""

    def __init__(self,idg,builder,nombre,bpel=""):
        """@Brief Clase que maneja la interfaz de un proyecto. Lo carga o crea
        al instanciarse.
           @param idg Instancia de la clase de control
           @param builder Instancia del tipo gtkbuilder
           @param nombre Nombre del proyecto a cargar/crear
           @param bpel (Opcional) Ruta al bpel para crear el proyecto.
           """

        # Instancia de idg
        self.idg = idg

        # Crear el proyecto
        try:
            self.proy = Proyecto(nombre,idg,bpel)
            self.idg.proyecto = self.proy
        except:
            # Por ahora cualquier excepción al crear el proyecto, lo manda todo
            # a tomar por saco.
            # TODO: Hacer excepciones recuperables y no recuperables.
            # Mostrar las recuperables en los errores en la interfaz.
            print _("Excepción [recuperable o no] al crear el proyecto")
            raise Exception()

        # Objeto gtkbuilder de idgui
        self.gtk = builder

        # Cargar el glade del proyecto
        self.gtk.add_from_file(path.join(self.idg.share,"ui/proyecto_base.glade"))

        # Obtener los elementos importantes

        # Contenedor de la gui 
        self.principal = self.gtk.get_object("principal")
        # Base del proyecto
        self.proyecto_base = self.gtk.get_object("proy_base_contenedor")
        # Cuaderno del proyecto
        self.proyecto_tab = self.gtk.get_object("proy_base_cuaderno")

        # Label indicador de errores y dejarlo vacío
        self.error_label = self.gtk.get_object("proy_base_errores_label")
        self.error("")

        # Nombre del proyecto
        self.nombre_label = self.gtk.get_object("proy_config_nombre_label")

        self.nombre_label.set_text(self.proy.nombre)

        # Configuración del servidor
        self.svr_texto = self.gtk.get_object("proy_config_svr_texto")
        self.svr_texto.set_text(self.proy.svr)

        self.port_texto = self.gtk.get_object("proy_config_port_texto")
        self.port_texto.set_text(self.proy.port)

        # Dependencias
        self.dep_totales_label = self.gtk.get_object("proy_config_dep_totales_label")
        self.dep_buenas_label = self.gtk.get_object("proy_config_dep_buenas_label")
        self.dep_rotas_label = self.gtk.get_object("proy_config_dep_rotas_label")
        self.actualizar_pantalla_config()

        # Conectar todas las señales
        self.gtk.connect_signals(self)

        # Situar en el contenedor y mostrar
        self.proyecto_base.reparent(self.principal)
        self.proyecto_base.show()

    def actualizar_pantalla_config(self):
        """@Brief Actualiza las variables y los datos de la pantalla config."""
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

    def on_proy_config_dep_inst_boton(self,widget):
        """@Brief Callback de pulsar el botón de buscar dependencias"""
        try:
            from idg.proyecto import ProyectoError
            self.proy.instrumentar()
        except ProyectoError:
            self.error(_("Error al instrumentar."))

    def on_proy_config_dep_buscar_boton(self,widget):
        """@Brief Callback de pulsar el botón de instrumentado"""
        try:
            from idg.proyecto import ProyectoError
            print self.proy.bpel_o
            self.proy.buscar_dependencias(self.proy.bpel_o)
        except ProyectoError:
            self.error(_("Se ha producido un error durante la búsqueda."))

        self.actualizar_pantalla_config()

    def error(self,msg):
        self.error_label.set_text(msg)
