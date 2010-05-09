# File abstractions
# -*- coding: utf-8 -*-

import os
import os.path as path
from xml.dom import minidom as md
from xml.etree import ElementTree as et
from exceptions import IOError, NotImplementedError

import util.logger
log = util.logger.getlog('idg.file')

class File(object):
    """@brief Base class for file management.
    
    Implements basic common file operations whithin the application.
    This a base class to inherit from. 
    """

    ## Associed file descriptor.
    _file = None

    def __init__(self, path_):
        """@brief Initialize File

        @param path File path

        If the file don't exists yet, it won't be created until open is called.
        """
        self._path = self.abspath(path_)
        self._name = path.basename(self._path)

    def name(self):
        """@returns The name of the file"""
        return self._name

    def path(self):
        """@returns The path of the file"""
        return self._path

    def open(self, mode='r'):
        """@brief Opens the file descriptor

        @param mode File open standar mode (r by default).
        @returns The open file descriptor.

        Does nothing if the file is already open.
        """
        if not self.is_open():
            try:
                self._file = open(self._path, mode)
            except IOError:
                log.error(_("idg.file.cant.open.file.for") + self._path + " " +\
                          mode)

        return self._file

    def close(self):
        """@brief Close the file descriptor

        Just closes the file, do not write changes. Use save for that.
        Does nothing if the file isn't open.
        """
        if self.is_open(): 
            self._file.close()
            self._file = None

    def is_open(self):
        """@brief Checks if the file is already open

        @returns True if the file is open. False otherwise.
        """
        return (self._file is not None) and (not self._file.closed)

    def save(self):
        """@brief Write the changes made to the file."""
        raise NotImplementedError

    @staticmethod
    def abspath(path_):
        """@brief Returns the absolute path of the file.

        @param path_ Path to transform.
        @returns The absolute version of path.
        """
        return path.abspath(path.realpath(path.expanduser(path_)))

    def get_abspath(self):
        """@brief Returns the absolute path of the file.
        
        @returns Absolute and real path of the file.
        Expands ~ symbol to $HOME
        Uses the real path if symlinks are present
        """
        return File.abspath(self._path)

    def relpath(self, from_="", path_=""):
        """@brief Returns the relative path to the file

        @param from_ The origin path to calculate the relative path. If ommited
        will use internal path
        @param path_ The destination path. If ommited will use internal path.
        @returns The relative path from from_ to path_

        First, calculates the absolute and expanded path of both from_ and
        path_.
        """
        from_ = self.abspath(from_ if from_ else self._path)
        path_ = self.abspath(from_ if from_ else self._path)
        return path.relpath(path_, from_)

    @staticmethod
    def is_external(proy, path_):
        """@brief Check if the file is inside the given proyect

        @param proy The proyect directory path 
        @param path_ Path to check.
        @returns True if the file is in the directory. False otherwise.
        """
        proy = self.abspath(proy)
        path_ = self.abspath(path_)
        return path_.startswith(proy)

    def external(self, proy):
        """@brief Check if the file is inside the given proyect

        @param proy The proyect directory path 
        @returns True if the file is in the directory. False otherwise.
        """
        return File.external(proy, self._path)

