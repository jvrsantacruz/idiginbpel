# Fichero principal
# -*- coding: utf-8 -*-

# Añadir el directorio de trabajo al path
import sys, os

# Ruta del programa al ejecutarse
base = os.path.abspath( sys.argv[0] )
# Ruta del directorio del script
path = os.path.dirname( base )

# Iniciar la aplicacion
if __name__ == "__main__":
	from idg import main
	global idgbpel 
	idgbpel = main.Idg(path)
