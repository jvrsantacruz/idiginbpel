# Clase Principal
# -*- coding: utf-8 -*-

import os 
import os.path as path
import commands
import shutil
import gettext
import tarfile
from xml.dom import minidom as md

# Establecer el log
from opciones import Opt
import util.logger
log = util.logger.getlog('idg.main')

# Traducciones mediante gettext
gettext.install('idiginbpel', './locale', unicode=1) # /usr/share/local en lugar de ./locale
log.warning(_('idg.main.not.installed.locales'))

class Idg(object):
    """@brief Main application class

    Opens and closes the program.
    Holds the basis of the program as basic paths and options.
    Loads the i18n system.
    Manages proyects (list, importation, exportation).
    """

    ## Default values (useful when config.xml cannot be found)
    _DEFAULTS = { 'home': ['~/.idiginbpel', 'src'],
                'share': ['~/IdiginBPEL/share', 'src'],
                'takuan': ['~/takuan', 'src'],
                'bpelunit': ['~/bin/AeBpelEngine', 'src'],
                'svr': ['localhost', 'value'],
                'port': ['7777', 'value']
               }

    ## Reference to the current open proyect.
    proy = None

    def __init__(self, path, config):
        """@brief Initialize idiginBPEL

        Reads config file, list available proyects and initialize options.
        @param path Absolute path to python executable file in the system.
        @param config Absolute path to the main config file.
        """

        self._config = config
    	self.path = path

        # Set up configuration and proyect list.
        self.set_config(self._DEFAULTS)
        self.update_proylist()

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

    def get_proylist(self):
        """@returns Returns the proyect list"""
        return self._proylist

    def update_proylist(self):
        """@brief Update and returns the list of proyects
        @returns The list of proyects
        """
        # List valid proyects in the user home.
        self._proylist = os.listdir(os.path.join(self.opt.get('home'),"proy"))
        self._proylist = [p for p in self._proylist if p[0] != '.']
        self._proylist.sort()
        log.info(_("idg.main.available.proyects.list") + str(self._proylist))

        return self._proylist

    def exportation(self, name, path):
        """@brief Make a tar (bz2) package with a proyect directory.
        @param name Name of proyect.
        @param path Where the tarfile will be saved.
        """
        if name not in self._proylist:
            return False

        # Check that the file doesn't exist and we can write there.
        tar_path = path.join(path, name + '.proy')
        if path.exists(tarname) or os.access(ruta, R_OK or W_OK):
            return False

        # Compress proyect directory
        try:
            tar = tarfile.open(tar_path, "w:bz2")
            tar.add(path.join(self.opt.get('home'), "proy", name))
            tar.close()
        except TarError:
            return None

        return True

    def importation(self, path):
        """@brief Imports a proyect from an exported package.
        @param path Path to the package.
        @retval True if everything is ok. False if the proyect cannot be
        imported.
        """

        # If path doesn't exist or cannot be accessed
        if not path.exists(path) or os.access(path ,F_OK or R_OK):
            return False

        try:
            import tarfile
            tar = tarfile.open(path, "r:bz2")
        except TarError:
            return False

        try:
            # If the first element isn't a directory, wrong format.
            if not tar[0].isdir():
                return False

            # Proyect name will be extracted from the root directory
            nom = tar[0].name

            # Check the name of the new proyect and rename if needed
            i = 1
            while nom in self._proylist:
                nom = "%s-%d" % (tar[0].name,i)
                ++i

            tar.extractall(path.join(self.home,"proy"))
        except TarError:
            return False

        # Update de proyects list.
        self.update_proylist()
        return True

    def close(self):
        """@brief Closes the program properly."""

        if self.proy is not None :
            self.proy.cerrar()
