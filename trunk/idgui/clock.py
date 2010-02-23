# -*- coding: utf-8 -*-
"""Clase reloj que actualiza periódicamente un label dado."""

import gtk
import time
from threading import Thread

import util.logger
log = util.logger.getlog('idgui.clock')

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
                log.warning(_("Intentando unpause en reloj no pausado"))

        def cancel(self):
            """@brief Mata y termina el thread."""
            self.end = True

        def run(self):

            while not self.end :

                # Diferencia desde que empezó hasta ahora
                diff = time.time() - self.tstart
                # Obtener dia, horas, minutos, segundos de esa diferencia
                date = time.gmtime(diff)
                sec = date[5]

                # No mostrar dias, horas o mins si no valen nada
                strfmt = "%i s" % sec
                if diff > 60 :
                    min = date[4]
                    strfmt = ("%i m " % min) + strfmt
                if diff > 3600 :
                    # Compensamos las horas, que empiezan en 01
                    hours = date[3] - 1
                    strfmt = ("%i h " % hours) + strfmt
                if diff > 86400 :
                    # Compensamos los días, que empiezan en 01
                    days = date[2] - 1 
                    strfmt = ("%i d " % days) + strfmt

                # Obtener cadena con el tiempo formateado
                strtm = time.strftime(strfmt, date)
                # Actualizar la hora
                try:
                    gtk.gdk.threads_enter()
                    self.label.set_text(strtm)
                finally:
                    gtk.gdk.threads_leave()

                # Dormir el thread un segundo
                time.sleep(1)

                # Comprobar el thread padre
                if self.padre is not None :
                    self.end = self.padre.poll() is not None

