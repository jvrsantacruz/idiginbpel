# Clase Principal
# -*- coding: utf-8 -*-

import os 
import commands
import shutil
from proyecto import Proyecto,ProyectoError
import lang

class Idg(object):
    """@Brief Objeto principal, maneja el programa completo."""

    def __init__(self,path):
        """@brief Inicializa IndigBPEL
           @param path ruta base de ejecución del programa."""

        # Leer parámetros de la configuración
        #self.leer_config()

	# Ruta base de ejecución
    	self.path = path

        # Leer la lista de proyectos
        self.obtener_lista_proyectos()

        # Iniciar gui
        from idgui import main
        idgui = main.Idgui(self)

    def crear_proyecto(self,nombre,bpel):
        """@brief Crea un nuevo proyecto a partir de la ruta de un bpel y el nombre. 
           @param nombre Nombre del proyecto
           @param bpel Ruta al fichero bpel.
           @returns False si se ha creado correctamente. El error correspondiente en caso contrario.
        """
        # Comprobar formato del nombre
        if len(nombre) == 0: 
            return _("El nombre del proyecto no puede estar vacío")

        # Comprobar que el nombre no existe ya
        if nombre in self.lista_proyectos:
            return _("Ya existe un proyecto con ese nombre")

        if not os.path.exists( bpel ):
            return _("El fichero no existe ") + bpel 

        # Crear un objeto proyecto
	self.proyecto = Proyecto(nombre,bpel)

	# Actualizar la lista de proyectos
        self.obtener_lista_proyectos()

        return False;

    def obtener_lista_proyectos(self):
        """@brief Obtiene la lista de proyectos y comprueba posibles problemas."""
        # Leer los proyectos existentes en data
        self.lista_proyectos = os.listdir("data")
        self.lista_proyectos.sort()
        print self.lista_proyectos

    def comprobar_proyectos(self):
        """@brief Comprueba el estado adecuado de un proyecto antes de incluirlo en la lista.""" 
        pass

    def leer_config(self):
        """@brief Obtiene todos los parámetros generales de los ficheros de configuración."""
        self.config = {}

        # Ruta instrumentador
        # Ruta base-build.xml
        # n cpus
        pass

    def config(self, nombre):
        """@brief Obtener parámetros leidos de la configuración. 
           @nombre Nombre del parámetro a leer.
           @returns Valor del parámetro.
        """
        pass

    def cerrar(self):
        """@Brief Realiza comprobaciones y cierra ordenadamente"""

        # Si hay un proyecto abierto y tiene cambios
        # preguntar si debemos guardarlo.
        if not self.proyecto is None \
            and not self.proyecto.guardado is None:
            return True
        else:
            return False
