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
    opts = { 'home' : './home',
            'share' : './share',
            'takuan' : '~/takuan',
            'bpelunit': '~/AeBpelEngine',
            'svr' : 'localhost',
            'port' : '7777'
           }

    ## Diccionario con los atributos de las opciones por defecto
    opts_nm = { 'home' : 'src',
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
        return self.opts[nom] if nom in self.opts else None

    def set(self, nom, val, attr="src"):
        """@brief Establece una opción.
        @param nom El nombre de la opción.
        @param val El valor de la opción con nombre nom.
        @param attr (Opcional) El atributo en el que se guardará.
        @retval True si se ha creado una opción nueva. False en otro caso.
        """
        # Añadirlo a las opciones si no estaba
        retval = nom in self.opts
        if not retval :
            self.opts_nm[nom] = attr

        # Establecer la opción
        self.opts[nom] = val
        return retval

    def write(self):
        """@brief Escribe el fichero config.
        Escribe los cambios en el fichero config situado en opts[home], si no
        existe, lo crea.
        """

        config = path.join(self.opts['home'], 'config.xml')
        try:
            dom = et.ElementTree()
            root = et.parse(config)
        except:
            log.error(_("No se ha podido abrir para escritura de opciones: ") +
                      config)
            return
        else:
            log.info(_("Escribiendo opciones config en: ") + config)

        for nom, attr in self.opts_nm.iteritems() :
            e = root.find(nom)
            # Si no existe, crearlo
            if not e :
                e = et.SubElement(root, nom)

            e.set(nom, attr, self.opts[nom])

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
            try:
                val = root.find(nom).get(attr)
            except:
                log.warning(_("Se usará el valor por defecto para: ") + nom)
                val = self.opts[nom] 
            finally:
                # Expandir la ruta si es un src
                if attr == 'src' :
                    val = path.abspath(path.realpath(path.expanduser(val)))
                    if not path.exists(val) :
                        log.error(_("No se encuentra: ") + val)

                self.opts[nom] = val
                self.opts_nm[nom] = attr

