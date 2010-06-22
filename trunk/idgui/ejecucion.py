# -*- coding: utf-8 -*-
"""Clase Monitorizadora de la ejecucion de los casos de prueba"""

import os
import shutil
import time
import re
import gtk
from threading import Thread

import util.logger
log = util.logger.getlog('idgui.tester')

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

    ## Expresión regular para capturar la parada de todos los casos
    re_passall_str = "Now stopping test suite:"

    ## Expresión regular para capturar un error dentro de un caso
    # 1. Texto del error
    re_errorcaso_str = "A test failure or error occurred on (.*)$"

    ## Expresión regular para capturar el nombre y el nº de los casos con round
    ## 1. Nombre del caso 2. Número del round
    re_casoround_str = "^(.*) \(Round (\d+)\)$"

    ## Caso actual en ejecución
    caso_actual = ""

    ## Error en el caso actual en ejecución
    caso_actual_error = False

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
        ## Período de comprobación
        self.t = tiempo
        ## Número de casos a ejecutar
        self.ncasos = len(self.ui.exe_path_cases)
        ## Contador de los casos que llevamos
        self.i_case = 0
        ## Barra de progreso
        self.barra = self.ui.ejec_barra
        self.barra.set_fraction( 0.0 )
        self.barra.set_text( _("idgui.tester.connecting") )

        # Compilar expresiones para filtrar el log
        self.re_log = re.compile(self.re_str)
        self.re_OK = re.compile(self.re_OK_str)
        self.re_KO = re.compile(self.re_KO_str)
        self.re_inicaso = re.compile(self.re_inicaso_str)
        self.re_passcaso = re.compile(self.re_passcaso_str)
        self.re_stopcaso = re.compile(self.re_stopcaso_str)
        self.re_casoround = re.compile(self.re_casoround_str)
        self.re_passall = re.compile(self.re_passall_str)
        self.re_errorcaso = re.compile(self.re_errorcaso_str)

        ## Pulso de la barra de progreso
        if self.ncasos != 0:
            self.pulse = 0.95 / self.ncasos
        else:
            self.pulse = 0

    ## @name Filtros
    ## @{

    def filtrar(self, line):
        """
         @brief Filtra una línea del log, aplicando las expresiones regulares
         correspondientes y calculando el progreso de la ejecución.
         @param line Línea obtenida del log.
         """

        # Filtrar las lineas del log
        # Aplicamos todas las expresiones hasta que una acierte
        exps = ((self.re_log, "log") , 
                (self.re_OK, "ok"), 
                (self.re_KO, "ko"))

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
            # 2. campo 3. nivel 5. mensaje
            line = m.expand('\g<2> \g<3> \g<5>\n')

            if m.group(2) == 'main' and  \
               m.group(3) == 'INFO' :

                # Aplicamos expresiones al mensaje hasta que alguna acierte
                exps = ((self.re_inicaso, "ini"), 
                        (self.re_passcaso, "pass"),
                        (self.re_stopcaso, "stop"), 
                        (self.re_passall, "passall"),
                        (self.re_passall, "passall"),
                        (self.re_errorcaso, "error")
                       )

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
                    self.init_case(caso)

                # Mensaje Test case passed.
                # main INFO  Test case passed.
                elif name == "pass" :
                    log.info(_("idgui.tester.pass.case"))

                # Finalizado el caso de prueba
                # main INFO Stopping testCase Test Case 'NOMBRE'
                elif name == "stop" :
                    caso = e.group(1)
                    self.stop_case(caso)

                elif name == "error" :
                    error = e.group(1)
                    self.error_case(error)

                # Terminados todos los casos
                # main INFO Now stopping test suite
                elif name == "passall" :
                    self.pass_all()

        elif name == "ok"  :
            log.info(_("idgui.tester.testing.succesfully"))

        elif name == "ko" :
            log.info(_("idgui.tester.testing.error"))

        return line

    def init_case(self, name):
        """@brief Función que procesa el inicio de un caso.
        Inicializa caso_actual con el nombre del caso.
        @param name El nombre del caso.
        """
        # Keep the original name
        oname = name
        # Comprobamos si es un caso con round
        r = self.re_casoround.match(name)
        if r :
            name = r.group(1)
            round = r.group(2)

        # Si el caso anterior era un round, y este caso que se abre no es un
        # round o es el primer round, es que se ha terminado el caso anterior
        # que tenia varios rounds. Actualizamos la gui en consecuencia.
        if self.caso_actual is not None and (not r or round == '1'):
            self.next_case(self.caso_actual)

        # Establecemos el caso como caso actual 
        self.caso_actual = name

        log.info("Iniciando caso: %s" % oname)

        # Actualizar la gui
        gtk.gdk.threads_enter()

        # Si es el primer caso, ponemos 0.06 representando el
        # trabajo realizado por la conexión.
        if self.i_case == 0:
            self.barra.set_fraction(0.06)
        # Aumentar el contador de casos si es un caso normal o el primer round
        if not r or round == '1' :
            self.i_case += 1 

        # Actualizamos el texto con el contador de casos
        # tenemos en cuenta que los round tienen un texto diferente
        #  Format:
        #  round: this_case / total_cases (this_round_case )
        #  no round: actual_case / total_cases 
        text = "%i / %i (%s)" % (self.i_case, self.ncasos, round) if r else \
                "%i / %i" % (self.i_case, self.ncasos) 
        self.barra.set_text(text)

        # Activar el estado de que está ejecutándose (estado 2)
        self.ui.activar_ejec_caso(name, 2)

        gtk.gdk.threads_leave()

    def stop_case(self, name) :
        """@brief Función que procesa la parada de un caso.
        @param name El nombre del caso
        """
        log.info("Case stopped: %s " % name)
        self.end_case(name)

    def pass_all(self):
        """@brief Función que procesa la parada de todos los casos."""
        # Cerrar el caso actual si está aún abierto
        if self.caso_actual is not None :
            self.stop_case(self.caso_actual) 

        # Poner la barra de progreso a tope
        gtk.gdk.threads_enter()
        self.barra.set_fraction(1)
        gtk.gdk.threads_leave()

    def error_case(self, error):
        """@brief Función que procesa el fallo de un caso.
        Establece la variable caso_actual_error a verdadera.
        @param name El nombre del caso
        @param error El texto del error
        """
        log.info("Error en el caso %s" % error)
        self.caso_actual_error = True

    ## @}

    ## @name Actions
    ## @{

    def end_case(self, name):
        """@brief Función que maneja el término de un caso
        Actualiza la barra y el tree en la gui y mueve el log correspondiente.
        Si es un round no mueve la barra.
        @param name El nombre del caso
        """
        log.info("Ending case: %s" % name)

        # ¿Is our case a round case or a complete one?
        round = self.re_casoround.match(name)

        if not round :
            # Mark actual complete case as finished
            self.caso_actual = None
            # Actualize gui
            self.next_case(name)

        # Move the (should be) only trace file in bpelunit logs directory
        BUpath = os.path.join(self.proy.bpelunit,'process-logs')
        src = ""
        dst = ""
        # Take the first trace file listed in bpelunit logs directory
        try:
            src = os.path.join(BUpath, os.listdir(BUpath)[0])
        except IndexError, e:
            log.error(_("no.trace.was.generated.at.end_case"))
            return

            log.debug("Lo que hay en process-logs: " + str(os.listdir(BUpath)))

        # Compose the name: completecasename:timestamp.log
        file = name + ":" + str(time.time()) + ".log"
        dst = os.path.join(self.proy.trazas_dir, file)

        log.info('Moving log from: ' + src + ' to: ' + dst)

        try:
            # Move into the proyecto
            shutil.move(src, dst)
        except:
            log.error("Error moving trace file %s from: %s to: %s"  \
                      % (name,src, dst))

    def next_case(self, name):
        """@brief Actualiza la barra incrementándola cuando se detecta que un
        caso completo (no un round) se termina.
        @param name El nombre del caso (completo, sin el rounds)
        """
        gtk.gdk.threads_enter()

        log.debug('Cerrando: %s' % name )

        # Make the bar grow
        frac = self.barra.get_fraction() + self.pulse
        self.barra.set_fraction( frac if frac <= 1 else 1 )

        # Set level and icon on treeview
        self.ui.activar_ejec_caso(name, 4 if self.caso_actual_error else 3)

        # Clean error flag
        self.caso_actual_error = False

        gtk.gdk.threads_leave()

    ## @}

    def terminate(self):
        """@brief Termina el proceso y cierra la ejecución al completo"""
        # Poner que pasamos todo en la gui
        self.pass_all()

        # Parar el reloj
        self.thread_timer.cancel()
        # Asegurarnos de que se termina la ejecución
        #  y actualizar la gui en consecuencia.
        gtk.gdk.threads_enter()
        self.ui.ejec_terminar()
        gtk.gdk.threads_leave()

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
        end = subproc is None or subproc.poll() is not None

        # Tiempo desde el comienzo de ejecución
        # Ejecuta cada segundo la función time en un thread aparte
        # Le pasamos el label que tiene que actualizar y lo arrancamos.
        #  también le pasamos el thread de ejecución para que quede ligado.
        self.thread_timer = Clock(label=self.ui.ejec_control_tiempo_label, padre=subproc)
        self.thread_timer.start()

        # El subproceso debe existir y no haber terminado
        while not end:

            # Mandar a dormir para esperar
            time.sleep(self.t)
            log.debug("Comprobando Tests")

            # Saber si el proceso ha terminado
            end = subproc.poll() is not None

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

        self.terminate()
