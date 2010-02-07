# Clase Principal
# -*- coding: utf-8 -*-

import os 
import os.path as path
import commands
import shutil
from xml.dom import minidom as md

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('idg.main')

#from proyecto import Proyecto,ProyectoError
from idgui.main import Idgui
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
    ## Ruta al directorio de instalación de takuan por defecto
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
        log.info(_("Proyectos disponibles: ") + str(self.lista_proyectos))

    def comprobar_proyectos(self):
        """TODO: @brief Comprueba el estado adecuado de un proyecto antes de incluirlo en la lista.""" 
        pass

    def set_config(self):
        """@brief Obtiene todos los parámetros generales de los ficheros de configuración."""
        try: 
            xml = md.parse(self.config)
        except:
            log.error(_("No se pudo leer el fichero de configuración ") + self.config) 
        else:
            log.info(_("Usando fichero de configuración: ") + self.config)

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
                    log.error(_("No se encuentra el directorio: ") + val)
                    raise Exception()
            except:
                log.warning(_("Se usará el valor por defecto para: ") + nom)

        # Imprimir los directorios usados
        log.info("Home: " + self.home)
        log.info("Share: " + self.share)
        log.info("Takuan: " + self.takuan)

    def exportar(self,nombre,ruta):
        """@brief Realiza un paquete tar en bz2 del directorio del proyecto.
        @param nombre Nombre del proyecto a exportar.
        @param ruta Ruta en la que se intentará depositar la exportación del
        proyecto."""

        if nombre not in self.lista_proyectos:
            return False

        eruta = path.join(ruta,nombre + '.proy')
        if path.exists(eruta) or os.access(ruta, R_OK or W_OK):
            return False

        # Comprimir el directorio del proyecto en tar
        try:
            import tarfile
            tar = tarfile.open(eruta, "w:bz2")
            tar.add(path.join(self.home,"proy",nombre))
            tar.close()
        except TarError:
            return False

        return True

    def importar(self,ruta):
        """@brief Importa un proyecto desde un paquete.
        @param nombre Nombre del proyecto a exportar.
        @retval True si todo va bien. False si no se ha podido importar."""

        # Si no existe o si no se puede leer, error
        if not path.exists(ruta) or os.access(ruta,F_OK or R_OK):
            return False

        try:
            import tarfile
            tar = tarfile.open(ruta, "r:bz2")
        except TarError:
            return False

        try:
            # Si el primer elemento no es un directorio 
            # es que el formato del proyecto está mal.
            if not tar[0].isdir():
                return False

            # El nombre del proyecto será el del 1º dir
            nom = tar[0].name

            # Comprobamos que el nombre del proyecto no esté ya usado
            i = 1
            while nom in self.lista_proyectos:
                nom = "%s-%d" % (tar[0].name,i)
                ++i
            # Descomprimimos
            tar.extractall(path.join(self.home,"proy"))
        except TarError:
            return False
        # Actualizar la lista de proyectos
        self.obtener_lista_proyectos()
        return True

    def cerrar(self):
        """TODO: @brief Realiza comprobaciones y cierra ordenadamente"""

        # Si hay un proyecto abierto y tiene cambios
        # preguntar si debemos guardarlo.
        if not self.proyecto is None \
            and not self.proyecto.guardado is None:
            return True
        else:
            return False
