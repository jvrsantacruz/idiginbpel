# Main class
# -*- coding: utf-8 -*-

import os 
import os.path as path
import commands
import shutil
import gettext
import tarfile
import locale

from xml.dom import minidom as md

import util.logger
log = util.logger.getlog('idg.main')

from opciones import Opt

# /usr/share/local instead of ./locale
app = 'idiginbpel'
ldir = './locale'

locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain(app, ldir)

gettext.bindtextdomain(app, ldir)
gettext.textdomain(app)

lang = gettext.translation(app, ldir)
_ = lang.gettext

gettext.install(app, ldir)
gettext.install(app, ldir, unicode=1)

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
                'bpelunit': ['~/AeBpelEngine', 'src'],
                'activebpel': ['~/bin/ActiveBPEL.sh', 'src'],
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

    def exportation(self, name, filepath):
        """@brief Make a tar (gz) package with a proyect directory.
        @param name Name of proyect.
        @param filepath Where the tarfile will be saved.
        """
        if name not in self._proylist:
            return False

        if self.proy is not None and self.proy.nombre == name:
            self.proy.guardar()

        # Compress proyect directory
        try:
            tar = tarfile.open(filepath, "w:gz")
            tar.add(path.join(self.opt.get('home'), "proy", name), arcname=name)
            tar.close()
        except tarfile.TarError, e:
            log.error(e)
            return None

        return True

    def importation(self, filepath):
        """@brief Imports a proyect from an exported package.
        @param file Path to the package.
        @retval True if everything is ok. False if the proyect cannot be
        imported.
        """

        # If path doesn't exist or cannot be accessed
        if not path.exists(filepath) or not os.access(filepath ,os.F_OK or os.R_OK):
            return False

        try:
            tar = tarfile.open(filepath, "r:gz")
        except tarfile.TarError, e:
            log.error(e)
            return False

        # Get the name of the root directory in the tarfile
        member = tar.getmembers()[0]

        # If the first element isn't a directory, wrong format.
        if not member.isdir():
            log.error(_("idg.importation.wrong.format" + filepath))
            return False

        # Check the name of the new proyect and rename if needed
        nom = member.name
        i = 1
        while nom in self._proylist:
            nom = "%s-%d" % (member.name, i)
            i += 1

        # Exctract files into a temporary dir
        extractpath = path.join(self.home, "proy", nom + ".tmp")
        try:
            tar.extractall(extractpath)
        except tarfile.TarError, e:
            log.error(e)
            return False

        # Move files from nom.temp/member.name to nom 
        # and delete nome/member.name
        try:
            shutil.move(path.join(extractpath, member.name), 
                        path.join(self.home, "proy", nom))
            shutil.rmtree(path.join(extractpath))
        except shutil.Error, e:
            log.error(e)
            return False

        # Update de proyects list.
        return True

    def close(self):
        """@brief Closes the program properly."""

        if self.proy is not None :
            self.proy.cerrar()
            self.proy = None
