# Clase Proyecto
# -*- coding: utf-8 -*-

import os
import os.path as path
import commands 
import shutil 

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
    wsdl_url =   'http://schemas.xmlsoap.org/wsdl/'
    xsd_url  =   'http://www.w3.org/2001/XMLSchema'
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
            self.leer_config()
        else:
            self.crear()
            self.guardar()

        # Comprueba que la estructura del proyecto está bien
        self.check()

        # Listados

        ## Lista con los ficheros en el proyecto
        self.fichs  =   os.listdir( self.dir )
        ## Lista con los ficheros de casos de prueba (.bpts)
        self.fcasos =   os.listdir( self.casos_dir )
        ## Lista con los ficheros de las trazas
        self.ftrazas=   os.listdir( self.trazas_dir )
        ## Lista con los ficheros de invariantes
        self.finvr  =   os.listdir( self.invr_dir )  

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
        ## Lista con las rutas de las dependencias del bpel
        self.deps = []
        ## Lista con las rutas de las dependencias no encontradas del bpel
        self.dep_miss = []
        # Proyecto instrumentado o no
        self.inst = path.exists(self.bpr)
        ## @}
#
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

        # Comprobar el bpel externo
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

        # Caso de parada de la función
        if len(files) == 0 :
            return []

        local_deps = set()

        # Buscamos en todas las rutas de ficheros que recibamos
        for f in files:

            # Si es la primera vez, añadimos a deps
            if first:
                deps.add(f)

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
            imps = xml.getElementsByTagName('import')
            imps += xml.getElementsByTagName('xsd:import')

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

        # Comenzar la instrumentación mandando a consola el comando
        cmd = "ant -f %s build-bpr" % self.build
        print _("Ejecutando: ") + cmd
        out = commands.getoutput(cmd)

        # Comprobar que se ha instrumentado correctamente
        if not path.exists( self.bpr ) or \
           out.rfind('BUILD SUCCESSFUL') == -1 :
            # Si ha sido por la falta de un fichero, volvemos a buscar
            # dependencias e intentamos instrumentar de nuevo.
            if( not self.inst is None  
               and out.rfind('java.io.FileNotFoundException') != -1):
                self.inst = None
                bpel = self.bpel_o if path.exists(self.bpel_o) else self.bpel
                self.buscar_dependencias(bpel)
                self.instrumentar()
            else:
                self.inst = False
                raise ProyectoRecuperable(_("No se pudo instrumentar") + out )
        else:
            self.inst = True
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
        configuración y trata de arreglarlo, de lo contrario lanza una excepción ProyectoError. """ 

        # Comprobar existencia de la estructura y de los
        # ficheros más importantes: proy,dir,text,bpel
        required = (self.dir, self.bpel, self.proy, self.build,
                    self.test, self.casos_dir, self.trazas_dir, self.invr_dir)

        for f in required:
            if not path.exists( f ):
                e =  _("No existe el fichero: ") + f
                print e
                raise ProyectoError(e)

        # Comprobar y escribir en base-build la ruta base a la instalación de takuan si es
        # incorrecta.

        # Abrir base-build.xml
        try:
            bbuild =  et.ElementTree()
        except:
            raise ProyectoError(_("No se pudo abrir el fichero base-build.xml"))

        # Buscar el atributo y comprobarlo
        root = bbuild.parse(path.join(self.dir,'base-build.xml'))
        dnms = bbuild.findall('property')
        dnms = [d for d in dnms if 'name' in d.attrib and d.attrib['name'] == 'takuan']

        # Si es distinto del que tenemos en memoria, modificarlo.
        if dnms[0].attrib['location'] != self.takuan:
            if len(dnms) == 0 :
                print _("No se ha podido configurar base-build.xml")
            else:
                print _("Modificando fichero base-build.xml")
                dnms[0].attrib['location'] = self.takuan

            try:
                bbuild.write(path.join(self.dir,'base-build.xml'))
            except:
                raise ProyectoError(_("No se pudo escribir el fichero base-build.xml"))

        # Instrumentar
        if not self.inst :
            self.instrumentar()

    def leer_config(self):
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
            self.bpel_o = e.attrib['src']

            # svr
            e = root.find('svr')
            self.svr = e.attrib['url']
            self.port = e.attrib['port']

            # dependencias
            e = root.find('dependencias')
            echilds = e.getchildren()

            # Añadir las dependencias donde correspondan
            for d in echilds:
                ruta = d.attrib['ruta']
                if d.attrib['rota'] == 'False':
                    self.deps.append(ruta)
                else:
                    self.dep_miss.append(ruta)

            # pruebas
            # ...
        except:
            raise ProyectoError(_("Error en el fichero de configuración: ") + \
                                self.proy)
    ## @}

    ## @name Guardar
    ## @{

    def guardar(self):
        """@brief Guarda todas las propiedades del proyecto en el fichero de
        configuración."""

        # Abrir self.proy para escribir la info del proyecto
        # Si falla elevamos una excepción
        tree = et.ElementTree()
        try:
            print _("Leyendo fichero de configuración : "), self.proy
            root = tree.parse(self.proy)
        except:
            err = _("No se puede abrir el fichero de configuración \
                                 del proyecto") 
            print err
            raise ProyectoError(err)

        # Escribir info en self.proy
        try:
            # Fechas
            import datetime 
            now = datetime.datetime.now().isoformat(' ')

            # Fecha de modificación
            root.attrib['guardado'] = now

            # Establecer la fecha de creación
            if root.attrib['creado'] == "" :
                root.attrib['creado'] = now

            # Modificación del nombre!  
            # Cuidado, la modificación del nombre puede hacerse desde la
            # realidad (self.nombre) hacia el proy.xml pero no al revés.  
            # El nombre del proyecto está en la ruta física del mismo y su cambio
            # implica el movimiento de directorios
            #if root.attrib['nombre'] != self.nombre:
            #    root.attrib['nombre'] = self.nombre

            # Server 
            e = root.find('svr')
            e.attrib['url'] = self.svr
            e.attrib['port'] = self.port

            # bpel original
            e = root.find('bpel_o')
            e.attrib['src'] = self.bpel_o

            # bpel proyecto
            e = root.find('bpel')

            # dependencias
            e = root.find('dependencias')
            echilds = e.getchildren()
            dnames = [d.attrib['nombre'] for d in echilds]

            # Comprobar las dependencias
            for d in self.deps + self.dep_miss:
                # Si no está, añadirlo
                if not d in dnames:
                    sub = et.SubElement(e,'dependencia')

                # Añadir/Actualizar los atributos
                sub.attrib['nombre'] = path.basename(d)
                sub.attrib['ruta'] = d
                sub.attrib['rota'] = str(d in self.dep_miss)
        except:
            raise ProyectoError(_("Error al configurar"))

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

    ## @}
