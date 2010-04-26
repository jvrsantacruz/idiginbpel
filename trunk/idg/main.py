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
log.warning(_('idg.main.not.installed.locales'))

class Idg(object):
    """@brief Objeto principal, maneja el programa completo."""

    ## Default values (useful when config.xml cannot be found)
    _DEFAULTS = { 'home': ['~/.idiginbpel', 'src'],
                'share': ['~/IdiginBPEL/share', 'src'],
                'takuan': ['~/takuan', 'src'],
                'bpelunit': ['~/bin/AeBpelEngine', 'src'],
                'svr': ['localhost', 'value'],
                'port': ['7777', 'value']
               }

    ## Referencia al objeto Proyecto abierto actualmente
    proyecto = None

    def __init__(self,path,config):
        """@brief Inicializa idiginBPEL y mantiene los datos básicos para el
        funcionamiento de la aplicación.
           @param path ruta base de ejecución del programa.
           @param config ruta absoluta del fichero de configuración."""

        # Leer parámetros de la configuración
        ## Ruta al fichero de configuración
        self._config = config
        self.set_config(self._DEFAULTS)

	## Ruta base de ejecución del programa
    	self.path = path

        # Leer la lista de proyectos
        self.update_proylist()

    def get_proylist(self):
        """@retval Returns the proyect list."""
        return self._proylist

    def update_proylist(self):
        """@brief Update and returns the list of proyects.
        @returns The list of proyects.
        """ 
        # Leer los proyectos existentes en home/proy
        # Eliminar directorios ocultos.
        ## Lista con los nombres de los directorios con los proyectos
        self._proylist = os.listdir(os.path.join(self.home,"proy"))
        self._proylist = [p for p in self._proylist if p[0] != '.']
        self._proylist.sort()
        log.info(_("idg.main.available.proyects.list") + str(self._proylist))
        return self._proylist

    def comprobar_proyectos(self):
        """TODO: @brief Comprueba el estado adecuado de un proyecto antes de incluirlo en la lista.""" 
        pass

    def set_config(self, defaults={}):
        """@brief Initialize opts system and basic variables.
        @param defaults Dictionary with default values for options.
        """
        self.opt = Opt(self._config, defaults)

        # Basic options needed
        self.home = self.opt.get('home')
        self.share = self.opt.get('share')
        self.takuan = self.opt.get('takuan')

        # Log main values
        log.info("Home: " + self.home)
        log.info("Share: " + self.share)
        log.info("Takuan: " + self.takuan)

    def export(self, name, path):
        """@brief Make a tar (bz2) package with a proyect directory.
        @param name Name of proyect.
        @param path Where the tarfile will be saved.
        """
        if name not in self._proylist:
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
            while nom in self._proylist:
                nom = "%s-%d" % (tar[0].name,i)
                ++i
            # Descomprimimos
            tar.extractall(path.join(self.home,"proy"))
        except TarError:
            return False

        # Update de proyects list.
        self.update_proylist()
        return True

    def cerrar(self):
        """@brief Realiza comprobaciones y cierra ordenadamente"""

        # Si hay un proyecto abierto lo cerramos antes de cerrar el programa.
        if self.proyecto is not None :
            self.proyecto.cerrar()
