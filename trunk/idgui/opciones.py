# -*- coding: utf-8 -*-

import os.path as path
import gtk

# Establecer el log
import util.logger
log = util.logger.getlog('idgui.options')

class OptUI(object):
    """Clase que permite manejar las opciones del programa desde la gui."""

    _CHANGED_ICON = gtk.STOCK_MEDIA_RECORD
    _NORMAL_ICON = gtk.STOCK_PROPERTIES

    def __init__(self, gtk, opts):
        """@brief Constructor de la gui de opciones
        @param gtk Builder de gtk
        @param opts Clase Opt
        """

        ## Builder de gtk
        self.gtk = gtk
        ## Clase Opt con las opciones
        self.opts = opts
        ## Flag de modificación
        self.mod = False

        # Añadir el glade
        gtk.add_from_file(path.join(opts.get('share'),"ui/opts.glade"))
        self.window = gtk.get_object('opt_window')

        # Vista 
        self.view = gtk.get_object('opt_treeview')
        # Lista
        self.list = gtk.get_object('opt_list')

        # Cargar la tabla
        self.cargar()

        # Conectar las señales que faltan
        gtk.connect_signals(self)

        # Abrir la ventana
        self.window.show_all()

    def cargar(self):
        # Desconectar la lista de la vista
        self.view.set_model(None)

        # Vaciar la lista
        self.list.clear()

        # Recorremos las opciones creando labels e inputs
        # con los valores y añadiéndolos a la tabla
        for id, (val, type) in self.opts.getall().items() :
            self.list.append([id, val,
                              self._NORMAL_ICON, _('msg.help.opt.' + id)])

        # Volver a conectar el modelo y la vista
        self.view.set_model(self.list)

    def on_changed(self, cell, path, val):
        """@brief Callback de cuando se modifica una entrada."""
        # Establecer las opciones como modificadas.
        log.debug("Modificado: " + self.list[path][0] + " de " +
                  self.list[path][1] + " a " + val)

        # Modificarlo en las opciones
        id = self.list[path][0]
        self.mod = self.opts.set(id, val)

        # Modificarlo en el treeview
        if self.mod is not None:
            self.list[path][1] = val
            self.list[path][2] = self._CHANGED_ICON
            self.list[path][3] = _('msg.help.opt.' + id)
        else:
            self.list[path][2] = self._NORMAL_ICON
            log.error(_('idgui.options.cant.change.option') + id)
            #  Indicar error

    def on_guardar(self, widget):
        if self.mod :
            self.opts.write()
        self.window.destroy()

    def on_cancelar(self, widget):
        if self.mod :
            #preguntar
            pass
        self.window.destroy()

    def on_reset(self, widget):
        """@brief Callback de pulsar el botón de resetear las opciones."""
        antes = [ l[1] for l in self.list]
        self.mod = True
        self.opts.reset()
        self.cargar()

        # Poner iconos a los que se han modificado
        for a,d in zip(antes,self.list):
            if a != d[1] :
                d[2] = self._CHANGED_ICON
