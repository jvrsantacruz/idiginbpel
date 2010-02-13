# -*- coding: utf-8 -*-
"""Clase Monitorizadora de la ejecucion de los casos de prueba"""

import gtk
import time
import re
from threading import Thread

import util.logger
log = util.logger.getlog('idgui.ejecucion')

class Ejecucion(Thread):
    """@brief Comprueba periódicamente, el estado de la ejecución de los
    tests leyendo de su log.
    """

    ## Expresión regular para filtrar el log
    ## Filtra cadenas como esta:
    ## [clase] 1 [caso] INFO paquete.paquetito - Mensaje: puede poner de todo
    ##  \[[^]]*\]  Es \[.*\] pero con ojo
    ##  Los campos están separados por un solo espacio
    ## \d+ es el número
    ## (\w+) es para pillar el INFO
    ## (\w|\W) es para pillar el paquete
    ## Las backreferencias son: 
    ## 1: paquete 2: clase 3: dummy 4: mensaje
    re_str = " *\[[^]]*\] \d+ (\[[^]]*\]) (\w+) (\w|\W)+ - (.*)$" 

    def __init__(self,proy,proyUI,tiempo):
        """@brief Inicializa el Thread
        @param proy Instancia del proyecto
        @param proyUI Instancia de la UI del proyecto.
        @param tiempo Tiempo en segundos que se espera para comprobar."""
        Thread.__init__(self)
        ## Instancia del proyecto
        self.proy = proy
        ## Instancia de la gui del proyecto
        self.ui = proyUI
        ## Frecuencia de comprobación
        self.t = tiempo

        # Expresión para filtrar el log
        self.relog = re.compile(self.re_str)

    def run(self):
        textview = self.ui.ejec_log_text
        buffer = self.ui.ejec_log_buffer
        subproc = self.proy.ejec_subproc
        log.debug(str(subproc))

        # Control para el término del proceso
        end = not subproc.poll() is None

        # El subproceso debe existir y no haber terminado
        while not subproc is None and not end:

            # Mandar a dormir para esperar
            time.sleep(self.t)
            log.debug("Comprobando Tests")

            try:
                gtk.gdk.threads_enter()

                # Saber si el proceso ha terminado
                end = not subproc.poll() is None
                # Tomar 5 líneas o todo el fichero si el proceso ha terminado
                it_end = subproc.stdout if end else range(5)

                # Leer 5 líneas del log o lo que queda de la tubería
                # Y ponerlas en la gui en el buffer
                #  filtrándolas y procesándolas antes
                for line in it_end:
                    # Si el proceso no ha terminado, line será un nº
                    if not end:
                        line = subproc.stdout.readline()

                    # Filtrar las lineas del log
                    m = self.relog.match(line)
                    # Si es una linea de log, eliminar los campos que no
                    # queremos
                    if m : 
                        line = m.expand('\g<1> \g<2> \g<4>\n')

                    bf_end = buffer.get_end_iter()
                    buffer.insert(bf_end, line) 
            #except:
            #    log.debug("Error al monitorizar el proceso")
            finally:
                gtk.gdk.threads_leave()

