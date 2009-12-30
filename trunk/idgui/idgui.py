# Clase de Interfaz de usuario
# -*- coding: utf-8 -*-

import os.path as path
import pygtk
pygtk.require("2.0")
import gtk

import lang
from proyecto import ProyectoUI


class Idgui(object):
    """@Brief Objeto principal de la gui."""

    def __init__(self,idg):
        """
           @brief Inicializa la GUI de IndigBPEL
           @param idg Instancia de IndigBPEL
        """

        # Instancia de gtkbuilder
        self.builder = gtk.Builder()

        # Instancia de la clase idg
        self.idg = idg;

        ### Ventana principal
        # Leer xml de la ventana principal
        #self.builder.add_from_file("idgui/ui/main.glade")
        self.builder.add_from_file(path.join(self.idg.share,"ui/main.glade"))

        # Obtener objeto ventana
        self.main_ventana = self.builder.get_object("main_ventana")

        # Obtener objeto panel principal
        self.principal = self.builder.get_object("principal")

        ### Cargar portada en principal
        self.cargar_portada()

        ### Lista de proyectos 
        # Modelo ListStore
        self.modelo_lista_proyectos = gtk.ListStore( str )

        # Vista ListStore
        self.vista_lista_proyectos = self.builder.get_object("lista_proyectos_vista");
        self.vista_lista_proyectos.set_model( self.modelo_lista_proyectos );

        # Añadir columna
        columna = gtk.TreeViewColumn('Proyectos', gtk.CellRendererText() , text=0)
        self.vista_lista_proyectos.append_column( columna )

        # Actualizar la lista de proyectos
        self.listar_proyectos()

        ### Conectar señales 
        ##self.builder.connect_signals({ "on_main_ventana_destroy" : gtk.main_quit })
        self.builder.connect_signals(self)

        # Mostrar la ventana
        self.main_ventana.show()

        # Bucle principal
        gtk.main()

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

    def nuevo_proyecto(self, widget):
        """
            @brief Callback de presionar el botón de Nuevo Proyecto
                    carga la pantalla de crear un nuevo proyecto.
            @param widget El botón que se pulsó.
        """

        self.nuevo = True
        # Cargar el proyecto desde el glade
        self.builder.add_from_file(path.join(self.idg.share,"ui/proyecto_panel.glade"))

        # Filtro para el selector de ficheros
        self.filtro_fichero_bpel = self.builder.get_object("filtro_fichero_bpel");
        self.filtro_fichero_bpel.add_pattern("*.bpel");
        self.builder.get_object("proyecto_selector_bpel").add_filter(self.filtro_fichero_bpel);

        # Obtener el objeto ventana del proyecto
        principal_proyecto = self.builder.get_object("proyecto_principal")

        # Ocultar lo que hay en principal ahora mismo
        children = self.principal.get_children()
        for child in children:
            child.hide()

        # Añadir a principal
        principal_proyecto.reparent( self.principal )

        # Mostrar
        principal_proyecto.show()

        # Conectar señales nuevas
        self.builder.connect_signals(self)

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
        # Label donde poner los errores
        errores = self.builder.get_object("proyecto_principal_errores")
        # Cadena con los errores
        error_str = ""

         # Comprobar nombre del proyecto
        if nombre == "":
            error_str =  _("El nombre del proyecto no puede estar vacío")

        # Obtenemos la ruta del bpel.
        bpel = self.builder.get_object("proyecto_selector_bpel").get_filename()
        if bpel is None:
            error_str += "\n" + _("Fichero bpel no seleccionado") 

        # Comprobar los errores y mostrarlos
        if error_str :
            errores.set_text(error_str)
            return error_str

        print _("Creando proyecto con el fichero bpel: "), bpel

        # Creamos el proyecto
        # False si todo va bien
        try:
            #res = self.idg.crear_proyecto(nombre,bpel)
            #self.proyecto = ProyectoUI(self.idg,self.builder)
            self.cargar_proyecto(nombre,bpel)
        except:
            print _("Excepción al crear proyecto ") + res
            #errores.set_text(e)
        else:
            # Si el proyecto ha sido creado correctamente
            # Actualizar la lista de proyectos 
            self.listar_proyectos()
            #self.cargar_proyecto()

        return True

    def cargar_portada(self, widget = None):
        """ 
            @brief Carga la portada del programa
            @param widget El widget desde donde se llama.
        """

        # Comprobar si portada está inicializada
        # y cargarla en ese caso
        #self.builder.add_from_file("idgui/ui/portada.glade")
        self.builder.add_from_file(path.join(self.idg.share,"ui/portada.glade"))
        self.portada = self.builder.get_object("portada")

        # Ocultar lo que hay en principal ahora mismo
        children = self.principal.get_children()
        for child in children:
            child.hide()

        self.portada.reparent( self.principal )
        self.portada.show()

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

        # Crear el proyecto UI
        self.proyecto = ProyectoUI(self.idg,self.builder,nombre,bpel)

    def on_lista_proyectos_cursor_changed(self, treeview):
        """
            @brief Callback de seleccionar un proyecto de la lista de
            proyectos. Toma el nombre de la interfaz y carga el proyecto.
            @param treeview El widget treeview con la lista de proyectos
        """

        # Obtener la selección
        model, sel = treeview.get_selection().get_selected()
        nombre = model.get_value(sel,0)
        print _("Seleccionado el proyecto: "), nombre;
        # Cargar el proyecto en idg
        # Cargar el proyecto en la gui
        self.cargar_proyecto(nombre)
        #if self.idg.cargar_proyecto(nombre) is None :
        #    self.cargar_proyecto();

    def error(self,msg):
        pass

    def on_main_ventana_destroy(self,widget):
        gtk.main_quit()
