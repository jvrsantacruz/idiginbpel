# Funciones comunes de gtk
# -*- coding: utf-8 -*-

def foreach_cb(model, path, iter, pathlist):
    """@brief Callback para selected_foreach. Añade a una lista las rutas de
    las filas  seleccionadas"""
    pathlist.append(path)

def get_selected_rows(treeselection):
    """@brief Obtiene todas las rutas seleccionadas de un treeview
    @retval Lista de rutas con la selección del treeview."""
    pathlist = []
    treeselection.selected_foreach(foreach_cb, pathlist)
    model = sel.get_treeview().get_model()
    return (model, pathlist)
