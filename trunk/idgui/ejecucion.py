# -*- coding: utf-8 -*-
"""Clase Monitorizadora de la ejecucion de los casos de prueba"""

import os
import shutil
import time
import re
import gtk
from threading import Thread

import util.logger
log = util.logger.getlog('idgui.ejecucion')

from idgui.clock import Clock

class Ejecucion(Thread):
    """@brief Comprueba periódicamente, el estado de la ejecución de los
    tests leyendo de su log.
    """

    ## Expresión regular para filtrar el log
    ## Filtra cadenas como esta:
    ## [clase] 1 [caso] INFO paquete.paquetito - Mensaje: puede poner de todo
    ##  \[[^]]*\]  Es \[.*\] pero con cuidado
    ##  Los campos están separados por un solo espacio
    ## \d+ es el número
    ## (\w+) es para pillar el INFO/WARNING/ERROR
    ## (\w|\W) es para pillar el paquete
    ## Las backreferences son: 
    ## 1. tipo 2: paquete 3: clase 4: dummy 5: mensaje
    re_str = " *\[([^]]*)\] \d+ \[([^]]*)\] (\w+) (\w|\W)+ - (.*)$" 

    ## Expresión regular para comprobar el éxito
    re_OK_str = "BUILD SUCCESSFUL"

    ## Expresión regular para comprobar el fracaso
    re_KO_str = "BUILD FAILED"

    ## Expresión regular para capturar los inicios de casos
    re_inicaso_str = "Initiating testCase Test Case (.*)$"

    ## Expresión regular para capturar el final de los casos
    re_passcaso_str = "Test case passed."

    ## Expresión regular para capturar la parada de los casos
    re_stopcaso_str = "Stopping testCase Test Case (.*)$"

    ## Expresión regular para capturar error de conexión
    re_cnerror_str = ""

    ## Expresión regular para capturar el nombre y el nº de los casos con round
    re_casoround_str = "^(.*) \(Round (\d+)\)$"

    ## Caso actual en ejecución
    caso_actual = ""

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
        ## Número de casos a ejecutar
        self.ncasos = len(self.ui.ejec_path_casos)
        ## Contador de los casos que llevamos
        self.i_case = 0
        ## Barra de progreso
        self.barra = self.ui.ejec_barra
        self.barra.set_fraction( 0.0 )
        self.barra.set_text( _("Conectando...") )
        ## Pulso de la barra de progreso
        self.pulse = 0.95 / self.ncasos

        # Compilar expresiones para filtrar el log
        self.re_log = re.compile(self.re_str)
        self.re_OK = re.compile(self.re_OK_str)
        self.re_KO = re.compile(self.re_KO_str)
        self.re_inicaso = re.compile(self.re_inicaso_str)
        self.re_passcaso = re.compile(self.re_passcaso_str)
        self.re_stopcaso = re.compile(self.re_stopcaso_str)
        self.re_casoround = re.compile(self.re_casoround_str)

    def filtrar(self, line):
        """
         @brief Filtra una línea del log, aplicando las expresiones regulares
         correspondientes y calculando el progreso de la ejecución.
         @param line Línea obtenida del log.
         """

        # Filtrar las lineas del log
        # Aplicamos todas las expresiones hasta que una acierte
        exps = ((self.re_log, "log") , (self.re_OK, "ok"), (self.re_KO, "ko"))
        m = name = None
        for rexp, nm in exps :
            m = rexp.match(line)
            if m :
                name = nm
                break

        # Si es una linea de log, nos quedamos con los campos que
        # queremos
        if name == "log" : 
            # Modificamos la línea para que quede bonita en el log
            # Dejamos los campos de la clase, el nivel y el mensaje
            line = m.expand('\g<2> \g<3> \g<5>\n')

            if m.group(2) == 'main' and  \
               m.group(3) == 'INFO' :

                # Aplicamos expresiones al mensaje hasta que alguna acierte
                exps = ((self.re_inicaso, "ini"), (self.re_passcaso, "pass"),
                        (self.re_stopcaso, "stop"))
                e = name = None
                for rexp, nm in exps:
                    e = rexp.match(m.group(5))
                    if e :
                        name = nm
                        break

                # Según lo que hayamos encontrado en el mensaje, realizamos
                # distintas acciones.

                # ¿Iniciando un caso de prueba?
                # main INFO  Initiating textCase 'NOMBRE'
                if name == "ini"  :
                    caso = e.group(1)
                    round = None

                    # Comprobamos si es un caso con round
                    r = self.re_casoround.match(caso)
                    if r :
                        caso = r.group(1)
                        round = r.group(2)

                    # Comprobamos si el anterior era un caso con round y por
                    # tanto no se ha cerrado bien. Lo cerramos en ese caso.
                    if self.caso_actual is not None  \
                       and self.caso_actual != caso :
                        gtk.gdk.threads_enter()
                        self.ui.activar_ejec_caso(self.caso_actual, 3)
                        gtk.gdk.threads_leave()

                    # Establecemos la variable general caso
                    self.caso_actual = caso

                    log.info(_("Iniciando caso: ") + caso)

                    gtk.gdk.threads_enter()
                    # Flag de primer caso, ponemos 0.06 representando el
                    # trabajo realizado por la conexión.
                    if self.i_case == 0:
                        self.barra.set_fraction(0.06)

                    # Aumentar el contador si no es un round es el primer round
                    if round is None or round == '1' :
                        self.i_case += 1 

                    # Actualizamos el texto con el contador de casos
                    # tenemos en cuenta que los round tienen un texto diferente
                    if round is None :
                        self.barra.set_text("%i / %i" % (self.i_case , self.ncasos))
                    else :
                        nround = "%i (%s)" % (self.ncasos, round)
                        self.barra.set_text("%i / %s" % (self.i_case , nround))

                    self.ui.activar_ejec_caso(caso, 2)
                    gtk.gdk.threads_leave()

                # Mensaje Test case passed.
                # main INFO  Test case passed.
                elif name == "pass" :
                    log.info(_("Caso pasado"))

                # Finalizado el caso de prueba
                # main INFO Stopping testCase Test Case 'NOMBRE'
                elif name == "stop" :
                    caso = e.group(1)
                    rcaso = caso
                    round = None

                    # Comprobamos si es un caso con round
                    r = self.re_casoround.match(caso)
                    if r :
                        rcaso = r.group(1)
                        round = r.group(2)

                    log.info(_("Parado el caso: ") + rcaso)


                    if round is None :
                        # Marcamos el caso actual como terminado
                        self.caso_actual = None

                        gtk.gdk.threads_enter()
                        frac = self.barra.get_fraction() + self.pulse
                        self.barra.set_fraction( frac if frac <= 1 else 1 )
                        # Ponerle el icono correspondiente
                        self.ui.activar_ejec_caso(caso, 3)
                        gtk.gdk.threads_leave()

                    # Movemos el log generado y lo renombramos
                    BUpath = os.path.join(self.proy.bpelunit,'process-logs')
                    src = ""
                    dst = ""
                    try:
                        # Tomamos el primer log que haya en process-logs
                        src = os.path.join(BUpath, os.listdir(BUpath)[0])
                        file = caso + "-" + str(time.time()) + ".log"
                        dst = os.path.join(self.proy.trazas_dir, file)

                        log.info('Moviendo ' + src + ' a ' + dst)
                        # Y lo movemos al proyecto 
                        shutil.move(src, dst)
                    except:
                        log.error(_("Error al mover fichero de (src, dst): ") +
                                    src + " " + dst)

        elif name == "ok"  :
            log.info(_("Ejecución terminada correctamente"))

        elif name == "ko" :
            log.info(_("Error al ejecutar"))

        return line

    def run(self):
        """
        @brief Consulta el proceso de ejecución de los testcases y obtiene
        el log, actualizando la gui con el progreso de la misma.
        """
        # Obtenemos el buffer de la interfaz
        buffer = self.ui.ejec_log_buffer
        view = self.ui.ejec_log_text
        # self.ui.ejec_log_text.set_buffer(buffer) 
        #buffer = gtk.TextBuffer()

        # Obtenemos el subproceso instanciado en el proyecto
        subproc = self.proy.ejec_subproc

        # Control para el término del proceso
        # poll es None si el proceso no ha terminado aún.
        end = not subproc is None and not subproc.poll() is None

        # Tiempo desde el comienzo de ejecución
        # Ejecuta cada segundo la función time en un thread aparte
        # Le pasamos el label que tiene que actualizar y lo arrancamos.
        thread_timer = Clock(self.ui.ejec_control_tiempo_label)
        thread_timer.start()

        # El subproceso debe existir y no haber terminado
        while not subproc is None and not end:

            # Mandar a dormir para esperar
            time.sleep(self.t)
            log.debug("Comprobando Tests")

            # Saber si el proceso ha terminado
            end = not subproc.poll() is None
            # Leer lo que haya en la tubería
            while 1 :
                line = subproc.stdout.readline()
                if not line:
                    break

                # Filtramos la linea y la procesamos
                line = self.filtrar(line)

                try:
                    gtk.gdk.threads_enter()
                    # La añadimos al final del buffer de texto
                    iter = buffer.get_end_iter()
                    buffer.place_cursor(iter)
                    buffer.insert(iter, line)
                    view.scroll_to_mark(buffer.get_insert(), 0.1)
                    #buffer.insert_at_cursor(line)
                finally:
                    gtk.gdk.threads_leave()

        # Parar el reloj
        thread_timer.cancel()
        # Asegurarnos de que se termina la ejecución 
        #  y actualizar la gui en consecuencia.
        gtk.gdk.threads_enter()
        self.ui.ejec_terminar()
        gtk.gdk.threads_leave()
