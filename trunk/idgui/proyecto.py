# Clase de Proyecto Interfaz
# -*- coding: utf-8 -*-

import os.path as path
import pygtk
pygtk.require("2.0")
import gtk
import lang

class ProyectoUI:
    """@Brief Manejo de la interfaz de usuario del proyecto."""

    def __init__(self,idg,builder):
        """@Brief Cargar un proyecto cargado creado rpeviamente en idg en proyecto_base
           @param idg Instancia de la clase de control
           @param builder Instancia del tipo gtkbuilder
           """

        # Instancia de id
        self.idg = idg
        # Instancia del proyecto
        self.proy = self.idg.proyecto 
        # Objeto gtkbuilder de idg
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

        # Gestionar posibles errores
        if len(self.proy.dep_miss) > 0 :
            self.error("%d dependencias rotas" % len(self.proy.dep_miss))

        # Conectar todas las señales
        self.gtk.connect_signals(self)

        # Situar en el contenedor y mostrar
        self.proyecto_base.reparent(self.principal)
        self.proyecto_base.show()

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

    def error(self,msg):
        self.error_label.set_text(msg)