class XMLFile(File):
    """@brief Base class for XML files.

    Implements basic common file operations with xml.
    Allows to use minidom or ElementTree, but do NOT use both at the same time.
    """

    _dom = None
    _type = None

    def type(self):
        """@brief Returns the opened doms (md, et) or None"""
        return self._type

    def open(self, type="md"):
        """Convenience function to fit the File interface
        Opens and returns a dom instance of minidom or etree.

        @param type Select the type of dom. Values: md, et
        @returns Opened minidom or ElementTree dom. None in case of error.
        """
        return self.dom(type)

    def save(self):
        """@brief Convenience function to fit the File interface

        @returns True if all ok. None in case of error.
        """
        self.serialize()

    def close(self):
        """@brief Resets the open dom without write the changes"""
        self._dom = None

    def dom(self, type="md"):
        """@brief Returns an opened dom of the specified type (md or et)

        @param type Select the type of dom. Values: md, et
        @returns Opened minidom or ElementTree dom. None in case of error.
        """
        try:
            if self._dom is None:
                if type == 'md':
                    self._dom = md.parse(self._path)
                if type == 'et':
                    self._dom = et.ElementTree()
                    self._dom.parse(self._path)

                self._type = type
        except:
            log.error(_('idg.file.cannot.parse.file') + type + " " + self._path)
        finally:
            return self._dom

    def serialize(self, path=""):
        """@brief Writes the selected dom, previously opened

        @param path Serialize in another file, not in _path.
        @returns True if serialized correctly, None in case of error.
        """
        path = path if path else self._path
        check = self._serialize_minidom(path) if self._type == 'md' else\
                self._serialize_tree(path)

        if check is None:
            log.error(_('idg.file.cant.serialize.xml') + type + " " + path)

        return check

    def _serialize_minidom(self, path_):
        """@brief Serializes minidom document

        @returns True if serialized correctly. None in case of error.
        """
        if path.exists(path_) and self._dom is not None:
            self.fix_none_tags()
            f = open(path_, 'w')
            f.write(self._dom.toxml(encoding="utf-8"))
            f.close()
            return True
        else:
            return None

    def _serialize_tree(self, path_):
        """@brief Serializes ElementTree document

        @returns True if serialized correctly. None in case of error.
        """
        if path.exists(path_) and self._dom is not None:
            self._dom.write(path_)
            return True
        else:
            return None

    def fix_none_tags(self):
        """@brief Walks the dom looking for attributes with None for attribute
        values.

        Fixes minidom bug. Read http://bugs.python.org/issue5762

        When a element attribute have None as value, minidom toxml fails.
        Existent patches solves this problem by replacing None values with "" in
        minidom internal functions.

        The implemented fix walks the entire document looking for None values
        into attributes and replacing it with empty strings.
        """
        elements = [self._dom]
        while elements:
            e = elements.pop(0)

            if e.attributes:
                for a,v in e.attributes.items():
                    if v is None:
                        #log.debug('None encontrado')
                        #log.debug(e)
                        #log.debug(a)
                        e.attributes[a] = ""
            elements.extend(e.childNodes)

    def autodeclare(self):
        """@brief Autodeclare namespaces"""
        self._autodeclare(self._dom.fistChild)

    def _autodeclare(self, parent):
        """@brief Inline declaration for all namespaces references in the
        document.

        @param e Parent dom
        @returns the same givn parent element.
        """

        # We'll use a queue to process the elements in document order
        elms = [parent]
        while elms:
            e = elms.pop(0)
            # Add inline declaration if they need it.
            if e.namespaceURI:
                if not e.prefix:
                    e.previx = 'ns0'   # Avoid empty prefixes
                e.setAttribute('xmlns:' + e.prefix, e.namespaceURI)

            # Queue children
            elms.extend(e.childNodes)

        return parent

    def _get_parent(self, e, name):
        """@brief Finds the parent of the element with the given name.

        @returns dom of parent element or None if couldn't be founded.
        """
        while e is not None and e.parentNode is not None:
            # Namespaced elements tag is preceeded by "prefix:"
            prefix = "" if not e.namespaceURI else e.prefix + ":"
            if prefix + e.tagName == name: break # We found it!
            e = e.parentNode # Next parent

        return e



