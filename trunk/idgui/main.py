# Clase de Interfaz de usuario
# -*- coding: utf-8 -*-

import pygtk
pygtk.require("2.0")
import gtk
import lang

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
        self.builder.add_from_file("idgui/ui/main.glade")

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
        self.builder.add_from_file("idgui/ui/proyecto_panel.glade")

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
            @param widget El botón que se pulsó.
            @returns False si todo va bien y se crea el proyecto. El error correspondiente en caso contrario.
        """

        # Obtenemos el nombre que el usuario ha escrito.
        # Limpiamos los espacios
        nombre = self.builder.get_object("proyecto_nombre").get_text().strip()
        if nombre == "":
            return "El nombre del proyecto no puede estar vacío"

        # Obtenemos la ruta del bpel.
        bpel = self.builder.get_object("proyecto_selector_bpel").get_filename()
        if bpel is None:
            return "Fichero bpel no seleccionado"

        print _("Seleccionado el fichero "), bpel

        # Si devuelve False todo va bien.
        res = self.idg.crear_proyecto(nombre,bpel)

        # Si el proyecto ha sido creado, cargarlo en pantalla.
        if not res:
            # Actualizar la lista de proyectos
            self.listar_proyectos()
            return self.cargar_proyecto(nombre)
        else:
            print res
            return res

    def cargar_portada(self, widget = None):
        """ 
            @brief Carga la portada del programa
            @param widget El widget desde donde se llama.
        """

        # Comprobar si portada está inicializada
        # y cargarla en ese caso
        self.builder.add_from_file("idgui/ui/portada.glade")
        self.portada = self.builder.get_object("portada")

        # Ocultar lo que hay en principal ahora mismo
        children = self.principal.get_children()
        for child in children:
            child.hide()

        self.portada.reparent( self.principal )
        self.portada.show()

    def cargar_proyecto(self, nombre):
        """ 
            @brief Cargar un proyecto en proyecto_base.
            @param nombre El nombre del proyecto.
            @return False si todo ha ido bien.
        """

        #res = self.idg.cargar_proyecto(nombre)

        self.builder.add_from_file("idgui/ui/proyecto_base.glade")
        self.proyecto = self.builder.get_object("proyecto_base")

        # Ocultar lo que hay en principal ahora mismo
        children = self.principal.get_children()
        for child in children:
            child.hide()

        self.proyecto.reparent( self.principal )

    def on_lista_proyectos_cursor_changed(self, treeview):
        """
            @brief Callback de seleccionar un proyecto de la lista de proyectos.
            @param treeview El widget treeview con la lista de proyectos
        """

        # Obtener la selección
        model, sel = treeview.get_selection().get_selected()
        nombre = model.get_value(sel,0)
        print _("Seleccionado el fichero "), nombre;

        self.cargar_proyecto(nombre);

    def error(self,msg):
        pass

    def error_inline(self,msg):
        pass

    def on_main_ventana_destroy(self,widget):
        gtk.main_quit()

