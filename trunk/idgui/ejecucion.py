# -*- coding: utf-8 -*-
"""Clase Monitorizadora de la ejecucion de los casos de prueba"""

import gtk
import time
import re
from threading import Thread

import util.logger
log = util.logger.getlog('idgui.ejecucion')

class Timer(Thread):
        """@brief Calcula el tiempo de ejecución y lo establece en la gui
          Muere cuando muere el thread de ejecución."""

        def __init__(self, padre, ui):
            """@brief Constructor del thread
            @param padre Thread padre.
            """
            Thread.__init__(self)
            self.tstart = time.time()
            self.tnow = self.tstart - 1
            self.padre = padre
            self.ui = ui
            self.end = False

        def cancel(self):
            """@brief mata el thread."""
            self.end = True

        def run(self):

            while self.padre.is_alive() and not self.end:
                # Actualizar la hora si ha pasado un segundo
                ttemp = time.time()
                tstart = self.tstart

                tnow = ttemp
                diff = tnow - tstart
                # Obtener dia, horas, minutos, segundos de la diferencia
                date = time.gmtime(diff)
                # Ajustar 01 días y 01 horas a 0 
                days = date[2] - 1 
                hours = date[3] - 1
                min = date[4]
                sec = date[5]

                # No mostrar dias, horas o mins si no valen nada
                strfmt = "%i s" % sec
                if diff > 60 :
                    strfmt = ("%i m " % min) + strmft
                if diff > 3600 :
                    strfmt = ("%i h " % hours) + strfmt
                if diff > 86400 :
                    strfmt = ("%i d " % days) + strfmt

                # Obtener cadena con el tiempo formateado
                strtm = time.strftime(strfmt, date)
                # Actualizar la hora
                try:
                    gtk.gdk.threads_enter()
                    self.ui.ejec_control_tiempo_label.set_text(strtm)
                finally:
                    gtk.gdk.threads_leave()

                # Dormir el thread un segundo
                time.sleep(1)

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
                    log.info(_("Iniciando caso: ") + caso)

                    gtk.gdk.threads_enter()
                    # Flag de primer caso, ponemos 0.06 representando el
                    # trabajo realizado por la conexión.
                    if self.i_case == 0:
                        self.barra.set_fraction(0.06)
                    self.i_case = self.i_case + 1
                    self.barra.set_text("%i %s %i" % (self.i_case, _("de"),
                                                    self.ncasos))
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
                    log.info(_("Parado el caso: ") + caso)
                    gtk.gdk.threads_enter()
                    self.barra.set_fraction( self.barra.get_fraction() +
                                            self.pulse )
                    self.ui.activar_ejec_caso(caso, 3)
                    gtk.gdk.threads_leave()

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
        thread_timer = Timer(self, self.ui)
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
