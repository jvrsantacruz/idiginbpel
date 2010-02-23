# -*- coding: utf-8 -*-
"""Clase que establece y maneja las opciones básicas del programa"""

import os.path as path
from xml.etree import ElementTree as et

# Establecer el log
import util.logger
log = util.logger.getlog('idg.opciones')

class Opt(object):
    """@brief Establece las opciones básicas leyendo el config.xml"""

    ## Diccionario con las opciones por defecto
    _opts = { 'home' : './home',
            'share' : './share',
            'takuan' : '~/takuan',
            'bpelunit': '~/AeBpelEngine',
            'svr' : 'localhost',
            'port' : '7777'
           }

    ## Diccionario con los atributos de las opciones por defecto
    _opts_nm = { 'home' : 'src',
            'share' : 'src',
            'takuan' : 'src',
            'bpelunit': 'src',
            'svr' : 'value',
            'port' : 'value'
           }


    def __init__(self, config):
        """@brief Construye el objeto Opt con la configuración. 
        @param config La ruta al fichero de configuración."""

        self.config = config

    def get(self, nom):
        """@brief Devuelve una opción. 
        @param nom El nombre de la opción.
        @retval El valor de la opción con nombre nom, o None si no existe.
        """
        return self._opts[nom] if nom in self._opts else None

    def set(self, nom, val, attr="src"):
        """@brief Establece una opción.
        @param nom El nombre de la opción.
        @param val El valor de la opción con nombre nom.
        @param attr (Opcional) El atributo en el que se guardará.
        @retval True si se ha creado una opción nueva. False en otro caso.
        """
        # Añadirlo a las opciones si no estaba
        retval = nom in self._opts
        if not retval :
            self._opts_nm[nom] = attr

        # Establecer la opción
        self._opts[nom] = val
        return retval

    def write(self):
        """@brief Escribe el fichero config.
        Escribe los cambios en el fichero config situado en opts[home], si no
        existe, lo crea.
        """

        config = self.config
        try:
            dom = et.ElementTree()
            root = dom.parse(config)
        except:
            log.error(_("No se ha podido abrir para escritura de opciones: ") +
                      config)
            return
        else:
            log.info(_("Escribiendo opciones config en: ") + config)

        for nom, attr in self._opts_nm.iteritems() :
            e = root.find(nom)
            # Si no existe, crearlo
            if e is None:
                e = et.SubElement(root, nom)

            e.set(attr, self._opts[nom])

        try:
            dom.write(config)
        except:
            log.error(_("No se han podido guardar las opciones en: ") + config)

    def read(self):
        """@brief Lee el fichero config."""

        config = self.config

        try: 
            dom = et.ElementTree()
            root = et.parse(config)
        except:
            log.error(_("No se ha podido parsear el fichero de config: ") +
                      config)
            return
        else:
            log.info(_("Usando fichero de configuración: ") + config)

        for nom,attr in (('home', 'src'), ('share', 'src'),
                         ('takuan', 'src'),('bpelunit', 'src'),
                        ('svr', 'value'), ('port', 'value')):

            # Buscar el elemento en el xml
            e = root.find(nom)
            if e is None or not e.get(attr):
                log.warning(_("Se usará el valor por defecto para: ") + nom)
                val = self._opts[nom] 
            else :
                val = e.get(attr)

            # Expandir la ruta si es un src
            if attr == 'src' :
                val = path.abspath(path.realpath(path.expanduser(val)))
                # Comprobar que la ruta existe
                if not path.exists(val) :
                    log.error(_("No se encuentra: ") + val)

            # Guardar en el diccionario los valores.
            self._opts[nom] = val
            self._opts_nm[nom] = attr

    def getall(self):
        """@brief Devuelve todas las opciones disponibles. """
        return self._opts