class ConfigFile(XMLFile):
    """@brief Configuration file.

    Manages options.
    """

    def __init__(self, path_):
        """@brief Initializes and opens the config file.

        Uses ElementTree for common operations and serialization.
        """
        XMLFile.__init__(self, path_)
        # Open the file with ElementTree
        self.open('et')

    def save(self, dict={}):
        """@brief Update the configuration file using the options in
        dictionary

        @param dict Dictionary in the form {id: [val, type]} with options to
        add.
        @returns True if no problem. None if the file couldn't be wroten.
        Overrides File.save
        """
        root = self._dom.getroot()
        for id, (val, type) in dict.items():
            self.set(id, val, type)

        return self.serialize()

    def set(self, id, val, type=None):
        """@brief Set a option in the file

        @param id Identifier of the option.
        @param val Value of the option.
        @param type The type of the option.
        @returns True if a new option was added. False if an old option was
        updated. None in case of error.

        Note: When adding a new option, type is mandatory (value/src).
        """
        root = self._dom.getroot()
        e = root.find(id)

        new = e is None

        if new:
            # Create new element.
            e = et.SubElement(root, id)
            if type is None: return  # New option --> type is mandatory

        # If already exists and no type is given, use the same that already has.
        elif type is None:
            type = 'src' if 'src' in e.attrib else 'value'

        e.clear()  # Reset old values and attributes.
        e.set(type, val)

        return new

    def get(self, id):
        """@brief Get the option from the file.

        @returns (value, type), or None if the option isn't in the file.
        """
        root = self._dom.getroot()
        e = root.find(id)
        if e is None: return None

        if e.get('src') is None:
            return e.get('value'), 'value'
        elif e.get('value') is not None:
            return e.get('src'), 'src'
        else:
            return None

    def get_all(self, ltype=""):
        """@brief Returns all the options in a dictionary with the following
        structure:
            {id: [value, type], ..}

        @param ltype Filter options by type. All by default.
        @returns Dictionary with the options.

        Expands absolute paths in src options. DON'T checks paths.
        """
        root = self._dom.getroot()

        dict = {}

        for e in root.getchildren():
            id = e.tag
            type = 'src' if 'src' in e.attrib else 'value'
            # Filter by type
            if ltype and ltype != type: continue

            val = e.get(type)
            if type == 'src':
                val = ConfigFile.abspath(val)

            if val is not None:
                dict[id] = [val, type]

        return dict

class ANTFile(XMLFile):
    """@brief ANT file.

    Manages ANT properties
    """

    def __init__(self, path_):
        """@brief Initialize and open the ANT File.

        Reads all properties an stores it in a dictionary.
        """
        XMLFile.__init__(self, path_)
        self.open("md")

        # Root element project
        try:
            self._project = self._dom.getElementsByTagName('project')[0]
        except:
            log.error(_('idg.file.antfile.missing.project.element'))
            self.close()

    def get(self, name, attr):
        """@brief Returns the value of the selected attribute of the property
        with the given name.


        @param name The property name
        @param attr The attribute name
        @returns A string with the value, False if the attribute doesn't exist
        or None if the property doesn't exist.
        """
        property = self._get_property(name)

        if property is None:
            return None
        elif not property.hasAttribute(attr):
            return False
        else:
            return property.getAttribute(attr)

    def set(self, name, attr, val):
        """@brief Set the attribute of the property referenced with name.
        Creates the property if doesn't previously exist.

        @param name The property name
        @param attr The property attribute
        @param val The value to set the property attribute
        @returns True if a new property was created. False otherwise.
        """
        property = self._get_property(name)
        new = False
        if property is None:
            new = True
            property = self._create_property(name)

        property.setAttribute(attr, val)

        return new

    # @name Internal
    # @{

    def _get_property(self, name):
        """@returns the dom element of a property with the given name. None if
        the property doesn't exist.

        @param name The property name.
        """

        try:
            return [p for p in self._dom.getElementsByTagName('property')\
                    if p.getAttribute('name') == name][0]
        except:
            return None

    def _create_property(self, name):
        """@brief Creates a new property with the given name, inserts it in the
        tree and returns its dom object.

        @param name The property name.
        """
        property = self._dom.createElement('property')
        property.setAttribute('name', name)
        self._project.appendChild(property)
        return property

    # @}
