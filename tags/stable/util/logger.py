# Soporte de logging unificado para toda la aplicacion.
# -*- coding: utf-8 -*-

import logging

def getlog(name, level = ""):
    """@brief Devuelve un objeto logger estandar bien configurado
       @param name Nombre del módulo que hace logging.
       @param level Nivel de logging."""

    # DEBUG por defecto si no se especifica, en otro caso, INFO
    LEVEL = logging.DEBUG if not level else logging.INFO

    # Formato para el log
    FORMAT = "%(levelname)s    \t%(name)s:  %(message)s"

    logging.basicConfig(format=FORMAT, level=LEVEL)
    return logging.getLogger(name)
