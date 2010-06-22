# Clase Proyecto
# -*- coding: utf-8 -*-

import os
import os.path as path
import sys

import subprocess as subproc
import xml.dom.minidom as md
import xml.etree.ElementTree as et
import urllib
import shutil 
import re
import glob
import time

from file import ANTFile
from bptsfile import BPTSFile
from instrum import Instrumentador
import util.xml
import util.logger

log = util.logger.getlog('idg.proyect')

class ProyectoError(Exception):
    """@brief Clase excepción para la clase Proyecto"""

    def __init__(self,msj):
        self.msj = msj

    def __str__(self):
        return str(self.msj)

class ProyectoIrrecuperable(ProyectoError):
    """@brief Error irrecuperable de la clase Proyecto"""

class ProyectoRecuperable(ProyectoError):
    """@brief Error recuperable de la clase Proyecto"""

class Proyecto(object):
    """@brief Clase Proyecto con todas las operaciones sobre un proyecto
    idiginBPEL. Realiza la creación de un nuevo proyecto, la comprobación, el
    guardado y la eliminación así como todas las otras operaciones que tengan
    relación con un proyecto. """

    ## @name Nombres de ficheros por defecto
    ## @{

    ## Nombre del bpel importado
    bpel_nom   =   'bpel_original.bpel'
    ## Nombre del fichero de configuración de proyecto
    proy_nom   =   'proyecto.xml'
    ## Nombre del ant a ejecutar para realizar las acciones
    build_nom  =   'build.xml'
    ## Nombre del fichero que reune los casos de prueba
    test_nom   =   'test.bpts'
    ## Nombre del fichero bpr generado por la instrumentación
    bpr_nom    =   'bpr_file.bpr'
    ## @}

    ## @name Directorios de Proyecto
    ## @{

    ## Directorio con los casos de prueba
    casos_nom  =    'casos'
    ## Directorio 'almacén' con las trazas generadas por la ejecución
    trazas_nom =    'trazas'
    ## Directorio con las trazas que se van a usar en el análisis
    trazas_anl_nom = 'anl_trazas'
    ## Directorio con las trazas que se usarán en el análisis
    anltrazas_nom = 'anltrazas'
    ## Directorio con los invariantes generados
    invr_nom   =    'invariantes'
    ## Directorio con las dependencias del bpel
    dep_nom    =    'dependencias'
    ## @}

    ## @name Url de Namespaces 
    ## @{

    bpel_url = 'http://docs.oasis-open.org/wsbpel/2.0/process/executable'
    wsdl_url = 'http://schemas.xmlsoap.org/wsdl/'
    xsd_url  = 'http://www.w3.org/2001/XMLSchema'
    test_url = 'http://www.bpelunit.org/schema/testSuite'
    ## @}

    ## @name Configuración de conexión por defecto
    ## @{

    ## Url del servidor Active Bpel
    svr    =   'localhost'
    ## Puerto del servidor Active Bpel
    port   =   '7777'
    ## @}

    ## @name Flags de estado y propiedades
    ## @{

    ## Flag de instrumentado
    inst   =   False 
    ## Flag de modificado el proyecto
    mod    =   False 
    ## Exists cases flag
    have_cases = False
    # @}

    ## @name Inicialización 
    ## @{

    def __init__(self,nombre,idg,bpel=""):
        """@brief Constructor de la clase proyecto.  Establece los valores por
        defecto para las rutas del proyecto.  
        Crea el proyecto si se le indica la ruta a un bpel Lee la configuración
        del proyecto ya creado si no Comprueba que el proyecto esté bien 

        @param nombre Nombre del proyecto a cargar/crear.  
        @param idg Instancia de la clase de control .  
        @param bpel Ruta al bpel original.  
        """
        # Valores por defecto de proyecto

        ## Nombre del proyecto (se emplea en la ruta)
        self.nombre = nombre

        ## Instancia del control del proyecto
        self.idg = idg

        ## Instancia del control de opciones
        self.opts = idg.opt

        ## Ruta del bpel original (si está especificado)
        self.bpel_o =   path.abspath( bpel ) if bpel else ""

        # Variables internas, rutas, etc...
        self._set_vars()

        # Si se indica la ruta del bpel, debemos crear el proyecto 
        # Si ya está creado, leemos su configuración
        if not bpel :
            self.cargar_proy()
        else:
            self.crear()
            self.guardar()
            self.idg.update_proylist()

        # Load BPTSFiles
        self._load_bptsfiles()

        # Load Main bpts file (test)
        self.test = BPTSFile(self.test_path)

        # Proyecto instrumentado o no
        self.inst = path.exists(self.bpr)

        # Comprueba que la estructura del proyecto está bien
        try:
            self.check()
        except (ProyectoRecuperable) as e:
            log.error(_("idg.proyect.created.with.errors") + str(e))

        ## @name Listas
        ## @{

        ## Lista con los ficheros en el proyecto
        self.fichs  =   os.listdir(self.dir)

        ## Lista con los ficheros de las trazas
        self.ftrazas=   os.listdir(self.trazas_dir)
        ## Lista con los ficheros de invariantes
        self.finvr  =   os.listdir(self.invr_dir)
        ## @}

        # Set have cases flag
        self.have_cases = len([b.get_cases() for b in self.bptsfiles.values()]) > 0

    def _set_vars(self):
        """@brief Establece las variables internas del objeto"""

        idg = self.idg
        opt = self.opts

        # Urls generales de proyecto
        self.home       =   opt.get('home')
        self.share      =   opt.get('share')
        self.takuan     =   opt.get('takuan')
        self.bpelunit   =   opt.get('bpelunit')

        self.svr        =   opt.get('svr')
        self.port       =   opt.get('port')

        ## Directorio del proyecto
        self.dir        =   path.join(self.home,'proy',self.nombre) 
        self.dir        =   path.abspath( self.dir )

        ## @name Rutas de Ficheros 
        ## @{

        ## Ruta al bpel importado, se emplea para ejecutar etc...
        self.bpel = path.join(self.dir, self.bpel_nom)
        ## Ruta al fichero de configuración  del proyecto.
        self.proy = path.join(self.dir, self.proy_nom)
        ## Ruta al fichero ant para realizar las ejecuciones.
        self.build_path = path.join(self.dir, self.build_nom)
        ## Ruta al fichero bpts que contiene los casos de prueba.
        self.test_path = path.join(self.dir, self.test_nom)
        ## Ruta al fichero bpr que se genera en la instrumentación.
        self.bpr = path.join(self.dir, self.bpr_nom)
        ## @}

        ## @name Rutas Directorios 
        ## @{

        ## Ruta al directorio que contiene los casos de prueba
        self.casos_dir  =   path.join(self.dir, self.casos_nom ) # Casos
        ## Ruta al directorio que contiene todas las trazas
        self.trazas_dir =   path.join(self.dir, self.trazas_nom) # Trazas
        ## Ruta al directorio que contiene las trazas a usar en el análisis
        self.trazas_anl_dir = path.join(self.dir, self.trazas_anl_nom)
        ## Ruta al directorio que contiene las trazas
        self.anltrazas_dir =   path.join(self.dir, self.anltrazas_nom) # Trazas
        ## Ruta al directorio que contiene los invariantes
        self.invr_dir   =   path.join(self.dir, self.invr_nom)   # Invariantes
        ## Ruta al directorio que contiene las dependencias
        self.dep_dir    =   path.join(self.dir, self.dep_nom)    # Dependencias
        ## @}

        ## @name Listas 
        ## @{

        ## Lista con las rutas de las dependencias del bpel
        self.deps = []
        ## Lista con las rutas de las dependencias no encontradas del bpel
        self.dep_miss = []
        ## BPTSFiles dict with the bpts by name
        self.bptsfiles = {}
        ## @}

        ## @name Ejecución
        ## @{

        ## Subproceso de la ejecución
        self.ejec_subproc = None
        ## Thread instrumentador
        self.inst_thread = None
        ## @}

        ## @name Analisis
        ## @{
        
        ## Tipo de aplanado
        self.flattening = 'index-flattening'
        ## Simplify
        self.simplify = True

        ## Subproceso
        self.anl_subproc = None
        ## @}

    ## @}

    ## @name Tratar Bpel
    ## @{

    def buscar_dependencias(self, bpel):
        """@brief Busca las dependencias de un bpel recursivamente. 
           Copia el bpel y las dependencias al proyecto.
           Modifica el bpel y las dependencias para adaptarlos al proyecto
           \returns True si todo va bien, None si algo falla.
           Eleva excepciones ProyectoError.
        """

        # Comprobar el bpel que nos pasan
        if not path.exists( bpel ):
            log.error(_("idg.proyect.bpel.file.dont.exist") + bpel)
            raise ProyectoError( _("idg.proyect.bpel.file.dont.exist") + bpel)

        # Buscar las dependencias del bpel recursivamente
        ## Lista de rutas con las dependencias del bpel
        self.deps, self.dep_miss = self.__buscar_dependencias([bpel])

        log.info("%i dependencias encontradas, %i dependencias rotas, %i dependencias totales" % \
        (len(self.deps),len(self.dep_miss),len(self.dep_miss)+len(self.deps)) )

        return True

    def __buscar_dependencias(self,files,deps=set(),miss=set(),first=True):
        """@brief Busca las dependencias xsd y wsdl recursivamente en los
        ficheros y devuelve sus rutas completas. 
        Copia las dependencias al proyecto y las modifica para adaptar los
        import a rutas relativas al proyecto. 
        Añade las dependencias que no han podido ser obtenidas a dep_miss.
        @param files Lista con rutas a los ficheros en los que buscar
        @param first Flag para saber si estamos mirando el bpel original.
        @retval (deps,deps_miss) Listas con las rutas de las dependencias,
        encontradas y rotas.
        """

        if first:
            deps = set()
            miss = set()

        # Caso de parada de la función
        if len(files) == 0 :
            return []

        local_deps = set()

        # Buscamos en todas las rutas de ficheros que recibamos
        for f in files:

            nom = path.basename(f) # Nombre del fichero
            dir = path.dirname(f)  # Directorio del fichero
            proy = path.join(self.dep_dir, nom) # Ruta dentro del proyecto
            if path.exists(proy):   # Si ya existe en el proyecto
                miss.discard(dir)  # Quitamos de las dependencias rotas 

            log.debug(_("idg.proyect.dependence.list") + nom)

            # Abrimos el fichero, obtenemos uss imports, modificamos las rutas 
            # y lo serializamos de nuevo pero dentro del proyecto.

            # Cargar fichero en memoria
            try:
                xml = md.parse( f )
            except:
                # Mostramos un error y añadimos 
                # a las dependencias rotas
                log.error(_("idg.proyect.parse.error") + f)
                miss.add(f)
                continue

            # Buscar los imports en el fichero
            # empleando los distintos namespaces
            imps_l = xml.getElementsByTagName('import')
            imps_l += xml.getElementsByTagNameNS(self.bpel_url,'import')
            imps_l += xml.getElementsByTagNameNS(self.wsdl_url,'import')
            imps_l += xml.getElementsByTagNameNS(self.xsd_url,'import')
            imps = set(imps_l)

            # Modificar los import a rutas al mismo directorio
            # Obtener las rutas absolutas  meterlas en deps
            for i in imps:
                attr = 'location' if i.hasAttribute('location') else 'schemaLocation'
                # Si no está el atributo por alguna razón, pasar de el.
                ruta = i.getAttribute(attr) 
                if not ruta:
                    continue

                # Ruta real de la dependencia encontrada
                dep = path.abspath(path.join(dir, ruta))

                # Añadir la dependencia al conjunto local y total
                local_deps.add(dep)
                deps.add(dep)

                log.debug(nom + " --> " + path.basename(ruta))

                # Los bpel (first) apuntan a dentro del directorio  dependencias
                # El resto de dependencias, al mismo directorio en el que están.
                if first : 
                    ruta = path.join(self.dep_nom, path.basename(ruta))
                else:
                    ruta = path.basename(ruta)

                #log.debug(ruta)

                # Modificar el atributo con la ruta correcta
                i.setAttribute(attr, ruta)

            # Copiar el fichero en el proyecto
            try:
                # Serializar el xml a un fichero en el directorio self.dep_dir
                # Con la ruta adecuada si es el bpel original. 
                if first :
                    file = open(self.bpel,'w')
                else:
                    file = open(path.join(self.dep_dir, nom), 'w')

                file.write(xml.toxml('utf-8'))
            except:
                # Si no se ha podido escribir la versión modificada del
                # fichero, añadirlo a las dependencias rotas 
                log.error(_("idg.proyect.cant.write") + nom)
                miss.add(ruta)
            finally:
                file.close()

                # fin del for
        # fin del for

        # Llamada recursiva, false porque ya no es la primera llamada.
        self.__buscar_dependencias(list(local_deps), deps, miss, False)

        # Si es la primera llamada, devolvemos todas las dependencias.
        if first: 
            return list(deps), list(miss)
        # Si es una llamada normal, devolvemos los ficheros a mirar en
        # la siguiente iteración.
        else:
            return files

    ## @}

    ## @name Ejecuciones
    ## @{

    def instrumentar(self):
        """@brief Instrumenta el proyecto mediante dos subprocesos.""" 
        # No queremos dos thread para hacer lo mismo
        if self.inst_thread is None or not self.inst_thread.isAlive():
            self.inst = False
            # Comenzar la instrumentación
            self.inst_thread = Instrumentador(self)
            self.inst_thread.start()

    def ejecutar(self):
        """@brief Ejecuta los casos de prueba del proyecto en el servidor ABpel. """

        # No crear otro subproceso si ya se está ejecutando uno.
        if self.ejec_subproc is not None and self.ejec_subproc.poll() is None :
            log.warning(_("idg.proyect.test.already.running"))
            return

        # Ruta logs bpelunit
        #log.debug(self.bpelunit)
        BUpath = path.join(self.bpelunit, 'process-logs')

        # Comprobar que existe la ruta a bpelunit
        try:
            os.listdir(BUpath)
        except:
            log.error(_("idg.proyect.cant.find.bpelunit.path"))

        # Borrar los logs antiguos bpelunit
        try:
            self.borrar_trazas(BUpath)
        except:
            e = ProyectoRecuperable(_("idg.proyect.cant.remove.old.bpelunit.logs"\
                                      + BUpath))
            e.what = BUpath
            raise

        # Ejecutar el ant en un subproceso aparte
        cmd = ("ant", "-f", self.build_path, "test")
        log.info(_("idg.proyect.test.running.command") + str(cmd) )
        # Escribimos en una tubería desde la cual podremos leer el log
        # Sin expansión de argumentos por shell
        # El resultado va todo a stdout, el de stderr también.
        self.ejec_subproc = subproc.Popen(cmd, 
                                          shell = False,
                                          stdout = subproc.PIPE,
                                          stderr = subproc.STDOUT)

    def comprobar_abpel(self):
        """@brief Comprueba el estado del servidor ActiveBpel.
           @returns True si está corriendo, False si no lo está, None si no se
           pudo conectar.
           """

        # Abrir la url del servidor en el puerto predeterminado de tomcat
        url = "http://%s:%s/BpelAdmin/home.jsp"  % (self.svr, '8080')

        # Realizar la conexión
        try:
            f = urllib.urlopen(url)
            log.info(_("idg.proyect.test.activebpel.server.connection") + url)
        except IOError:
            log.error(_("idg.proyect.cant.connect.activebpel.server") + url)
        else:
            # Comprobar el código http 
            log.debug(_("idg.proyect.activebpel.server.response.code") +\
                      str(f.getcode()))

            # Expresión regular para saber si está activo
            patron = re.compile('.*Running.*')

            active = False
            # leer el resultado
            for line in f :
                if patron.match(line) :
                    active = True
                    break
            log.info(_("idg.proyect.activebpel.server.status") + \
                     'Running' if active else 'Stopped' )
            return active

        return None

    def cancelar_ejecucion(self):
        """@brief Termina la ejecución matando el proceso relacionado."""
        try:
            self.ejec_subproc.kill()
        except:
            return False
        else :
            log.info("Subproceso de ejecución matado")
            return True

    def seleccionar_trazas_analisis(self, trz):
        """@brief El análisis utiliza las trazas que están en el directorio
        anl_trazas de manera que hay que enlazar las trazas seleccionadas para
        el análisis desde trazas a anl_trazas.
        @param trz Trazas seleccionadas en una estructura tipo 
        trz[fichero][caso] = t_file
        """
        # Acortar nombres
        anl_tdir = self.trazas_anl_dir 
        tdir = self.trazas_dir

        # Limpiar ficheros antiguos seleccionados
        # El directorio anl_tdir puede que no exista
        self.borrar_trazas(anl_tdir)

        log.debug('Linking trace files from %s to %s for analysis'  
                  % (tdir, anl_tdir))

        # Añadir la selección actual enlazando los ficheros desde su lugar en
        # self.trazas_dir
        for file, cases in trz.items() :
            for case, tfile in cases.items() :
                os.link(path.join(tdir,tfile), path.join(anl_tdir, tfile))

    def analizar(self, trz):
        """@brief Ejecuta los scripts de aplanado y el motor Daikon sobre las
        trazas seleccionadas."""

        self.seleccionar_trazas_analisis(trz)

        # No crear otro subproceso si ya se está ejecutando
        if self.anl_subproc is not None and self.anl_subproc.poll() is None :
            log.warning(_("idg.proyect.analysis.already.running"))
            return

        cmd = ["ant", "-f", self.build_path, "analyze"]
        log.info(_("idg.proyect.analysis.running.command") + str(cmd))
        # Abrimos un proceso y leeremos de su salida estandar.
        # Redireccionamos la salida de errores a la estandar.
        self.anl_subproc = subproc.Popen(cmd,
                                         shell = False,
                                         stdout = subproc.PIPE,
                                         stderr = subproc.STDOUT)
        return self.anl_subproc
    ## @}

    ## @name Casos de prueba
    ## @{

    def list_bpts(self,path):
        """@brief Lista los casos de prueba que hay en un bpts.
           @param path Ruta del fichero
           @returns Una lista con los nombres de los casos."""

        # Lo parseamos con ElementTree 
        # Abrirlo
        try:
            bpts = et.ElementTree()
            bproot = bpts.parse(path)
        except:
            raise ProyectoRecuperable(_("idg.proyect.cant.load.testcases.file") + path)

        # Construir los nombres con la uri es un peñazo
        ns = "{%s}" % self.test_url

        # Encontramos elementos básicos
        testSuite = bproot
        tCases = bproot.find(ns + 'testCases')

        # Buscamos todos los casos de prueba y los devolvemos.
        return [c.get('name') for c in tCases.findall(ns + 'testCase')]

    def add_bpts(self, path_):
        """@brief Add a new bpts to proyect.

        @param path_ The path to the new bpts.

        The new bpts will be copied into the proyect, procesed, normalized and
        its connection info will be added to the main bpts file.
        Raises ProyectoRecuperable
        """
        # Comprobamos que exista y se pueda leer
        if not path.exists(path_) or not os.access(path_, os.F_OK or os.R_OK):
            raise ProyectoRecuperable(_("idg.proyect.testcase.file.dont.exist"))

        # Nombre del fichero y directorio de la ruta
        name = path.basename(path_)

        # Escapamos los caracteres separadores ':' por '.'
        # Add timestamp to name
        name = name.replace(':', '.')
        name += str(time.time())

        p_path = path.join(self.casos_dir, name)

        # Copy to the proyect
        try:
            shutil.copy(path_, p_path)
        except:
            raise ProyectoRecuperable(_("idg.proyect.cant.copy.file.to.proyect") \
                    + path_)

                # Open the proyect copy of the bpts file and process it
        bpts = BPTSFile(p_path)
        bpts.autodeclare()
        bpts.save()

        # Add file to proyect BPTSFile list
        self.bptsfiles[bpts.name()] = bpts

        # copy new information from bpts to main bpts file
        self.test.copy_info(bpts, self.dep_nom)
        self.test.save()

    def get_bpts(self, name):
        """@brief Returns the bpts with the given name or None if doesn't
        exists"""
        try:
            return self.bptsfiles[name]
        except KeyError:
            return None

    def empty_test(self):
        """@brief Removes all cases in the main bpts file."""
        self.test.rm_all()
        self.test.save()

    def add_casos(self, casos):
        """@brief Adds Testcases to test.bpts

        @param casos A cases dictionary { nom_fichero: [nom_caso, ..], ..}

        Opens every bpts file, get the listed cases and adds to the test.bpts
        if not already in it.
        """
        # Cases inside test.bpts
        test_cases = self.test.get_cases()
        test_names = [c.name() for c in test_cases]

        # TestCases marked to stay into the test.bpts
        names_to_keep = []

        for fnom in casos:
            long_names = [fnom + ':' + c for c in casos[fnom]]

            # Skip file if all cases are already stored in test.bpts
            if len([c for c in test_cases if c not in long_names]) == 0\
               and len(test_cases) != 0:
                names_to_keep.extend(long_names)
                continue

            # Load the file with the cases and list the cases.
            bpts = BPTSFile(path.join(self.casos_dir, fnom))
            cases = bpts.get_cases()
            name_cases = [c.name() for c in cases]

            for case in long_names:

                # Check the case inside the bpts
                if case not in name_cases:
                    log.warning('idg.proyect.try.to.add.case.not.present')
                    continue

                # And mark it to do not delete from test.bpts
                names_to_keep.append(case)

                # Skip if we already have in the test.bpts
                if case in test_names:
                    log.debug('ya está dentro del cases: ' + case)
                    continue

                # Effectively adding the case.
                self.test.add_case(bpts.get_case(case))

        # Delete cases not listed in casos
        [self.test.rm_case(c) for c in test_names\
         if c not in names_to_keep]

        # Save changes
        self.test.save()

    ## @}

    ## @name Trazas
    ## @{

    def borrar_trazas(self, dir):
        """@brief Borra todas las trazas.log en un directorio.
        @param dir El directorio .
        """
        log.info('Cleaning old trace files from %s' % self.trazas_anl_dir)
        [os.remove(path.join(dir,f)) for f in os.listdir(dir) if f.endswith('.log')]

    def trazas_disponibles(self):
        """@brief Devuelve las trazas disponibles en un diccionario
        trazas[fichero][caso] = [trace_file, trace_file ..] 
        @retval Una lista con los nombres de los ficheros de trazas.
        """
        return self.dict_trazas(os.listdir(self.trazas_dir))

    def ordenar_trazas(self, trazas):
        """@brief Toma una lista con nombres de ficheros de trazas y la
        devuelve ordenada por tiempo de generación de mayor a menor timestamp
        es decir, de más nueva a la más antigua.
        @retval La lista trazas ordenada por tiempos de la más nueva a la más
        antigua.
        """
        # Función que obtiene un float con el tiempo de la traza
        n2f = lambda n : float(self.parse_traza(n)[2])

        def traza_time_cmp(x, y):
            # Nombre a float 
            #(sacar el timestamp del nombre de la traza y convertirlo a float.)
            # Devolver la diferencia 
            try: 
                return int(n2f(y) - n2f(x))
            except :
                return -1

        # Ordenar las trazas por tiempo de ejecución
        trazas.sort(traza_time_cmp)
        return trazas

    def parse_traza(self, traza):
        """@brief Toma el nombre de un fichero de traza y devuelve 3 valores,
        fichero, caso, time
        @param traza El nombre del fichero de traza.
        @retval Los 3 valores fich, caso, time 
        """
        # Estructura de los nombres
        # 0(fichero):1(caso):2(timestamp)
        # Ejemplo: LoanApprovalProcess.bpts:LargeAmount-1267033799.94.log
        # El timestamp se encuentra en segundos y es obtenido con time.time()
        try:
            fich, caso, time = traza.split(':')
            time = time.rsplit('.',1)[0]
        except:
            #log.warning(_("Hay una traza que no sigue el formato: " + traza))
            return "","",""

        return fich, caso, time

    def dict_trazas(self, trazas):
        """@brief Toma una lista con nombres de ficheros de trazas y devuelve
        un objeto del tipo  trazas[fichero][caso] = [fich_traza, ..]
        @param trazas Lista con los nombres de los ficheros de trazas.
        @retval Un diccionario  donde los nombres de los ficheros de trazas están ordenados de más
        reciente a más antiguo.
        { fichero : {
                        caso_prueba: [fich_traza 1, fich_traza 2, ..],
                        caso_prueba2: [fich_traza 1, fich_traza 2, ..],
                        ...
                    } 
        }
        """

        # Diccionario a devolver
        trz = {}

        # Ordenar las trazas que se pasan
        tord = self.ordenar_trazas(trazas)

        # Añadir las trazas al diccionario
        #  como están ordenadas, se añaden a las listas por orden.
        for f in tord :
            fich, caso, time = self.parse_traza(f)

            #log.debug("fichero %s , caso %s, time %s" % (fich,caso,time))
            if not fich or not caso or not time :
                log.warning("Wrong format for trace file %s " % f )
                continue

            if fich not in trz :
                trz[fich] = {}

            if caso not in trz[fich] :
                trz[fich][caso] = []

            trz[fich][caso].append(f)

        return trz

    def ultimas_trazas(self, trazas) :
        """@brief Devuelve las últimas trazas disponibles en una
            lista.
            @param trazas Lista con los nombres de los ficheros de trazas.
            @retval Lista con el más reciente de cada caso de los ficheros de
            traza.
        """
        tr = {}
        tord = self.ordenar_trazas(trazas) 
        tend = []
        for f in tord : 
            nom = f.rsplit(':', 1)[0]

            if nom not in tr :
                tr[nom] = True
                tend.append(f)

        return tend

    ## @}

    ## @name Analisis
    ## @{

    def get_flattening(self):
        """@returns Analyzer flattening mode"""
        return self.flattening

    def set_flattening(self, mode):
        """@brief Set the analyzer flattening mode

        @param mode The flattening mode
        """
        self.flattening = mode

    def set_simplify(self, flag):
        """@brief Establece el modo de simplify"""
        self.simplify = flag

    def anl_copiar_inv(self):
        """Copia el último invariante generado en la última ejecución a la carpeta
        de invariantes. Renombrándolos convenientemente"""
        log.info('Importando invariante generado')

        # Importar el fichero de invariantes
        dirs = glob.glob(path.join(self.dir, 'daikon-out*'))
        log.debug(path.join(self.dir, 'daikon-out*'))
        dirs.sort()
        log.debug(dirs)
        if dir :
            src = os.path.join(dirs[-1], 'procesoInspeccionado.out')
            dst = os.path.join(self.invr_dir, 'invr-' + str(time.time()) + '.out')
            shutil.move(src, dst)

    ## @}

    ## @name Invariantes
    ## @{

    def inv_ultimo(self):
        """@brief Devuelve el último invariante
        @retval La ruta completa al último invariante o None.
        """
        invs = glob.glob(path.join(self.invr_dir, 'invr-*'))
        if invs :
            invs.sort()
            invs = invs[-1]
        else:
            return None

        return invs

    ## @}

    ## @name Cargar y Crear
    ## @{

    def crear(self):
        """@brief Crea el proyecto desde 0 por primera vez."""

        try:
            # Comprobar el nombre
            if len(str(self.nombre).strip()) == 0: 
                raise ProyectoError(_("idg.proyect.name.proyect.is.empty"))

            # Comprobar el bpel original
            if not path.exists(self.bpel_o):
                raise ProyectoError(_("idg.proyect.bpel.file.dont.exist") + self.bpel_o)

            # Crear el directorio nuevo en data
            # Copiar los ficheros básicos de skel
            log.info(_("idg.proyect.init.proyect"))
            try:
                shutil.copytree( path.join(self.share ,'skel') , self.dir )
            except:
                raise ProyectoError(_("idg.proyect.init.proyect.error.using") + \
                                    path.join(self.share,'skel'))

            # Buscar dependencias (y el bpel original modificándolo)
            # Si falla borramos el intento de proyecto 
            # y elevamos de nuevo la excepción
            try:
                log.info(_("idg.proyect.looking.for.dependences"))
                self.buscar_dependencias(self.bpel_o ) 
            except ProyectoError, error:                    
                log.error(_("idg.proyect.error.cant.import.dependences"))
                raise error

            # Imprimir directorios del proyecto
            log.info(_("idg.proyect.proyect.created.succesfully"))
            log.info(str(os.listdir(self.dir)))
            return True

        except:
            # Eliminar el intento de proyecto para que no queden antiguos
            # proyectos en un estado inconsistente.
            shutil.rmtree(self.dir)
            raise

    def check(self):
        """@brief Comprueba que el proyecto está bien y sus ficheros de
        configuración reflejan el estado del mismo. En otro caso trata de
        arreglarlo. Puede lanzar una excepción ProyectoError,
        ProyectoIrrecuperable y ProyectoRecuperable.""" 

        # Comprobar existencia de la estructura y de los
        # ficheros más importantes: proy,dir,text,bpel
        required = (self.dir, self.bpel, self.proy, self.build_path,
                    self.test_path, self.casos_dir, self.trazas_dir, self.invr_dir)

        for f in required:
            if not path.exists( f ):
                e =  _("idg.proyect.file.dont.exist") + f
                log.error(e)
                raise ProyectoIrrecuperable(e)

        # Write data to base-build file
        # takuan installation and analyzer flags
        log.info("Modificando fichero base-build.xml")
        bbuild = ANTFile(path.join(self.dir, 'base-build.xml'))
        flags = '--metrics --' + self.get_flattening()
        if self.simplify : flags += ' --simplify'
        bbuild.set('takuan', 'location', self.takuan)
        bbuild.set('analyzer.flags', 'value', flags)
        bbuild.save()

        try:
            # Abrir el test.bpts y comprobar la configuración del servidor 
            bpts = md.parse(self.test_path)
        except:
            raise ProyectoRecuperable(_("idg.proyect.cant.open.main.test.file"))

        # Buscar y establecer el nombre del proyecto
        bproot = bpts.getElementsByTagNameNS(self.test_url, 'testSuite')[0]
        bpname = bproot.getElementsByTagNameNS(self.test_url, 'name')[0]
        bpname.nodeValue = self.nombre

        # Buscar y establecer la dirección correctamente
        bpbaseURL = bproot.getElementsByTagNameNS(self.test_url, 'baseURL')[0]
        bpbaseURL.nodeValue = "http://%s:%s/ws" % (self.svr, self.port)

        # Guardarlo
        try:
            file = open(self.test_path, 'w')
            file.write(bpts.toxml('utf-8'))
        except:
            raise ProyectoRecuperable(_("idg.proyect.cant.write.main.test.file"))

        # Si hay dependencias rotas, avisar.
        if len(self.dep_miss) != 0:
            msg = _("idg.proyect.found.broken.dependences.fix.and.search.again")
            #self.idgui.estado(msg)
            #self.error(msg)
            log.warning(msg)
        else:
            # Instrumentar si hace falta
            if self.inst == False :
                self.instrumentar()

    def _load_bptsfiles(self):
        """@brief Load available test cases into cases dict.
        """
        # self.casos is a dict with the given form {'file' : ['case', ..]}
        ## Load BPTSFiles into proyect
        for bptsname in os.listdir(self.casos_dir):
            try:
                bpts = BPTSFile(path.join(self.casos_dir, bptsname))
                self.bptsfiles[bpts.name()] = bpts
            except:
                log.error(_("idg.proyect.cant.load.bpts.file") + bptsname)

        #log.debug(str([f.get_cases() for f in self.bptsfiles.values()]))

    def cargar_deps(self,dom):
        """@brief Carga las dependencias del proyecto leyendo el fichero de
        configuración."""

        root = dom.getroot()

        try:
            # dependencias
            deps = root.findall('.//dependencia')
            for d in deps:
                r = d.get('ruta')
                # Si no estaba la añadimos
                if r not in (self.deps + self.dep_miss):
                    self.deps.append(r) if d.get('rota') == 'False' \
                                        else self.dep_miss.append(r)

        except:
            raise ProyectoError(_("idg.proyect.error.in.config.file") + \
                                   self.proy + " " + str(sys.exc_value))

    def cargar_proy(self):
        """@brief Lee e inicializa la clase leyendo de los ficheros de
        configuración."""

        # Abrir self.proy para leer 
        # Si falla elevamos una excepción
        tree = et.ElementTree()
        try:
            root = tree.parse(self.proy)
        except:
            raise ProyectoError(_("idg.proyect.cant.open.config.file") + \
                                self.proy)

        # Trabajar con self.proy
        try:
            # Fechas de creación y modificación
            self.creado = root.get('creado')
            self.guardado = root.get('guardado')

            # Bpel Original
            e = root.find('bpel_o')
            self.bpel_o = e.get('src')
        except:
            raise ProyectoError(_("idg.proyect.error.in.config.file") + \
                                self.proy + " " + str(sys.exc_value))
        # Cargar Dependencias
        self.cargar_deps(tree)

    ## @}

    ## @name Guardar y Configurar
    ## @{

    def guardar_datos(self,dom):
        """@brief Guarda los datos propios del proyecto en el fichero de
        configuración.
        @param dom ElementTree del proyecto abierto.
        """

        root = dom.getroot()
        # Escribir info en self.proy
        try:
            # Fechas
            import datetime 
            now = datetime.datetime.now().isoformat(' ')

            # Fecha de modificación
            root.attrib['guardado'] =  now

            # Establecer la fecha de creación
            if root.get('creado') == "" :
                root.attrib['creado'] =  now

            # Modificación del nombre!  
            # Cuidado, la modificación del nombre puede hacerse desde la
            # realidad (self.nombre) hacia el proy.xml pero no al revés.  
            # El nombre del proyecto está en la ruta física del mismo y su cambio
            # implica el movimiento de directorios
            #if root.attrib['nombre'] != self.nombre:
            #    root.attrib['nombre'] = self.nombre

            # Server 
            #e = root.find('svr')
            #e.attrib['url'] =  self.svr
            #e.attrib['port'] =  self.port

            # bpel original
            #e = root.find('bpel_o')
            #e.attrib['src'] = self.bpel_o

            # bpel proyecto
            #e = root.find('bpel')
        except:
            raise ProyectoError(_("idg.proyect.cant.save.proyect.data"))

    def guardar_deps(self,dom):
        """@brief Guarda las dependencias en el fichero de configuración.
        @param dom ElementTree del proyecto abierto.
        """

        root = dom.getroot()
        try:
            # dependencias
            e = root.find('dependencias')
            echilds = e.getchildren()
            drutas = []

            # Quitar las que están en el xml pero no en el proyecto
            for d in echilds:
                ruta = d.get('ruta')
                if ruta not in self.deps + self.dep_miss:
                    e.remove(d)
                else:
                    drutas.append(ruta)

            # Comprobar las dependencias
            # Las que están en proyecto y no en el xml
            for d in self.deps + self.dep_miss:
                # Si no está, añadirlo
                if not d in drutas:
                    sub = et.SubElement(e,'dependencia')

                    # Añadir/Actualizar los atributos
                    sub.attrib['nombre'] =  path.basename(d)
                    sub.attrib['ruta'] =  d
                    sub.attrib['rota'] =  str(d in self.dep_miss)
        except:
            raise ProyectoError(_("idg.proyect.cant.save.dependences"))

    def guardar_casos(self, dom):
        """@brief Guarda los casos de prueba disponibles en el fichero de
        configuración.
        @param dom ElementTree del proyecto abierto.
        """

        root = dom.getroot()

        try: 
            # Casos de prueba
            e = root.find('testcases')

            # Quitar las antiguas
            # Eliminamos todas
            if e is not None :
                root.remove(e)

            # Lo creamos otra vez y añadimos los casos
            e = et.SubElement(root, 'cases')

            for name, bpts in self.bptsfiles.items():
                sub = et.SubElement(e, 'testfile')
                [et.SubElement(sub, 'testcase').set('name',str(c))\
                 for c in bpts.get_cases()]
        except:
            raise ProyectoError(_("idg.proyect.cant.save.testcases"))

    def guardar_trazas(self, dom):
        """@brief Guarda las trazas disponibles en el fichero de configuración.
        @param dom ElementTree del proyecto abierto.
        """

        root = dom.getroot()

        try:
            # Trazas
            e = root.find('traces')

            # Quitar las antiguas. Eliminamos todas.
            if e is not None :
                root.remove(e)

            # La creamos de nuevo y añadimos las trazas
            e = et.SubElement(root, 'traces')

            # traces[file][case] = [trace_file, trace_file ..]
            for file, cases in self.trazas_disponibles().items() :
                efile = et.SubElement(e, 'file')
                for case, tfiles in cases.items() :
                    ecase = et.SubElement(efile, 'case')
                    [et.SubElement(ecase, 'tracefile').set('name',n) for n in \
                     tfiles]
        finally:
            #raise ProyectoError(_("Error al guardar las trazas"))
            pass

    def guardar(self):
        """@brief Guarda todas las propiedades del proyecto en el fichero de
        configuración."""

        # Guarda las opciones
        self.opts.write()

        # Abrir self.proy para escribir la info del proyecto
        # Si falla elevamos una excepción
        tree = et.ElementTree()
        try:
            log.info(_("idg.proyect.writing.config.file") + self.proy)
            root = tree.parse(self.proy)
        except:
            err = _("idg.proyect.cant.open.config.file") 
            log.error(err)
            raise ProyectoError(err)

        # Guarda los datos, dependencias, casos y trazas 
        self.guardar_datos(tree)
        self.guardar_deps(tree)
        self.guardar_casos(tree)
        self.guardar_trazas(tree)

        try:
            tree.write(self.proy)
        except: 
            raise ProyectoError(_("idg.proyect.cant.write.config.file")\
                                + self.proy )

    def guardado(self):
        """@brief Comprueba si hay información modificada por guardar.
           \returns True si está todo guardado."""
        # Comprobar proyecto.xml
        # |- Comprobar casos
        # |- Comprobar trazas
        # |- Comprobar invariantes
        # `- Comprobar ejecuciones
        pass
        return self.mod

    def cerrar(self):
        """@brief Cierra el proyecto, realiza comprobaciones y lo guarda. """
        self.cancelar_ejecucion()
        self.guardar()

    ## @}
