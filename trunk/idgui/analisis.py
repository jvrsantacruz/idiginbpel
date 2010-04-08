# -*- coding: utf-8 -*-
"""Clase Monitorizadora del análisis de las trazas en Daikon"""

import os
import shutil
import time
import re
import gtk
from threading import Thread

import util.logger
log = util.logger.getlog('idgui.analisis')

from idgui.clock import Clock

class Analisis(Thread):
    """@brief Comprueba periódicamente el estado del subproceso de análisis
    leyendo su salida.
    """

    def __init__(self, proy, proyUI, tiempo):
        """@brief Inicializa el Thread
        @param proy Instancia del proyecto
        @param proyUI Instancia de la UI del proyecto
        @param tiempo Tiempo en segundos que se espera para comprobar.
        """
        Thread.__init__(self)
        ## Instancia del proyecto
        self.proy = proy
        ## Instancia de la gui
        self.ui = proyUI
        ## Período de comprobación
        self.t = tiempo

    def run(self):
        """
        @brief Consulta el proceso de ejecución de los testcases y obtiene
        el log, actualizando la gui con el progreso de la misma.
        """
        log.debug('Entrando en check analisis')

        # Obtenemos el buffer de la interfaz
        buffer = self.ui.gtk.get_object('proy_anl_log_text_buffer')
        view = self.ui.gtk.get_object('proy_anl_log_text')

        ## Subproceso a comprobar
        sproc = self.proy.anl_subproc

        # Controlar el fin del subproceso
        # poll es None si el proceso no ha terminado aún
        end = sproc is None or sproc.poll() is not None

        timer = \
                Clock(label=self.ui.gtk.get_object('proy_anl_control_time_label'),
                      padre=sproc)
        timer.start()

        while not end:

            # Dormir 
            time.sleep(self.t)
            log.debug('Checking Analisis')

            # ¿Ha terminado?
            end = sproc.poll() is not None

            # Leer de la tubería del proceso
            while 1:
                line = sproc.stdout.readline()
                if not line :
                    break

                # Añadimos la línea al buffer
                try: 
                    gtk.gdk.threads_enter()
                    iter = buffer.get_end_iter()
                    buffer.insert(iter, line)
                    view.scroll_to_mark(buffer.get_insert(), 0.1)
                finally:
                    gtk.gdk.threads_leave()

                # Al terminar el bucle, parar el reloj
                timer.cancel()

        # Tras el análisis copiar los invariantes a la carpeta de invariantes.
        self.proy.anl_copiar_inv()
        # Movernos a la siguiente pestaña y mostrarlos
        try: 
            gtk.gdk.threads_enter()
            self.ui.next_page()
            self.inv_mostrar()
        finally:
            gtk.gdk.threads_leave()
