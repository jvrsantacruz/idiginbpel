# Clase Proyecto
# -*- coding: utf-8 -*-

import os
import os.path as path
import commands 
import shutil 
import sys
from threading import Lock
from instrum import Instrumentador
from xml.dom import minidom as md
from xml.etree import ElementTree as et

import lang

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
    ## Directorio con las trazas generadas por la ejecución
    trazas_nom =    'trazas'
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
    ## Flag de si hay casos de prueba incluidos
    hay_casos = False
    # @}

    ## @name Inicialización 
    ## @{

    def __init__(self,nombre,idg,bpel=""):
        """@brief Constructor de la clase proyecto.
        Establece los valores por defecto para las rutas del proyecto.
        Crea el proyecto si se le indica la ruta a un bpel
        Lee la configuración del proyecto ya creado si no
        Comprueba que el proyecto esté bien
        @param nombre Nombre del proyecto a cargar/crear.
        @param idg Instancia de la clase de control .
        @param bpel Ruta al bpel original.
        """
        # Valores por defecto de proyecto

        ## Nombre del proyecto (se emplea en la ruta)
        self.nombre = nombre

        ## Instancia del control del proyecto
        self.idg = idg

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
            self.idg.obtener_lista_proyectos()

        # Proyecto instrumentado o no
        self.inst = path.exists(self.bpr)

        # Comprueba que la estructura del proyecto está bien
        try:
            self.check()
        except (ProyectoRecuperable) as e:
            print _("El proyecto se ha creado con errores: " + str(e))

        ## @name Listas
        ## @{

        ## Lista con los ficheros en el proyecto
        self.fichs  =   os.listdir( self.dir )
        ## Lista con los ficheros de casos de prueba (.bpts)
        self.fcasos =   os.listdir( self.casos_dir )
        ## Lista con los ficheros de las trazas
        self.ftrazas=   os.listdir( self.trazas_dir )
        ## Lista con los ficheros de invariantes
        self.finvr  =   os.listdir( self.invr_dir )  
        ## @}

        # Número de casos
        self.hay_casos = len(self.casos) > 0

    def _set_vars(self):
        """@brief Establece las variables internas del objeto"""

        
        # Urls generales de proyecto
        self.home       =   self.idg.home
        self.share      =   self.idg.share
        self.takuan     =   self.idg.takuan

        ## Directorio del proyecto
        self.dir        =   path.join(self.home,'proy',self.nombre) 
        self.dir        =   path.abspath( self.dir )

        ## @name Rutas de Ficheros 
        ## @{

        ## Ruta al bpel importado, se emplea para ejecutar etc...
        self.bpel   =   path.join(self.dir, self.bpel_nom)  # bpel
        ## Ruta al fichero de configuración  del proyecto.
        self.proy   =   path.join(self.dir, self.proy_nom)  # config proy
        ## Ruta al fichero ant para realizar las ejecuciones.
        self.build  =   path.join(self.dir, self.build_nom) # ant proy
        ## Ruta al fichero bpts que contiene los casos de prueba.
        self.test   =   path.join(self.dir, self.test_nom)  # test.bpts
        ## Ruta al fichero bpr que se genera en la instrumentación.
        self.bpr    =   path.join(self.dir, self.bpr_nom)   # instrument
        ## @}

        ## @name Rutas Directorios 
        ## @{

        ## Ruta al directorio que contiene los casos de prueba
        self.casos_dir  =   path.join(self.dir, self.casos_nom ) # Casos
        ## Ruta al directorio que contiene las trazas
        self.trazas_dir =   path.join(self.dir, self.trazas_nom) # Trazas
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
        ## Lista con los casos de prueba disponibles "fichero:nom_caso"
        self.casos = {}
        ## @}

        ## @name Threading
        ## @{

        ## Lock del instrumentador
        self.inst_lock = Lock()
        ## Thread instrumentador
        self.inst_thread = None
        ## @}

    ## @}

    ## @name Tratar Bpel
    ## @{

    def buscar_dependencias(self,bpel):
        """@brief Busca las dependencias de un bpel recursivamente. 
           Copia el bpel y las dependencias al proyecto.
           Modifica el bpel y las dependencias para adaptarlos al proyecto
           \returns True si todo va bien, None si algo falla.
           Eleva excepciones ProyectoError.
        """

        # Comprobar el bpel que nos pasan
        if not path.exists( bpel ):
            print _("Error no se pudo abrir ") + bpel
            raise ProyectoError( _("Error no se pudo abrir ") + bpel)

        # Buscar las dependencias del bpel recursivamente
        ## Lista de rutas con las dependencias del bpel
        self.deps, self.dep_miss = self.__buscar_dependencias([bpel])

        print "%i dependencias encontradas, %i dependencias rotas, %i \
        dependencias totales" % \
        (len(self.deps),len(self.dep_miss),len(self.dep_miss)+len(self.deps))

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

            print _("Dependencia: "), nom

            # Abrimos el fichero, obtenemos uss imports, modificamos las rutas 
            # y lo serializamos de nuevo pero dentro del proyecto.

            # Cargar fichero en memoria
            try:
                xml = md.parse( f )
            except:
                # Mostramos un error y añadimos 
                # a las dependencias rotas
                print _("Error al parsear "),f
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
                # Si no está el atributo por alguna razón, continuar.
                ruta = i.getAttribute(attr) 
                if not ruta:
                    continue

                # Ruta real de la dependencia encontrada
                dep = path.abspath(path.join(dir, ruta))

                # Añadir la dependencia al conjunto local y total
                local_deps.add(dep)
                deps.add(dep)

                print nom , " --> " , path.basename(ruta)

                # Si es el bpel original (first) la dependencia apuntará al
                # directorio de dependencias (self.dep_nom)
                # Si es una dependencia más, sus imports estarán en el
                # mismo directorio.
                ruta = path.basename(ruta) if not first else  \
                        path.join(self.dep_nom, path.basename(ruta))

                # Modificar el atributo con la ruta correcta
                i.setAttribute(attr, ruta)


            # Copiar el fichero en el proyecto
            try:
                # Serializar el xml a un fichero en el directorio self.dep_dir
                # Con el nombre adecuado si es el bpel original
                if first :
                    file = open(self.bpel,'w')
                else:
                    file = open(path.join(self.dep_dir,nom), 'w')

                file.write(xml.toxml('utf-8'))
            except:
                # Si no se ha podido escribir la versión modificada del
                # fichero, añadirlo a las dependencias rotas 
                print _("Error al escribir en el proyecto"), nom
                miss.add(ruta)
            finally:
                file.close()

                # Quitamos de deps las que están en miss
                # deps = deps.difference_update(miss)

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

    def instrumentar(self):
        """@brief Instrumenta el proyecto o lanza una excepción.""" 
        # No queremos dos thread para hacer lo mismo
        if self.inst_thread is None or not self.inst_thread.isAlive():
            self.inst = False
            # Comenzar la instrumentación
            self.inst_thread = Instrumentador(self)
            self.inst_thread.start()
            self.inst = True

    ## @}

    ## @name Casos de prueba
    ## @{

    def add_bpts(self,ruta):
        """@brief Añade un fichero con casos de prueba al proyecto.
        @param ruta Ruta al fichero .bpts.
        El primer bpts que se añade es el que nos proporcionará la información
        referida al <put>.
        Eleva ProyectoRecuperable en caso de error."""

        # Comprobamos que exista y se pueda leer
        if not path.exists(ruta) or not os.access(ruta, os.F_OK or os.R_OK):
            raise ProyectoRecuperable(_("No existe el fichero de casos de prueba o no es accesible"))

        # Nombre del fichero y directorio de la ruta
        nom = path.basename(ruta)
        dir = path.dirname(ruta)

        # Lo copiamos al proyecto en casos_dir
        # Aseguramos el nombre para no sobreescribir
        i = 1
        pnom = nom
        pruta = path.join(self.casos_dir,pnom)

        while path.exists(pruta):
            pnom = "%s-%d" % (nom,i)
            pruta = path.join(self.casos_dir,pnom)
            i = i + 1
            print pruta

        try:
            # Copiar de ruta a pruta (en el proyecto)
            shutil.copy(ruta,pruta)
        except:
            raise ProyectoRecuperable(_("No se pudo copiar al proyecto el\
                                        fichero de casos de prueba: ") + ruta)
        # Añadimos el fichero a fcasos
        self.fcasos.append(pnom)

        # Lo parseamos con ElementTree
        # Abrirlo
        try:
            bpts = et.ElementTree()
            bproot = bpts.parse(pruta)
        except:
            raise ProyectoRecuperable(_("No se ha podido cargar el fichero de casos de prueba"))

        # Construir los nombres con la uri es un peñazo
        ns = "{%s}" % self.test_url

        # Encontramos elementos básicos
        testSuite = bproot
        tCases = bproot.find(ns + 'testCases')

        # Buscamos todos los casos de prueba y los añadimos a self.casos
        self.casos[pnom] = [c.get('name') for c in tCases.findall(ns + 'testCase')]

        # Escribir los casos de prueba en el proy
        self.sinc_casos()

        # Actualizamos la información de test.bpts con la del proyecto
        self.add_bpts_info(bpts)

    def add_bpts_info(self,bpts):
        """@brief Añade al bpts general del proyecto la información necesaria
        para la ejecución. Esto sucede la primera vez que se añade un bpts.
        @param bpts ElementTree con el bpts parseado."""

        # Namespace
        ns = "{%s}" % self.test_url
        # Raiz del bpts
        bproot = bpts.getroot()

        # Encontramos el put con el wsdl,el property y los partners en el .bpts
        deploy = bproot.find(ns + 'deployment')
        partners = deploy.findall(ns + 'partner') 
        put = deploy.find(ns + 'put')
        wsdl = put.find(ns + 'wsdl')  

        # Abrimos el fichero general .bpts de casos de prueba
        try:
            test = et.ElementTree()
            troot = test.parse(self.test)
        except:
            ProyectoRecuperable(_("No se ha podido cargar el fichero de \
            tests") + self.test )

        # Buscamos el put con el wsdl
        tdeploy = troot.find(ns + 'deployment')
        tput = tdeploy.find(ns + 'put')
        twsdl = tput.find(ns + 'wsdl')

        # Copiar el wsdl y los partner
        # Hay que añadirles el dependencias/ para la ruta.
        twsdl.text = path.join(self.dep_nom, wsdl.text)
        for p in partners:
            sub = et.SubElement(tdeploy, ns + 'partner')
            sub.attrib['name'] =  p.attrib['name']
            sub.attrib['wsdl'] = path.join(self.dep_nom, p.attrib['wsdl'])

        try:
            test.write(self.test)
        except:
            ProyectoRecuperable(_("No se ha podido escribir el fichero de \
            tests") + self.test)

        self.hay_casos = True

    ## @}

    ## @name Cargar y Crear
    ## @{

    def crear(self):
        """@brief Crea el proyecto. """

        # Comprobar el nombre
        if len(str(self.nombre).strip()) == 0: 
            raise ProyectoError(_("Nombre de proyecto vacio"))

        # Comprobar el bpel original
        if not path.exists(self.bpel_o):
            raise ProyectoError(_("Fichero bpel no existe ") + self.bpel_o)

        # Crear el directorio nuevo en data
        # Copiar los ficheros básicos de skel
        print _("Inicializando proyecto")
        try:
            shutil.copytree( path.join(self.share ,'skel') , self.dir )
        except:
            raise ProyectoError(_("Error al iniciar proyecto con: ") + \
                                path.join(self.share,'skel'))

        # Buscar dependencias (y el bpel original modificándolo)
        # Si falla borramos el intento de proyecto 
        # y elevamos de nuevo la excepción
        try:
            print _("Buscando dependencias")
            self.buscar_dependencias(self.bpel_o ) 
        except ProyectoError, error:                    
            shutil.rmtree(self.dir)
            print _("Crear Proyecto: Error al crear ficheros de proyecto")
            raise error

        # Imprimir directorios del proyecto
        print _("Proyecto creado correctamente")
        print os.listdir(self.dir)
        return True

    def check(self):
        """@brief Comprueba que el proyecto está bien y sus ficheros de
        configuración reflejan el estado del mismo. En otro caso trata de
        arreglarlo. Puede lanzar una excepción ProyectoError,
        ProyectoIrrecuperable y ProyectoRecuperable.""" 

        # Comprobar existencia de la estructura y de los
        # ficheros más importantes: proy,dir,text,bpel
        required = (self.dir, self.bpel, self.proy, self.build,
                    self.test, self.casos_dir, self.trazas_dir, self.invr_dir)

        for f in required:
            if not path.exists( f ):
                e =  _("No existe el fichero: ") + f
                print e
                raise ProyectoIrrecuperable(e)

        # Comprobar y escribir en base-build la ruta base a la instalación de takuan si es
        # incorrecta.
        try:
            bbuild =  et.ElementTree()
            root = bbuild.parse(path.join(self.dir,'base-build.xml'))
        except:
            raise ProyectoRecuperable(_("No se pudo abrir el fichero base-build.xml"))

        # Buscar el atributo y comprobarlo
        # dnms = root.find("./property[@name='takuan']")
        dnms = bbuild.findall('property')
        dnms = [d for d in dnms if 'name' in d.attrib and d.get('name') == 'takuan']

        # Si es distinto del que tenemos en memoria, modificarlo.
        if dnms[0].get('location') != self.takuan:
            if len(dnms) == 0 :
                print _("No se ha podido configurar base-build.xml")
            else:
                print _("Modificando fichero base-build.xml")
                dnms[0].attrib['location'] =  self.takuan

            try:
                bbuild.write(path.join(self.dir,'base-build.xml'))
            except:
                raise ProyectoError(_("No se pudo escribir el fichero base-build.xml"))

        # Abrir el test.bpts y comprobar la configuración del servidor 
        try:
            bpts = et.ElementTree()
            bproot = bpts.parse(self.test)
        except:
            raise ProyectoRecuperable(_("No se pudo abrir el fichero de casos\
            de prueba general"))
        # Buscar y establecer el nombre del proyecto
        ns = "{%s}" % self.test_url
        bpname = bproot.find(ns + 'name')
        bpname.text = self.nombre

        # Buscar y establecer la dirección correctamente
        bpbaseURL = bproot.find(ns + 'baseURL')
        bpbaseURL.text = "http://%s:%s/ws" % (self.svr, self.port)

        # Guardarlo
        try:
            bpts.write(self.test)
        except:
            raise ProyectoRecuperable(_("No se pudo escribir el fichero de \
                                        casos de prueba"))

        # Si hay dependencias rotas, avisar.
        if len(self.dep_miss) != 0:
            msg = _("Hay dependencias rotas en el proyecto, solucione la \
            situación y realice una búsqueda o cree de nuevo el proyecto")
            #self.idgui.estado(msg)
            #self.error(msg)
            print msg
        else:
            # Instrumentar si hace falta
            if self.inst == False :
                self.instrumentar()

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
            raise ProyectoError(_("Error en el fichero de configuración: ") + \
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
            raise ProyectoError(_("No se puede abrir el fichero de \
            configuración del proyecto: ") + self.proy)

        # Trabajar con self.proy
        try:
            # fechas
            self.creado = root.get('creado')
            self.guardado = root.get('guardado')

            # bpel_o 
            e = root.find('bpel_o')
            self.bpel_o = e.get('src')

            # svr
            e = root.find('svr')
            self.svr = e.get('url')
            self.port = e.get('port')

            # Dependencias
            self.cargar_deps(tree)
            
            # Sincroniza casos de prueba
            self.sinc_casos(tree)

        except:
            raise ProyectoError(_("Error en el fichero de configuración: ") + \
                                self.proy + " " + str(sys.exc_value))
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
            e = root.find('svr')
            e.attrib['url'] =  self.svr
            e.attrib['port'] =  self.port

            # bpel original
            e = root.find('bpel_o')
            e.attrib['src'] = self.bpel_o

            # bpel proyecto
            e = root.find('bpel')
        except:
            raise ProyectoError(_("Error al guardar los datos del proyecto."))

    def guardar_deps(self,dom):
        """@brief Guarda las dependencias en el fichero de configuración.
        @param dom ElementTree del proyecto abierto."""

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
            raise ProyectoError(_("Error al guardar las dependencias"))

    def guardar(self):
        """@brief Guarda todas las propiedades del proyecto en el fichero de
        configuración."""

        # Abrir self.proy para escribir la info del proyecto
        # Si falla elevamos una excepción
        tree = et.ElementTree()
        try:
            print _("Escribiendo fichero de configuración : "), self.proy
            root = tree.parse(self.proy)
        except:
            err = _("No se puede abrir el fichero de configuración \
                                 del proyecto") 
            print err
            raise ProyectoError(err)

        # Guarda los datos generales
        self.guardar_datos(tree)
        # Guarda las dependencias
        self.guardar_deps(tree)
        # Sincroniza los casos de prueba
        self.sinc_casos(tree)

        try:
            tree.write(self.proy)
        except: 
            raise ProyectoError(_("No se pudo escribir el fichero de \
                                       configuración en: ") + self.proy )

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

    def sinc_casos(self,tree=None):
        """@brief Actualiza la información de los casos de prueba a partir de
        proyecto.xml. Añade al xml los que no estén. 
        @param (Opcional) El dom ElementTree de proy.xml abierto
        """

        itree = tree
        if itree is None:
            # Si no se pasa ya abierto, abrir proy
            try:
                itree = et.ElementTree()
                itree.parse(self.proy)
            except:
                raise ProyectoRecuperable(_("Error al abrir proyecto.xml"))

        # self.casos es un diccionario del tipo 'fichero' : ['caso', 'caso']
        # No se pueden emplear expresiones xpath tan molonas como las
        # siguientes debido a que se añadirán a ElementTree en la versión 1.3. 
        # La versión actual de Python 2.6 trae ElementTree 1.2.6
        #fnode = proot.find("./fprueba[@nombre='%s']" % f) 
        #cnode = fnode.find("./prueba[@nombre='%s']" % c)
        root = itree.getroot()
        proot = root.find('pruebas')
        fpruebas = proot.getchildren()
        nuevos = False

        # Ahora añadir al xml los que están 
        # en el proyecto y no en el xml
        for f in self.casos:
            # Buscarlo entre los nodos prueba
            try:
                fnode = [fp for fp in fpruebas if fp.get('nombre') == f][0]
            except:
                fnode = et.SubElement(proot, 'fprueba')
                fnode.attrib['nombre'] =  f
                nuevos = True

            fchild = fnode.getchildren()
            # Buscamos sus casos
            for c in self.casos[f]:
                # Buscarlo entre los casos de f
                try:
                    cnode = [fc for fc in fchild if fc.get('nombre') == c][0]
                except:
                    cnode = et.SubElement(fnode, 'prueba')
                    cnode.attrib['nombre'] =  c
                    nuevos = True
            # Número de casos que tiene el fichero
            fnode.attrib['ncasos'] = str(len(self.casos[f]))

        # Añadir al proyecto los que solo están en el xml 
        fpruebas = proot.getchildren()
        for f in fpruebas:
            fnom = f.get('nombre')
            casos = f.getchildren()
            if fnom not in self.casos:
                self.casos[fnom] = []
            for c in casos:
                cnom = c.get('nombre')
                if cnom not in self.casos[fnom]:
                    self.casos[fnom].append(cnom)

        # Comprobar ficheros de casos
        # Miramos los que tenemos cargados y comprobamos que exista el fichero.
        casos = self.casos.keys()
        for f in casos :
            fpath = path.join(self.casos_dir, f)
            print "Comprobando fichero %s" % fpath
            if path.exists(fpath) :
                   print "%s existe " % fpath
            else :
                   print "%s no existe " % fpath
                   # Eliminarlo de casos
                   del self.casos[f]

        # Escribir solo si es necesario
        # y si no se nos ha pasado el dom abierto
        if nuevos and not tree is None:
            try:
                tree.write(self.proy)
            except:
                raise

        print self.casos
    ## @}
