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
    """@Brief Clase excepción para la clase Proyecto"""

    def __init__(self,msj):
        self.msj = msj

    def __str__(self):
        return str(self.msj)

class Proyecto(object):
    """@Brief Clase Proyecto con todas las operaciones sobre un proyecto
    idiginBPEL. Realiza la creación de un nuevo proyecto, la comprobación, el
    guardado y la eliminación así como todas las otras operaciones que tengan
    relación con un proyecto. """

    # Nombres de ficheros por defecto
    bpel_nom   =   'bpel_original.bpel'
    proy_nom   =   'proyecto.xml'
    build_nom  =   'build.xml'
    test_nom   =   'test.bpts'
    bpr_nom    =   'bpr_file.bpr'

    # Directorios
    casos_nom  =    'casos'
    trazas_nom =    'trazas'
    invr_nom   =    'invariantes'
    dep_nom    =    'dependencias'

    # Url de Namespaces 
    bpel_url = 'http://docs.oasis-open.org/wsbpel/2.0/process/executable'
    wsdl_url =   'http://schemas.xmlsoap.org/wsdl/'
    xsd_url  =   'http://www.w3.org/2001/XMLSchema'

    # Configuración de conexión por defecto
    svr    =   'localhost'
    port   =   '7777'

    # Flags de estado y propiedades
    inst   =   False # Instrumentado
    mod    =   False # Modificado


    def __init__(self,nombre,bpel=""):
        """@Brief Constructor de la clase proyecto.
           \nombre Nombre del proyecto
           \bpel Ruta original del bpel

        Establece los valores por defecto para las rutas del proyecto.
        Crea el proyecto si se le indica la ruta a un bpel
        Lee la configuración del proyecto ya creado si no
        Comprueba que el proyecto esté bien
        """
        # Valores por defecto de proyecto

        # Nombre y rutas absolutas
        self.nombre     =   nombre

        # Directorio de proyecto
        self.dir        =   path.join("data",nombre)
        self.dir        =   path.abspath( self.dir )
        
        # Rutas de Ficheros
        self.bpel   =   path.join( self.dir , self.bpel_nom  )
        self.proy   =   path.join( self.dir , self.proy_nom  )
        self.build  =   path.join( self.dir , self.build_nom )
        self.test   =   path.join( self.dir , self.test_nom  )
        self.bpr    =   path.join( self.dir , self.bpr_nom   )

        # Rutas Directorios
        self.casos_dir  =   path.join( self.dir , self.casos_nom  )
        self.trazas_dir =   path.join( self.dir , self.trazas_nom )
        self.invr_dir   =   path.join( self.dir , self.invr_nom   )
        self.dep_dir    =   path.join( self.dir , self.dep_nom   )

        # Dependencias
        self.dep = []
        # Dependencias no encontradas
        self.dep_miss = []

        # Si se indica la ruta del bpel, debemos crear el proyecto
        if self.bpel_o :
            # Bpel original
            self.bpel_o     =   path.abspath( bpel )
            self.crear()
        # En caso contrario, inicializamos el proyecto
        else:
            self.leer_config()

        # Comprueba que la estructura del proyecto está bien
        self.check()

        # Listas

        # Ficheros en directorio
        self.fichs  =   os.listdir( self.dir )
        # Casos de prueba (.bpts)
        self.fcasos =   os.listdir( self.casos_dir )
        # Trazas
        self.ftrazas=   os.listdir( self.trazas_dir )
        # Invariantes
        self.finvr  =   os.listdir( self.invr_dir )  

        # Comprueba y sincroniza la configuración del proyecto
        # con la realidad del sistema de ficheros
        self.check_cfg()

    def buscar_dependencias(self,bpel):
        """@Brief Busca las dependencias de un bpel recursivamente. 
           Copia el bpel y las dependencias al proyecto.
           Modifica el bpel y las dependencias para adaptarlos al proyecto
           \returns True si todo va bien, None si algo falla.
           Eleva excepciones ProyectoError.
        """

        # Comprobar el bpel externo
        if not path.exists( bpel ):
            print _("Error_no_pudo_abrir "), bpel
            raise ProyectoError( _("Error_no_pudo_abrir") + bpel)

        # Buscar las dependencias del bpel recursivamente
        self.deps = self.__buscar_dependencias([bpel])

        print "%i dependencias encontradas, %i dependencias rotas, %i \
        dependencias totales" % \
        (len(self.deps),len(self.dep_miss),len(self.dep_miss)+len(self.deps))

        return True

    def __buscar_dependencias(self,files,first=True):
        """@Brief Busca las dependencias xsd y wsdl recursivamente en los
        ficheros y devuelve sus rutas completas. 
        Copia las dependencias al proyecto y las modifica para adaptar los
        import a rutas relativas al proyecto. 
        Añade las dependencias que no han podido ser obtenidas a dep_miss.
        \param files Lista con rutas a los ficheros en los que buscar
        \param first Flag para saber si estamos mirando el bpel original.
        \returns Lista de rutas absolutas con las dependencias originales.
        """

        # Caso base files vacio
        if len(files) == 0 :
            return []
        else:
            # deps son las rutas encontradas
            deps = []

            # Buscamos en todos los ficheros que recibamos
            for f in files:
                # Nombre y directorio del fichero dependencia
                nom = path.basename(f)
                dir = path.dirname(f)

                # Si el fichero ya existe, no lo evaluamos
                if path.exists( path.join( self.dep_dir , nom) ):
                    continue

                print _("Dependencia: "), nom
                # Cargar fichero en memoria
                try:
                    xml = md.parse( f )
                except:
                    # Mostramos un error y añadimos 
                    # a las dependencias rotas
                    print _("Error al parsear "),f
                    self.dep_miss.append( f )
                    continue

                # Buscar los imports en el fichero
                # empleando los distintos namespaces
                imps = xml.getElementsByTagName('import')
                imps += xml.getElementsByTagName('xsd:import')

                # Modificar los import a rutas al mismo directorio
                # Obtener las rutas absolutas  meterlas en deps
                for i in imps:
                    attr = ""
                    if i.hasAttribute('location'):
                        attr = 'location'
                    elif i.hasAttribute('schemaLocation'):
                        attr = 'schemaLocation'

                    # Si no es ninguna de las dos, saltarlo
                    else:
                        continue

                    # Meter en deps la ruta absoluta 
                    # de la dependencia
                    ruta = i.getAttribute(attr)
                    dep = path.join(dir,ruta)
                    dep = path.abspath(dep)
                    deps.append(dep)

                    # Poner la ruta del import en el mismo directorio
                    # Si es el bpel original
                    if first:
                        i.setAttribute(attr, path.join( self.dep_nom , \
                                                       path.basename(ruta)))
                    # Si es una dependencia más, en el mismo directorio
                    else:
                        i.setAttribute(attr, path.basename(ruta))

                # Copiar las dependencias en proyecto
                try:
                    # Volcar el xml a un fichero en el directorio self.dep_dir
                    # Con el nombre adecuado si es el bpel original
                    if first :
                        file = open(self.bpel,'w')
                    else:
                        file = open(path.join(self.dep_dir,nom), 'w')
                    file.write(xml.toxml('utf-8'))
                except:
                    print _("Error al escribir en el proyecto"), nom
                    self.dep_miss.append(f)
                else:
                    # Eliminar de dep_miss dependencias 
                    # que finalmente si se han podido copiar
                    for d in deps:
                        if d in self.dep_miss:
                            self.dep_miss.remove(d)

            # Devolvemos las dependencias que ha recibido la función
            #  más las que encontraremos en la próxima vuelta.
            #  False en la llamada porque ya no es la primera.
            files.extend(self.__buscar_dependencias(deps, False))
            return files

    def crear(self):
        """@Brief Crea el proyecto. """

        if len(str(self.nombre).strip()) == 0: 
            raise ProyectoError(_("Nombre de proyecto vacio"))

        if not path.exists(self.bpel_o):
            raise ProyectoError(_("Fichero bpel no existe ") + self.bpel_o)

        # Crear el directorio nuevo en data
        # Copiar los ficheros básicos [ skel ]
        print _("Inicializando proyecto")
        try:
            shutil.copytree( 'base/skel' , self.dir )
        except:
            raise ProyectoError(_("Error al iniciar proyecto con base/skel"))

        # Inicializar el proyecto copiando skel

        # Copiar el bpel (y los wsdl y xsd que faltan)
        print _("Buscando dependencias")
        try:
            self.buscar_dependencias(self.bpel_o ) 
        except ProyectoError, error:                    
            # Borramos el intento de proyecto 
            shutil.rmtree(self.dir)
            print _("Crear Proyecto: Error al crear ficheros de proyecto")
            # Elevamos de nuevo la excepción
            raise error

        # Abrir self.proy para escribir la info del proyecto
        tree = et.ElementTree()
        try:
            print self.proy
            root = tree.parse(self.proy)
        except:
            print _("No se puede abrir el fichero de configuración del proyecto")
            raise ProyectoError(_("No se puede abrir el fichero de configuración \
                                 del proyecto"))

        # Escribir info en self.proy
        #try:
            # Nombre del proyecto 
        root.attrib['nombre'] = self.nombre
            # bpel original
        e = root.find('bpel_o')
        e.attrib['src'] = self.bpel_o
        #e.attrib['timestamp'] = path.getmtime(self.bpel_o)
             # bpel proyecto
        e = root.find('bpel')
        #e.attrib['timestamp'] = path.getmtime(self.bpel)
            # dependencias
        e = root.find('dependencias')

        for d in self.dep + self.dep_miss:
            print d
            sub = et.SubElement(e,'dependencia')
            sub.attrib['nombre'] = path.basename(d)
            sub.attrib['ruta'] = d
            sub.attrib['rota'] = d in self.dep_miss

        tree.write(self.proy)
            #except:
        print _("No se pudo escribir el fichero de configuración")
                #    raise ProyectoError(_("No se pudo escribir el fichero de configuración"))

        # Imprimir directorios del proyecto
        print _("Proyecto creado correctamente")
        print os.listdir(self.dir)
        return True

    def check(self):
        """@Brief Comprueba que el proyecto está bien y sus ficheros de
        configuración, de lo contrario lanza una excepción ProyectoError. """ 

        # Comprobar existencia de la estructura
        for f in ( self.dir, self.bpel, self.proy,
                self.build, self.test,
                self.casos_dir, self.trazas_dir,
                self.invr_dir ) : 

            if not path.exists( f ):
                print _("No existe el fichero "),f
             #raise f

        # Instrumentar
        self.instrumentar()

    def leer_config(self):
        """@Brief Lee e inicializa la clase leyendo de los ficheros de
        configuración."""


    def instrumentar(self):
        """@Brief Instrumenta el proyecto o lanza una excepción.""" 

        # Comprobamos si el bpel está instrumentado
        # También si ha cambiado desde la última
        # instrumentación
        if not path.exists( self.bpr ):
            self.inst = False
        else:
            bpr_time = path.getmtime( self.bpr )
            bpel_time = path.getmtime( self.bpel )
            self.inst = bpr_time < bpel_time

        # Si no está instrumentado, instrumentar
        if not self.inst:
            out = commands.getoutput('ant -f '+self.build+' build-bpr')
            if not path.exists( self.bpr ) or \
                    out.rfind('BUILD SUCCESSFUL') == -1 or \
                    out.rfind('BUILD FAILED') != -1 :

                raise ProyectoError(_("No se pudo instrumentar") + out )
        else:
            self.inst = True

    def guardar(self):
        """@Brief Guarda todas las propiedades del proyecto."""
        pass

    def guardado(self):
        """@Brief Comprueba si hay información modificada por guardar.
           \returns True si está todo guardado."""
        # Comprobar proyecto.xml
        # |- Comprobar casos
        # |- Comprobar trazas
        # |- Comprobar invariantes
        # `- Comprobar ejecuciones
        pass
        return self.mod

