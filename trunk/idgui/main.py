# Clase de Interfaz de usuario
# -*- coding: utf-8 -*-

import os
import os.path as path
import sys
import traceback

import pygtk
pygtk.require("2.0")
import gtk
import gobject
import webkit

import util.logger
log = util.logger.getlog('idgui.main')

from proyecto import ProyectoUI
from opciones import OptUI

class Idgui(object):
    """@brief Objeto principal de la gui."""

    ## @name Inicialización
    ## @{

    def __init__(self,idg):
        """
           @brief Inicializa la GUI de IndigBPEL
           @param idg Instancia de Idg
        """
        ## Instancia de gtkbuilder
        self.builder = gtk.Builder()
        ## Instancia de la clase idg
        self.idg = idg
        ## Instancia del proyectoUI
        self.proyecto = None

        # Thread safe
        gobject.threads_init()
        gtk.gdk.threads_init()

        ## Opciones de la configuración
        self.opt = idg.opt

        ### Ventana principal
        self.builder.add_from_file(path.join(self.idg.share,"ui/main.glade"))
        ## Objeto ventana
        self.main_ventana = self.builder.get_object("main_ventana")
        ## Contenedor Principal
        self.principal = self.builder.get_object("principal")
        ## Barra de estado
        self.barra_estado = self.builder.get_object("main_estado")

        # Cargar portada en principal

        # Cargar el glade de la portada
        self.builder.add_from_file(path.join(self.idg.share,"ui/portada.glade"))
        ## Portada de la aplicación con el dibujo de bienvenida
        self.web = webkit.WebView()
        #self.html.load_html_string("<p>HoHoHo</p>", "file:///")
        self.portada = self.builder.get_object("portada")
        self.cargar_portada()

        # Ruta por defecto para abrir los selectores de fichero
        self.last_path = ""

        # Cargar la lista de proyectos
        self.__init_lista_proyectos()

        # Conectar señales 
        self.builder.connect_signals(self)

        # Mostrar la ventana
        self.main_ventana.show()

        # Bucle principal
        gtk.main()

    def __init_lista_proyectos(self):
        """@brief Inicializa la gui de la lista de proyectos."""
        ## Modelo ListStore con la lista de proyectos
        self.modelo_lista_proyectos = \
        self.builder.get_object("main_lista_proyectos")

        ## Vista ListStore para la lista de proyectos
        self.vista_lista_proyectos = self.builder.get_object("main_lista_proyectos_vista");

        # Actualizar la lista de proyectos
        self.listar_proyectos()

    def __init_pantalla_nuevo_proyecto(self):
        """@brief Inicializa la gui de la pantalla de nuevo proyecto."""
        # Cargar glade de pantalla de nuevo proyecto
        self.builder.add_from_file(path.join(self.idg.share,"ui/nuevo_proyecto.glade"))

        # Filtro para el selector de ficheros
        filtro_fichero_bpel = self.builder.get_object("proyecto_filtro_fichero_bpel").add_pattern("*.bpel")

    ## @}

    ## @name Actualizar
    ## @{

    def listar_proyectos(self, widget=None):
        """ 
            @brief Lista los proyectos disponibles en la barra principal.
            @param widget El widget desde donde se llama a esta función.
        """

        # Limpiar lista actual
        self.modelo_lista_proyectos.clear()

        # Introducir los datos en el ListStore obtenidos de idg
        for p in self.idg.lista_proyectos :
            if p not in self.modelo_lista_proyectos:
                self.modelo_lista_proyectos.append( [p] )

    def cargar_proyecto(self,nombre,bpel=""):
        """ 
            @brief Oculta todo lo que hay en el contenedor principal de la
            aplicación  y carga un proyecto creando una instancia de
            ProyectoUI.
            @param nombre Nombre del proyecto a cargar
            @param bpel (Opcional) La ruta del bpel si es para crear el
            proyecto por primera vez.
        """
        # Ocultar lo que hay en principal ahora mismo
        children = self.principal.get_children()
        for child in children:
            child.hide()


        # Comprobar que el proyecto actualmente cargado, si lo hay, 
        #  no es el mismo que pretendemos cargar.
        if not self.idg.proyecto is None \
           and self.idg.proyecto.nombre == nombre :
            log.info(_("Proyecto ya cargado, no se vuelve a cargar."))
            # Mostrarlo en la interfaz
            self.proyecto.proyecto_base.reparent(self.proyecto.principal)
            self.proyecto.proyecto_base.show()
            return False

        # Crear el proyecto UI
        try:
            ## Referencia a la instancia de ProyectoUI abierta en el momento
            self.proyecto = ProyectoUI(self.idg,self,nombre,bpel)
        except:
            log.error("Crear Proyecto %s: %s" % sys.exc_info()[:2])
            log.error("%s" % traceback.print_exc())
            self.estado("Error al cargar el proyecto")
            self.cargar_portada()

    def estado(self,msg,dsc=""):
        """@brief Añadir estado a la barra de estado de la aplicación.
        @param msg Mensaje a añadir.
        @param dsc Descripción del mensaje en la statusbar."""
        id = self.barra_estado.get_context_id(dsc)
        self.barra_estado.push(id,str(msg))

    ## @}

    ## @name Callbacks 
    ## @{

    def on_lista_proyectos_cursor_changed(self, treeview):
        """
            @brief Callback de seleccionar un proyecto de la lista de
            proyectos. Toma el nombre de la interfaz y carga el proyecto.
            @param treeview El widget treeview con la lista de proyectos
        """

        # Obtener la selección
        model, sel = treeview.get_selection().get_selected()
        nombre = model.get_value(sel,0)
        log.info(_("Seleccionado el proyecto: ") + nombre)

        # Si hay otro ya abierto, cerrarlo
        if self.proyecto is not None :
            self.proyecto.cerrar()

        # Cargar el proyecto en la gui
        self.cargar_proyecto(nombre)

    def crear_proyecto(self,widget):
        """
            @brief Callback de presionar el botón Crear, en Nuevo Proyecto. 
            Toma los datos del proyecto desde la interfaz y crea una
            instancia de ProyectoUI. Muestra los errores en la interfaz si
            fuese el caso.

            @param widget El botón que se pulsó.
            """

        # Obtenemos el nombre que el usuario ha escrito y lo limpiamos.
        nombre = self.builder.get_object("proyecto_nombre").get_text().strip()

        # Obtenemos la ruta del bpel.
        file_chooser = self.builder.get_object("proyecto_selector_bpel")
        # Poner como ruta la última usada
        if self.last_path :
            file_chooser.set_current_folder(self.last_path)
        bpel = file_chooser.get_filename()
        self.last_path = path.dirname(bpel)

        # Cadena con los errores
        error_str = ""

         # Comprobar nombre del proyecto
        # No debe estar vacio
        if not nombre:
            error_str =  _("El nombre del proyecto no puede estar vacío.") 

        # No debe estar usado
        elif nombre in self.idg.lista_proyectos:
            error_str =  _("Ya existe un proyecto con ese nombre.") 

         # Debe ser un nombre 'unix' válido
        else:
            # Caracteres que no deben estar en el nombre del proyecto
            wrong = "|:,!@#$()/\\\"'`~{}[]=+&^ \t"
            for i in wrong:
                if nombre.find(i) != -1 :
                    error_str = _("El nombre del proyecto no puede contener el carácter: ") + '"%c"' % i
                    break

        # La ruta debe estar seleccionada
        if bpel is None:
            error_str = _("Fichero bpel no seleccionado") 
        elif not os.access(bpel, os.F_OK or os.R_OK or os.W_OK):
            error_str = _("El fichero bpel seleccionado no existe")

        # Comprobar los errores y mostrarlos
        if error_str :
            self.errores_label.set_text(error_str)
            return error_str

        log.info(_("Creando proyecto con el fichero bpel: ") + bpel)

        # Creamos el proyecto
        # False si todo va bien
        try:
            self.cargar_proyecto(nombre,bpel)
        except:
            log.error(_("Excepción al crear proyecto "))
            #errores.set_text(e)

        # Si el proyecto ha sido creado correctamente
        # Actualizar la lista de proyectos 
        self.listar_proyectos()

        return True

    def nuevo_proyecto(self, widget):
        """
            @brief Callback de presionar el botón de Nuevo Proyecto
                    carga la pantalla de crear un nuevo proyecto.
            @param widget El botón que se pulsó.
        """

        self.nuevo = True
        self.__init_pantalla_nuevo_proyecto()
        # Obtener el objeto ventana del proyecto
        principal_proyecto = self.builder.get_object("proyecto_principal")

        ## Label para los errores
        self.errores_label = self.builder.get_object("proyecto_principal_errores")
        self.errores_label.set_text("")


        # Ocultar lo que hay en principal ahora mismo
        children = self.principal.get_children()
        for child in children:
            child.hide()

        # Añadir a principal y mostrar
        principal_proyecto.reparent( self.principal )
        principal_proyecto.show()

        # Conectar señales nuevas
        self.builder.connect_signals(self)

    def cargar_portada(self, widget = None):
        """ 
            @brief Carga la portada del programa
            @param widget El widget desde donde se llama.
        """

        # Ocultar lo que hay en principal ahora mismo
        children = self.principal.get_children()
        for child in children:
            child.hide()

        webhelp = 'file://' + path.join(self.opt.get('share'),
                                         'help/es/main.html') 
        self.web.open(webhelp)
        self.portada.add(self.web)
        self.portada.reorder_child(self.web, 2)
        self.portada.reparent( self.principal )
        self.portada.show_all()

    def on_main_ventana_destroy(self,widget):
        """@brief Callback de pulsar el cierre de la ventana."""
        self.idg.cerrar()
        gtk.main_quit()

    def on_main_exportar(self, widget):
        """@brief Callback de pulsar la opción de exportar"""
        pass

    def on_main_importar(self, widget):
        """@brief Callback de pulsar la opción de importar"""
        pass

    def on_menu_opciones(self, widget):
        """@brief Callback de seleccionar en el menú ver las opciones."""
        OptUI(self.builder, self.idg.opt)

    ## @}

