# -*- coding: utf-8 -*-
"""Clase que establece y maneja las opciones básicas del programa"""

import os.path as path
from xml.etree import ElementTree as et

# Establecer el log
import util.logger
log = util.logger.getlog('idg.options')

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

    def __init__(self, config, defaults={}):
        """@brief Construye el objeto Opt con la configuración. 
        @param config La ruta al fichero de configuración.
        @paran defaults Opciones por defecto de forma {id: [value, type], ..}
        """
        self.config = config
        self._defaults = defaults

        # Expand urls (relative paths to abs paths, and expand ~)
        for id, (val, type) in self._defaults.items() :
            # Expand and check paths
            if type == 'src':
                val = self.expand(val)
                if not self.check(val): continue

            # Insert into dictionary if is a valid one.
            self._defaults[id] = [val, type]

        # Add defaults to options.
        self._opts.update(self._defaults)

        # Read configuration
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
            val = self.expand(val)
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
        try:
            dom = et.ElementTree()
            root = dom.parse(self.config)
        except:
            log.error(_("idg.options.cant.open.for.write") + self.config)
            return
        else:
            log.info(_("idg.options.writting.config.in") + self.config)

        # For each option, find it in config or create it.
        for id, (val, type) in self._opts.items():
            e = root.find(id)
            # if e don't exist, create it.
            if e is None: e = et.SubElement(root, id)
            e.set(type, val)

        try:
            dom.write(self.config)
        except:
            log.error(_("idg.options.cant.write.file") + self.config)

    def expand(self, val):
        """@brief Expande una ruta y resuelve relativas.
        @param val Ruta a expandir
        """
        try: 
            val = path.abspath(path.realpath(path.expanduser(val)))
        except:
            pass

        return val

    def check(self, val):
        """@brief Comprueba que un argumento sea válido. 
        @param val Valor del atributo.
        @retval Devuelve True si es válido, False si no lo es.
        """
        if val is None: return False
        return path.exists(self.expand(val)) 

        return True

    def read(self):
        """@brief Lee el fichero config."""
        try: 
            dom = et.ElementTree()
            root = et.parse(self.config).getroot()
        except:
            log.error(_('idg.options.cant.parse.config.file') + self.config)
            return
        else:
            log.info(_('idg.options.using.config.file') + self.config)

        # Read all elements in config
        for e in root.getchildren() :
            #log.debug(e.tag)

            # Config element from xml
            id = e.tag
            type = 'src' if 'src' in e.attrib else 'value'
            val = e.get(type)

            # If attribute is path, expand and it
            # If is a non-valid path, none.
            if type == 'src' : 
                val = self.expand(val) if self.check(val) else None

            if val is None:
                log.error(_('idg.options.not.valid.value') + id + ": " + str(e.get(type)))
                if id in self._defaults :
                    log.warning(_('idg.options.using.default.value.for') + id)
                    val = self._defaults[id] 
                else:
                    log.warning(_('idg.options.not.found.default.value.for') + id)

            # Guardar en el diccionario los valores.
            self._opts[id] = [val, type]

    def getall(self):
        """@brief Devuelve todas las opciones disponibles. """
        return self._opts
