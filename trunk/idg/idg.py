# Clase Principal
# -*- coding: utf-8 -*-

import os 
import os.path as path
import commands
import shutil
from xml.dom import minidom as md

from proyecto import Proyecto,ProyectoError
from idgui.idgui import Idgui
import lang

class Idg(object):
    """@brief Objeto principal, maneja el programa completo."""

    # Rutas a los directorios con los datos 
    # y la instalación de takuan
    # Valores por defecto para cuando no hay config.xml
    ## Ruta al directorio de usuario por defecto
    home = "./home"
    ## Ruta al directorio de datos por defecto
    share = "./share"
    ## Ruta al directorio de instalación de takuan
    takuan = "~/takuan"

    ## Referencia al objeto Proyecto abierto actualmente
    proyecto = None


    def __init__(self,path,config):
        """@brief Inicializa idiginBPEL y mantiene los datos básicos para el
        funcionamiento de la aplicación.
           @param path ruta base de ejecución del programa.
           @param config ruta absoluta del fichero de configuración."""

        # Leer parámetros de la configuración
        ## Ruta al fichero de configuración
        self.config = config
        self.set_config()

	## Ruta base de ejecución del programa
    	self.path = path

        # Leer la lista de proyectos
        self.obtener_lista_proyectos()
        # Iniciar gui
        ## Referencia al objeto con la GUI
        idgui = Idgui(self)

    def obtener_lista_proyectos(self):
        """@brief Obtiene la lista de proyectos y comprueba posibles problemas."""
        # Leer los proyectos existentes en home/proy
        # Eliminar directorios ocultos.
        ## Lista con los nombres de los directorios con los proyectos
        self.lista_proyectos = os.listdir(os.path.join(self.home,"proy"))
        self.lista_proyectos = [p for p in self.lista_proyectos if p[0] != '.']
        self.lista_proyectos.sort()
        print self.lista_proyectos

    def comprobar_proyectos(self):
        """TODO: @brief Comprueba el estado adecuado de un proyecto antes de incluirlo en la lista.""" 
        pass

    def set_config(self):
        """@brief Obtiene todos los parámetros generales de los ficheros de configuración."""
        try: 
            xml = md.parse(self.config)
        except:
            print _("No se pudo leer el fichero de configuración ") + self.config
        else:
            print _("Usando fichero de configuración: ") + self.config

        # Leer valores individuales y establecerlos en el objeto
        # Nombre del elemento y atributo a leer
        # Los comprobamos
        for nom,attr in (('home','src'), ('share','src'), ('takuan','src')):
            try:
                val = xml.getElementsByTagName(nom)[0].getAttribute(attr)
                val = path.abspath(path.expanduser(val))
                if path.exists(val):
                    setattr(self, nom , val)
                else:
                    print _("No se encuentra el directorio: ") + val
                    raise Exception()
            except:
                print _("Se usará el valor por defecto para: ") + nom 

        print "Home: ", self.home
        print "Share: ",self.share
        print "Takuan: ",self.takuan

    def cerrar(self):
        """TODO: @brief Realiza comprobaciones y cierra ordenadamente"""

        # Si hay un proyecto abierto y tiene cambios
        # preguntar si debemos guardarlo.
        if not self.proyecto is None \
            and not self.proyecto.guardado is None:
            return True
        else:
            return False
