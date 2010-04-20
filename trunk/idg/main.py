# Clase Principal
# -*- coding: utf-8 -*-

import os 
import os.path as path

import commands
import shutil
import gettext
from xml.dom import minidom as md

# Establecer el log
import util.logger
log = util.logger.getlog('idg.main')

from opciones import Opt

# Traducciones mediante gettext
gettext.install('idiginbpel', './locale', unicode=1) # /usr/share/local en lugar de ./locale
log.warning(_('Usando locale en directorio local. ./locale No instaladas las locales.'))

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
    ## Ruta al directorio de BPELUnit
    bpelunit = '~/AeBpelEngine'

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
        ## Default values
        defaults = { 'home': ['~/.idiginbpel', 'src'],
                    'share': ['~/IdiginBPEL/share', 'src'],
                    'takuan': ['~/takuan', 'src'],
                    'bpelunit': ['~/bin/AeBpelEngine', 'src'],
                    'svr': ['localhost', 'value'],
                    'port': ['7777', 'value']
                   }
        self.set_config(defaults)

	## Ruta base de ejecución del programa
    	self.path = path

        # Leer la lista de proyectos
        self.obtener_lista_proyectos()

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

    def set_config(self, defaults={}):
        """@brief Inicializa el sistema de opciones."""
        self.opt = Opt(self.config, defaults)

        # Basic options needed
        self.home = self.opt.get('home')
        self.share = self.opt.get('share')
        self.takuan = self.opt.get('takuan')

        # Log main values
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
        """@brief Realiza comprobaciones y cierra ordenadamente"""

        # Si hay un proyecto abierto lo cerramos antes de cerrar el programa.
        if self.proyecto is not None :
            self.proyecto.cerrar()
