# Fichero principal
# -*- coding: utf-8 -*-
"""@Brief Iniciar sistema.
Establece la ruta de ejecución y crea el sistema.
"""

# Añadir el directorio de trabajo al path
import sys
import os.path as path
from idg.main import Idg

# Ruta completa del programa 
abspath = path.realpath(__file__)
ruta = path.dirname(abspath)

# Añadir este directorio al path para poder importar los módulos
sys.path.insert(0,ruta)

# Buscamos la configuración en los posibles home,  o la por defecto en share
configs = ('~/.idiginbpel', './home', '/usr/share/idiginbpel')

# Buscar el config.xml en las posibles rutas por el orden especificado
config = ""
for c in configs:
    c = path.abspath(path.expanduser(path.join(c,'config.xml')))
    if path.exists(c):
        config = c
        break

# Iniciar la aplicacion
if __name__ == "__main__":
	global idgbpel 
	idgbpel = Idg(ruta,config)
