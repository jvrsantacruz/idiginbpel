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
import gettext

import util.logger
log = util.logger.getlog('idgui.main')

from idgui.proyecto import ProyectoUI
from idgui.opciones import OptUI

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

        self.builder.set_translation_domain(gettext.textdomain())

        ### Ventana principal
        self.builder.add_from_file(path.join(self.idg.opt.get('share'),\
                                             "ui/main.glade"))
        self.builder.add_from_file(path.join(self.idg.opt.get('share'),\
                                             "ui/proj_context_menu.glade"))

        ## Objeto ventana
        self.main_ventana = self.builder.get_object("main_ventana")
        ## Contenedor Principal
        self.principal = self.builder.get_object("principal")
        ## Barra de estado
        self.barra_estado = self.builder.get_object("main_estado")
        ## Treeview lista proyectos
        self.lista_treeview =\
                self.builder.get_object("main_lista_proyectos_vista")
        ## Popup lista proyectos
        self.lista_popup = self.builder.get_object("proj_context_menu")

        # Cargar portada en principal

        # Cargar el glade de la portada
        self.builder.add_from_file(path.join(self.idg.opt.get('share'),\
                                             "ui/portada.glade"))
        ## Portada de la aplicación con el dibujo de bienvenida
        self.web = webkit.WebView()
        #self.html.load_html_string("<p>HoHoHo</p>", "file:///")
        self.portada = self.builder.get_object("portada")
        self.cargar_portada()

        # Conectar las acciones al menú contextual
       # self.builder.get_object("menu_action_open_project")\
       #         .connect_proxy(self.builder.get_object("proj_context_menu_open"))

        self.builder.get_object("menu_action_close_project")\
                .connect_proxy(self.builder.get_object("proj_context_menu_close"))

        self.builder.get_object("menu_action_export_project")\
                .connect_proxy(self.builder.get_object("proj_context_menu_export"))

       # self.builder.get_object("menu_action_import_project")\
       #         .connect_proxy(self.builder.get_object("proj_context_menu_import"))

        self.builder.get_object("menu_action_remove_project")\
                .connect_proxy(self.builder.get_object("proj_context_menu_rm"))

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
        self.builder.add_from_file(path.join(self.idg.opt.get('share'),\
                                             "ui/nuevo_proyecto.glade"))

        # Filtro para el selector de ficheros
        #filtro_fichero_bpel = self.builder.get_object("proyecto_filtro_fichero_bpel").add_pattern("*.bpel")

    ## @}

    ## @name Actualizar
    ## @{

    def listar_proyectos(self, widget=None):
        """ 
            @brief Lista los proyectos disponibles en la barra principal.
            @param widget El widget desde donde se llama a esta función.
        """
        # Recargar proyectos
        self.idg.update_proylist()

        # Limpiar lista actual
        self.modelo_lista_proyectos.clear()
        for p in self.idg.get_proylist():
            self.modelo_lista_proyectos.append([p]) 

    def get_proy_seleccionado(self):
        """
        @brief Devuelve el proyecto seleccionado en la lista o None.
        """
        if self.lista_treeview.get_selection():
            model, sel = self.lista_treeview.get_selection().get_selected()
            return model.get_value(sel,0)
        else:
            return None

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
        try:
            ## Referencia a la instancia de ProyectoUI abierta en el momento
            self.proyecto = ProyectoUI(self.idg,self,nombre,bpel)
        except:
            log.error("Crear Proyecto %s: %s" % sys.exc_info()[:2])
            log.error("%s" % traceback.print_exc())
            self.estado(_("idgui.main.error.loading.project"))
            self.cargar_portada()
            return

        # Comprobar que el proyecto actualmente cargado, si lo hay, 
        #  no es el mismo que pretendemos cargar.
        if not self.idg.proy is None \
           and self.idg.proy .nombre == nombre :
            log.info(_("idgui.main.already.loaded.nothing.to.do"))
            # Mostrarlo en la interfaz
            self.proyecto.proyecto_base.reparent(self.proyecto.principal)
            self.proyecto.proyecto_base.show()
            return False

    def estado(self,msg,dsc=""):
        """@brief Añadir estado a la barra de estado de la aplicación.
        @param msg Mensaje a añadir.
        @param dsc Descripción del mensaje en la statusbar."""
        id = self.barra_estado.get_context_id(dsc)
        self.barra_estado.push(id,str(msg))

    ## @}

    ## @name Callbacks 
    ## @{

    def on_action_open_activate(self, action):
        """
        @brief Callback de abrir un proyecto.
        @param El action desde el cual se llamó.
        """
        pass

    def on_action_close_activate(self, action):
        """
        @brief Callback de cerrar un proyecto.
        @param El action desde el cual se llamó.
        """
        if self.proyecto is not None:
            self.proyecto.cerrar()
            self.proyecto = None

        self.cargar_portada()

    def on_action_import_activate(self, action):
        """
        @brief Callback de importar un proyecto.
        @param El action desde el cual se llamó.
        """
        filter = gtk.FileFilter()
        #filter.add_mime_type("application/x-gzip-compressed-tar")
        filter.add_pattern("*.idg")

        file_chooser = gtk.FileChooserDialog(\
                            title=_('idgui.main.select.import.title'),
                            parent=self.main_ventana,
                            action=gtk.FILE_CHOOSER_ACTION_OPEN,
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        file_chooser.set_default_response(gtk.RESPONSE_OK)
        file_chooser.add_filter(filter)

        if file_chooser.run() == gtk.RESPONSE_OK:
            filepath = file_chooser.get_filename()

            if filepath is None: 
                return False

            cmp = self.idg.importation(filepath)

            if cmp:
                self.listar_proyectos()
                self.estado(_('idgui.main.project.imported.successfully'))
            else:
                self.estado(_('idgui.main.project.imported.error'))

        file_chooser.destroy()

    def on_action_export_activate(self, action):
        """
        @brief Callback de exportar un proyecto.
        @param El action desde el cual se llamó.
        """
        name = self.get_proy_seleccionado()
        file_chooser = gtk.FileChooserDialog(\
                            title=_('idgui.main.select.export.title'),
                            parent=self.main_ventana,
                            action=gtk.FILE_CHOOSER_ACTION_SAVE,
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        file_chooser.set_do_overwrite_confirmation(True)
        file_chooser.set_current_name(name + ".idg")
        file_chooser.set_default_response(gtk.RESPONSE_OK)

        if file_chooser.run() == gtk.RESPONSE_OK:
            filepath = file_chooser.get_filename()

            if filepath is None: 
                return False

            cmp = self.idg.exportation(name, filepath)

            if cmp:
                self.estado(_('idgui.main.project.exported.successfully'))
            else: 
                self.estado(_('idgui.main.project.exported.error') 
                                + name + " at " + filepath)
        file_chooser.destroy()

    def on_action_rm_activate(self, action):
        """
        @brief Callback de borrar un proyecto.
        @param El action desde el cual se llamó.
        """
        dialog = gtk.MessageDialog(parent=self.main_ventana,
                                   type=gtk.MESSAGE_QUESTION,
                                   buttons=gtk.BUTTONS_OK_CANCEL,
                                   message_format=
                                   _('idgui.main.rm.project.dialog'))

        if dialog.run() == gtk.RESPONSE_OK:
            if self.idg.proy is not None:
                name = self.idg.proy.nombre
                self.on_action_close_activate(None)
                self.idg.proy.borrar()
                self.idg.proy = None
                self.listar_proyectos()
                self.estado(_('idgui.main.project.removed') + name)

        dialog.destroy()


    def on_lista_proyectos_release(self, treeview, event):
        """
        @brief Callback de hacer click sobre la lista de proyectos.
        @param treeview El widget treeview con la lista de proyectos.
        @param event El evento del ratón.
        """
        if event.button == 3: # Right click
            x = int(event.x)
            y = int(event.y)

            pathinfo = treeview.get_path_at_pos(x, y)
            if pathinfo is not None:
                filepath, col, cellx, celly = pathinfo
                self.lista_popup.popup(None, None, None,
                                       event.button,event.time)

    def on_lista_proyectos_cursor_changed(self, treeview):
        """
            @brief Callback de seleccionar un proyecto de la lista de
            proyectos. Toma el nombre de la interfaz y carga el proyecto.
            @param treeview El widget treeview con la lista de proyectos
        """

        # Obtener la selección
        model, sel = treeview.get_selection().get_selected()
        nombre = model.get_value(sel,0)
        log.info(_("idgui.main.selected.proyect") + nombre)

        # Si hay otro ya abierto, cerrarlo
        if self.proyecto is not None:
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
            error_str =  _("idgui.main.proyect.name.cant.be.empty") 

        # No debe estar usado
        elif nombre in self.idg.get_proylist():
            error_str =  _("idgui.main.proyect.name.already.exists") 

         # Debe ser un nombre 'unix' válido
        else:
            # Caracteres que no deben estar en el nombre del proyecto
            wrong = "|:,!@#$()/\\\"'`~{}[]=+&^ \t"
            for i in wrong:
                if nombre.find(i) != -1 :
                    error_str = _("idgui.main.name.cant.contain.character") + '"%c"' % i
                    break

        # La ruta debe estar seleccionada
        if bpel is None:
            error_str = _("idgui.main.bpel.file.not.selected") 
        elif not os.access(bpel, os.F_OK or os.R_OK or os.W_OK):
            error_str = _("idgui.main.selected.bpel.file.dont.exist")

        # Comprobar los errores y mostrarlos
        if error_str :
            self.errores_label.set_text(error_str)
            return error_str

        log.info(_("idgui.main.creating.proyect.with.bpel") + bpel)

        # Creamos el proyecto
        # False si todo va bien
        try:
            self.cargar_proyecto(nombre,bpel)
        except:
            log.error(_("idgui.main.exception.in.proyect.creation"))
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
        self.idg.close()
        gtk.main_quit()

    def on_menu_opciones(self, widget):
        """@brief Callback de seleccionar en el menú ver las opciones."""
        OptUI(self.builder, self.idg.opt)

    ## @}

