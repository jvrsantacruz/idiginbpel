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
        """@Brief Cargar un proyecto proy en proyecto_base
           @param idg Instancia de la clase de control
           @param proy Instancia del proyecto 
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
        self.svr_label = self.gtk.get_object("proy_config_svr_label")
        #self.proy.svr

        # Situar en el contenedor y mostrar
        self.proyecto_base.reparent(self.principal)
        self.proyecto_base.show()

    def error(self,msg):
        self.error_label.set_text(msg)
