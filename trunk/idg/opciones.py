# -*- coding: utf-8 -*-
"""Clase que establece y maneja las opciones básicas del programa"""

import os.path as path
from xml.etree import ElementTree as et

# Establecer el log
import util.logger
log = util.logger.getlog('idg.options')
from idg.file import XMLFile

class Opt(object):
    """@brief Establece las opciones básicas leyendo el config.xml"""

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
        """@brief Construye el objeto Opt con la configuración. 
        @param config La ruta al fichero de configuración.
        @paran defaults Opciones por defecto de forma {id: [value, type], ..}
        """
        # Open and parse config file
        self.config = XMLFile(config)
        self.config.dom('et')

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
        """@brief Devuelve una opción. 
        @param id El nombre de la opción.
        @retval El valor de la opción con nombre nom, o None si no existe.
        """
        return self._opts.setdefault(id, [None])[0]

    def set(self, id, val, type=None):
        """@brief Establece una opción.
        @param id El nombre de la opción.
        @param val El valor de la opción con nombre nom.
        @param type (Opcional) El atributo en el que se guardará.
        @retval True si se ha creado una opción nueva. False si se ha
        actualizado una opción. None si no se ha modificado.

        Si la opción no estaba antes, hay que especificar type
        obligatoriamente. En otro caso es opcional.
        """
        # Añadirlo a las opciones si no estaba
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

        # Establecer la opción
        self._opts[id] = [val, type]

        return exists

    def reset(self):
        """@brief Reset to default value values in options wich have a default
        value
        """
        self._opts.update(self._defaults)

    def write(self):
        """@brief Escribe el fichero config.
        Escribe los cambios en el fichero config situado en opts[home], si no
        existe, lo crea.
        """
        dom = self.config.dom()
        if dom is None:
            log.error(_("idg.options.cant.open.for.write") + self.config.name())
        if self._config.save(self._opts)is None:
            log.error(_("idg.options.cant.open.for.write") + self._config.path())
            return
        else:
            log.info(_("idg.options.writting.config.in") + self._config.path())

    def check(self, val):
        """@brief Comprueba que un argumento sea válido. 
        @param val Valor del atributo.
        @retval Devuelve True si es válido, False si no lo es.
        """
        if val is None: return False
        return path.exists(ConfigFile.abspath(val))

    def read(self):
        """@brief Lee el fichero config."""

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
        """@brief Devuelve todas las opciones disponibles. """
        return self._opts
