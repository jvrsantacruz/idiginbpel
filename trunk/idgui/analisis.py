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

    ## Expresión regular para filtrar el log
    ## Filtra cadenas como estas :
    ## [apply] Processing multidimensional vectors in the Daikon dtrace '/home/arl/.idiginbpel/proy/sample/daikon-out-20100408-1659/MetaSearchTest.bpts:MaxItOut:1270738043.35.dtrace' using aplanarDTraceNodeSet.pl (6/8)...
    ## [apply] * number of CPUs:			1
    # 1. cadena
    re_str = " *\[apply\] (.*)$"

    ## Expresión regular para comprobar el éxito
    re_OK_str = "BUILD SUCCESSFUL"

    ## Expresión regular para comprobar el fracaso
    re_KO_str = "BUILD FAILED"

    ## Comienza Daikon
    re_daikon_str = "Running Daikon using"

    ## Cadena para parsear comienzo de procesamiento de logs
    re_exelog_str = "Converting execution log"

    ## Cadena para parsear comienzo de procesamiento 
    re_multilog_str = "Processing multidimensional vectors"

    ## Estado interno 
    estado = 'init'
    cont = 1

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

        # Compilar expresiones
        self.re = re.compile(self.re_str)
        self.re_OK = re.compile(self.re_OK_str)
        self.re_KO = re.compile(self.re_KO_str)
        self.re_daikon = re.compile(self.re_daikon_str)
        self.re_exelog = re.compile(self.re_exelog_str)
        self.re_multilog = re.compile(self.re_multilog_str)

    def filtrar(self, line ):
        """@brief Filtra una línea obtenida del log y actualiza la gui en
        consecuencia
        """

        m = self.re.match(line)
        if m : line = m.expand('\g<1>')

        m = self.re_OK.match(line) if not m else m 
        m = self.re_KO.match(line) if not m else m

        exps = ((self.re_OK, "ok"),
                (self.re_KO, "ko"),
                (self.re_daikon, "daikon"),
                (self.re_exelog, "exelog"),
                (self.re_multilog, "multilog"))

        m = name = None
        for rexp, nm in exps :
            m = rexp.match(line)
            if m :
                name = nm
                break

        try: 
            gtk.gdk.threads_enter()

            if name == 'ok' :
                # Poner la barra a tope
                #  y mensaje en el pie
                self.estado = 'ok'
                self.bar.set_fraction(1)
                self.bar.set_text('Completed')
                log.debug('Analisis done')

            elif name == 'ko' :
                # Poner la barra a tope 
                #  y mensaje en el pie
                self.estado = 'ko'
                self.bar.set_fraction(1)
                self.bar.set_text(_('Completed with errors'))
                log.debug('Analisis done with errors')

            elif name == 'daikon' :
                # Poner la barra a 2/3
                #  y mensaje en la barra
                self.estado = 'daikon'
                self.bar.set_fraction(2/3.0)
                self.bar.set_text(_('Ejecutando Daikon'))
                log.debug('Daikon')

            elif name == 'exelog' :
                # Poner la barra a 1/6
                #  y mensaje en la barra 
                if self.estado != 'exelog' :
                    self.estado = 'exelog'
                    self.bar.set_fraction(1/6.0)
                    self.cont = 0

                self.cont += 1
                text = "Processing logs (%i)" % self.cont
                self.bar.set_text(text)
                print 'Processing log (%i)\r' % self.cont,

            elif name == 'multilog' :
                # Poner barra a 1/3 
                #  y mensaje en la barra
                if self.estado != 'multilog':
                    self.estado = 'multilog'
                    self.bar.set_fraction(1/3.0)
                    self.cont = 0

                self.cont += 1
                text = "Processing multidimensional vectors (%i)" % self.cont
                self.bar.set_text(text)
                print 'Processing multidimensional vectors (%i)\r' % self.cont,

        finally:
            gtk.gdk.threads_leave()

    def run(self):
        """
        @brief Consulta el proceso de ejecución de los testcases y obtiene
        el log, actualizando la gui con el progreso de la misma.
        """
        log.debug('Entrando en check analisis')

        # Obtenemos el buffer de la interfaz
        buffer = self.ui.gtk.get_object('proy_anl_log_text_buffer')
        view = self.ui.gtk.get_object('proy_anl_log_text')

        # Obtenemos la barra de la interfaz y su label
        self.bar = self.ui.gtk.get_object('proy_anl_control_bar')

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

                # Filtrar la línea y actualizar la gui
                self.filtrar(line)

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
            self.ui.proyecto_notebook.next_page()
            self.ui.inv_cargar()
        finally:
            gtk.gdk.threads_leave()
