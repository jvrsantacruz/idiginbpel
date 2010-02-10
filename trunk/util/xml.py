# Funciones comunes de xml
# -*- coding: utf-8 -*-

#import xml.dom.minidom

def minidom_namespaces(elto):
    """@brief Declara inline namespaces no declarados
       @param elto Elemento padre"""

    # Utilizamos una cola y procesamos los elementos en orden de documento
    eltos = [elto]
    while eltos :
        e = eltos.pop(0) 
        # Les añadimos la declaración del namespace si tienen
        if e.namespaceURI :
            e.setAttribute('xmlns:' + e.prefix, e.namespaceURI)
        # Metemos sus hijos en la cola
        eltos.extend(e.childNodes)

    return elto
