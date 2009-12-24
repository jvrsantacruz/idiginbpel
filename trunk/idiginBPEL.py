# Fichero principal
# -*- coding: utf-8 -*-
"""@Brief Iniciar sistema.
Establece la ruta de ejecución y crea el sistema.
"""

# Añadir el directorio de trabajo al path
import sys
from os.path import *
from idg import Idg

# Ruta del programa al ejecutarse
base = abspath( sys.argv[0] )
# Ruta del directorio del script
path = dirname( base )

# Buscamos la configuración
configs = ('~/.idiginbpel', './home', '/usr/share/idiginbpel')

config = ""
for c in configs:
    c = abspath(expanduser(join(c,'config.xml')))
    if exists(c):
        config = c
        break

# Iniciar la aplicacion
if __name__ == "__main__":
	global idgbpel 
	idgbpel = main.Idg(path,config)
