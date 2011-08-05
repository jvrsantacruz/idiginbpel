# -*- coding: utf-8 -*-

import os.path as path
import gtk

# Establecer el log
import util.logger
log = util.logger.getlog('idgui.options')

class OptUI(object):
    """Clase que permite manejar las opciones del programa desde la gui.

    En el treeview:
        0 - Nombre
        1 - Valor
        2 - Icono
        3 - Texto de Ayuda
    """

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
        self.statusbar = gtk.get_object("opt_statusbar")

        # Vista 
        self.view = gtk.get_object('opt_treeview')
        # Lista
        self.list = gtk.get_object('opt_list')

        # map con los cambios nombre - valor
        self.changes = {}

        # Cargar la tabla
        self.cargar(self.opts.getall())
        # Conectar las señales que faltan
        gtk.connect_signals(self)
        # Abrir la ventana
        self.window.show_all()

    def cargar(self, values):
        """
        @brief Recarga la lista de opciones
        @param valores para recargarla en un diccionario
                tipo { id : [valor, tipo] }
        """
        # Desconectar la lista de la vista
        self.view.set_model(None)

        # Vaciar la lista
        self.list.clear()

        # Recorremos las opciones creando labels e inputs
        # con los valores y añadiéndolos a la tabla
        for id, (val, type) in values.items() :
            msg = _('msg.help.opt.' + id) 
            # Add no-available message if necessary
            if msg == 'msg.help.opt' + id :
                msg = _('idgui.options.no.help.available') 
            self.list.append([id, val, self._NORMAL_ICON,\
                              _('msg.help.opt.' + id)])

        # Volver a conectar el modelo y la vista
        self.view.set_model(self.list)

    def on_changed(self, cell, path, val):
        """@brief Callback de cuando se modifica una entrada."""

        # Modificar solo cuando algo cambie
        if self.list[path][1] == val:
            return None

        id = self.list[path][0]
        log.debug("checking: %s : %s" % (val, self.opts.check(id, val)))

        # Modificarlo en el treeview
        if self.opts.check(id, val):
            self.changes[id] = val
            self.list[path][1] = val
            self.list[path][2] = self._CHANGED_ICON
            self.list[path][3] = _('msg.help.opt.' + id)
            self.statusbar.push(self.statusbar.get_context_id("error")
                                ,_('idgui.options.successfully.changed') + id)
        else:
            self.list[path][2] = self._NORMAL_ICON
            error_txt = _('idgui.options.cant.change.option') + id
            log.error(error_txt)
            self.statusbar.push(self.statusbar.get_context_id("error")
                                ,error_txt)

    def on_guardar(self, widget):
        # TODO: preguntar
        log.info(_('idgui.options.saving.options'))
        for id,val in self.changes:
            self.opts.set(id, val)

        self.opts.write()
        self.window.destroy()

    def on_cancelar(self, widget):
        # TODO: preguntar
        log.info(_('idgui.options.closing.without.saving'))
        self.window.destroy()

    def on_reset(self, widget):
        """@brief Callback de pulsar el botón de resetear las opciones."""
        self.changes = dict([(l[0],l[1]) for l in self.list])
        self.mod = True

        self.cargar(self.opts.get_defaults())

        # Poner iconos a los que se han modificado
        for item in self.list:
            if self.changes[item[0]] != item[1]:
                item[2] = self._CHANGED_ICON
            else:
                del self.changes[item[0]]

        self.statusbar.push(self.statusbar.get_context_id("reset"),
                            _('idgui.options.default.opts.setted'))
