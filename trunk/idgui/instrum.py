# Clase Comprobadora de Instrumentacion
# -*- coding: utf-8 -*-

from threading import Thread
import gtk
import time

import util.logger
log = util.logger.getlog('idgui.instrumenter')

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
        try:
            gtk.gdk.threads_enter()
            if self.proy.inst:
                self.ui.idgui.estado(_("idgui.instrumenter.finished.successfully"))
            else:
                self.ui.idgui.estado(_("idgui.instrumenter.failed"))
        finally:
            gtk.gdk.threads_leave()
