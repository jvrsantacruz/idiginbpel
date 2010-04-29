# -*- coding: utf-8 -*-
"""Clase que establece y maneja las opciones básicas del programa"""

import os.path as path
from xml.etree import ElementTree as et

# Establecer el log
import util.logger
log = util.logger.getlog('idg.options')
from idg.file import ConfigFile

class Opt(object):
    """@brief Holds options and syncronize with a xml file"""

    ## Default options dictionary
    ## { id : [ value, type] }
    _defaults = {}

    ## Actual options
    _opts = {}

    ## Diccionario con los atributos de las opciones por defecto
    _opts_nm = { 'home' : 'src',
            'share' : 'src',
            'takuan' : 'src',
            'bpelunit': 'src',
            'svr' : 'value',
            'port' : 'value'
           }

    ## Configuration File
    _config = None

    def __init__(self, config, defaults={}):
        """@brief Initializes Option object with the configuration.
        @param config Path to the config file.
        @paran defaults Dict with default options in this form:
            {id: [value, type], ..}
        """
        self._defaults = defaults

        # Check and fix paths in default options
        for id, (val, type) in self._defaults.items() :
            if type == 'src':
                val = ConfigFile.abspath(val)
                if not self.check(val): continue  # Don't use wrong paths

            # Insert into dictionary if is a valid one.
            self._defaults[id] = [val, type]

        # Add defaults to options.
        self._opts.update(self._defaults)

        # Open and read config file
        self._config = ConfigFile(config)
        self.read()

    def get(self, id):
        """@brief Returns an option.
        @param id The name of the option.
        @returns The value of the option with the given id, None if not
        present.
        """
        return self._opts.setdefault(id, [None])[0]

    def set(self, id, val, type=None):
        """@brief Set an option in the configuration.
        @param id The option identifier.
        @param val The value of the option with the identifier id
        @param type (Optional) src if is a path.
        @retval True a new option was created. False if a previous existing
        option was updated. None in case of error.

        Note: When setting a new option, type is mandatory.
        """
        exists = id in self._opts

        # If type is not specified, try to find it
        if type is None: 
            if not exists: 
                return None
            type = self._opts[id][1]

        # If type is src, check path.
        if type == 'src':
            val = ConfigFile.abspath(val)
            if not self.check(val): 
                return None

        # Set the option.
        self._opts[id] = [val, type]

        return exists

    def reset(self):
        """@brief Reset to default value values in options wich have a default
        value
        """
        self._opts.update(self._defaults)

    def write(self):
        """@brief Writes down the config file"""

        if self._config.save(self._opts)is None:
            log.error(_("idg.options.cant.open.for.write") + self._config.path())
            return
        else:
            log.info(_("idg.options.writting.config.in") + self._config.path())

    def check(self, val):
        """@brief Checks paths.

        @param val Path to check.
        @returns True if is a valid path, False otherwise.
        """
        if val is None: return False
        return path.exists(ConfigFile.abspath(val))

    def read(self):
        """@brief Reads options from the config file"""

        # Add options from config file.
        print self._config.get_all()
        for id, (val, type) in self._config.get_all().items():
            if type == 'src' and not self.check(val):  # Don't use wrong paths
                log.warning(_('idg.options.not.valid.use.default') + id +\
                             " " + val)
                continue
            self._opts[id] = [val, type]

        dom = self._config.dom()
        if dom is None:
            log.error(_('idg.options.cant.parse.config.file') +\
                      self._config.path())
            return
        else:
            log.info(_('idg.options.using.config.file') + self._config.path())

    def getall(self):
        """@brief Returns all options into a dictionary"""
        return self._opts
