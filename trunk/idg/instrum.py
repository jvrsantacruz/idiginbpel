# Clase Instrumentadora
# -*- coding: utf-8 -*-

import commands
import re
import os.path as path
from threading import Thread

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('idg.instrum')

class Instrumentador(Thread):
    """@brief Esta clase realiza la instrumentación mediante threading para no
    dejar la gui congelada esperando el resultado. """

    ## Expresión regular para comprobar el resultado de la instrumentación
    resuccess = re.compile(r"BUILD SUCCESSFUL")
    ## Expresión regular para comprobar fallos en la instrumentación
    refileexc = re.compile(r"java.io.FileNotFoundException")

    def __init__(self,proy):
        """@brief Inicializa el Thread
        @param proy Instancia del proyecto para obtener los valores necesarios.
        """
        Thread.__init__(self)
        ## Instancia del proyecto
        self.proy = proy
        ## Resultado del comando de instrumentación.
        self.out = ""
        ## Contador de las veces que se ha intentado la instrumentación
        self.cont = 0

    def instrumentar(self):
        """@brief Ejecuta el comando en la consola y pone su salida en
        self.out"""
        # Comenzar la instrumentación mandando a consola el comando
        cmd = "ant -f %s build-bpr" % self.proy.build
        log.info(_("Ejecutando: ") + cmd)
        self.out = commands.getoutput(cmd)
        self.cont = self.cont + 1

    def comprobar(self):
        """@brief Comprueba self.out para saber el resultado de la
        instrumentación.
        @retval True si está bien, False si ha fallado y None si ha fallado por
        una excepción por dependencias"""
        if re.findall(self.resuccess, self.out) and path.exists(self.proy.bpr): 
            return True
        elif re.findall(self.refileexc, self.out): 
            return None
        else: 
            return False

    def run(self):
        """@brief Realiza el trabajo del thread"""
        # Intentar la instrumentación
        self.instrumentar()
        # Comprobar que se ha instrumentado correctamente
        c = self.comprobar()
        # Si ha sido por la falta de un fichero, volvemos a buscar
        # dependencias e intentamos instrumentar de nuevo.
        if self.cont > 1 : c = False

        if c is None:
            bpel = self.proy.bpel_o if path.exists(self.proy.bpel_o) else self.proy.bpel 
            self.proy.buscar_dependencias(bpel)
            self.instrumentar()
        elif c is False:
           # raise ProyectoRecuperable(_("No se pudo instrumentar") + out )
           pass

        # Establecemos en la clase proyecto si se ha instrumentado bien o no.
        self.proy.inst = c
        log.debug(self.out)
        log.info(_("Instrumentación terminada"))

