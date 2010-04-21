# -*- coding: utf-8 -*-
"""Clase reloj que actualiza periódicamente un label dado."""

import gtk
import time
from threading import Thread

import util.logger
log = util.logger.getlog('idgui.clock')
from util.clock import min_format

class Clock(Thread):
        """@brief Calcula el tiempo de ejecución y lo establece en la gui
          Muere cuando se llama a cancel()."""

        def __init__(self, label, intervalo = 1, padre=None):
            """@brief Constructor del thread
            @param label Label a actualizar con el tiempo.
            @param intervalo Intervalo de actualización del reloj.
            @param padre Intancia del thread padre. Terminará con el.
            """
            Thread.__init__(self)
            ## Tiempo inicial
            self.tstart = time.time()
            ## Flag para parar el reloj y terminar con el thread
            self.end = False
            ## Pausa se utilizará para almacenar el tiempo que se ha pausado.
            self.pausa = False
            ## Label a actualizar con el reloj
            self.label = label
            ## Thread padre
            self.padre = padre

        def time(self):
            """@brief Devuelve el tiempo acumulado en segundos."""
            if self.pausa is not False :
                self.tstart += (time.time() - self.pausa)

            return time.time() - self.tstart

        def stime(self):
            """@brief Devuelve el tiempo acumulado en una cadena."""
            return min_format(self.time())

        def status(self):
            """@brief Devuelve si el reloj está en corriendo (True) o en pausa
            (False).
            """
            return self.pausa is False

        def pause(self):
            """@brief Pausa el reloj el cual deja de contar el tiempo hasta
            recibir una llamada con unpause.
            """
            self.pausa = time.time()

        def unpause(self):
            """@brief Quita la pausa del reloj y sigue contando el tiempo pero
            sin tener el cuenta el tiempo que ha estado pausado.  
            El reloj debe estar en estado de pausa previamente, de lo contrario
            no hará nada.
            """
            if self.pausa is not False :
                # Le añadimos a tstart los segundos que ha pasado en pausa.
                self.tstart += (time.time() - self.pausa)
                self.pausa = False
            else :
                log.warning(_("idgui.clock.is.not.pause.cant.resume"))

        def cancel(self):
            """@brief Mata y termina el thread."""
            self.end = True

        def run(self):
            while not self.end :

                # Obtener dia, horas, minutos, segundos de la
                # diferencia desde que empezó hasta ahora
                date = min_format(time.time() - self.tstart)

                # Actualizar la hora
                try:
                    gtk.gdk.threads_enter()
                    self.label.set_text(date)
                finally:
                    gtk.gdk.threads_leave()

                # Dormir el thread un segundo
                time.sleep(1)

                # Comprobar el thread padre
                if self.padre is not None :
                    self.end = self.padre.poll() is not None
