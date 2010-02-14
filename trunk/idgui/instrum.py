# Clase Comprobadora de Instrumentacion
# -*- coding: utf-8 -*-

from threading import Thread
import gtk
import time

import util.logger
log = util.logger.getlog('idgui.instrum')

class Comprobador(Thread):
    """@brief Comprueba periódicamente, una vez lanzada la instrumentación, si esta se ha
    realizado o no"""

    def __init__(self,proy,proyUI,tiempo):
        """@brief Inicializa el Thread
        @param proy Instancia del proyecto
        @param proyUI Instancia de la UI del proyecto.
        @param tiempo Tiempo en segundos que se espera para comprobar."""
        Thread.__init__(self)
        self.proy = proy
        self.ui = proyUI
        self.t = tiempo

    def run(self):
        thread = self.proy.inst_thread
        thread.join()
        #while not thread is None and thread.isAlive() : 
            # Actualizar barra
            # Mandar a dormir para esperar
            # log.debug("Comprobando instrumentación")
            # self.proy.inst_thread.join()
            # time.sleep(self.t)
        try:
            gtk.gdk.threads_enter()
            if self.proy.inst:
                self.ui.idgui.estado(_("Instrumentación correcta"))
            else:
                self.ui.idgui.estado(_("La instrumentación ha fallado."))
        finally:
            gtk.gdk.threads_leave()
