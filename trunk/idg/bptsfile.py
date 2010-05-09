# BPTS File abstractions
# -*- coding: utf-8 -*-

import os.path as path

from file import XMLFile
import util.logger

log = util.logger.getlog('idg.bptsfile')

class BPTSFile(XMLFile):
    """@brief BPTS test case file common operations"""

    ## Cases list (short case names)
    _cases = []

    ## Round cases dict {case: rounds, ..}
    _round_cases = {}

    ## Related files dict {case: [ (src, type), ..], ..}
    _attach = {}

    ## BPTS Namespace
    _NS ='http://www.bpelunit.org/schema/testSuite'

    ## get info copied flag.
    _copied_info = False

    def __init__(self, path_, normalize=False):
        """@brief Initialize and open the BPTS file."""
        XMLFile.__init__(self, path_)
        # Open the file with Minidom
        self.open('md')
        self._update_data()
        if normalize:
            self.normalize()
        self._update_cases()

    def normalize(self):
        """@brief Normalize the btps names to idiginBPEL internal proyect
        conventions.

        Changes the name of the cases up to 'file:case'
        """
        for case in self._dom.getElementsByTagNameNS(self._NS, 'testCase'):
            name = case.getAttributeNS(self._NS, 'name').replace(':','.')
            case.setAttributeNS(self._NS, 'name', self._name + ':' + name)

    def get_cases(self, mode="long"):
        """@brief Returns the cases inside the BPTS

        @param mode long case identifier (file:case) or short, with just the
        name.
        @returns The cases inside the BPTS.
        """
        prename = self._name if mode == "long" else ""
        return [prename + ':' + case for case in self._cases]

    def get_round_cases(self, mode="long"):
        """@brief Returns a list with the cases with more than one execution.

        @param mode long case identifier (file:case) or short, with just the
        name.
        """
        prename = self._name if mode == "long" else ""
        return [prename + ':' + case for case in self._round_cases.keys]

    def get_case_delay(self, name, mode="long"):
        """@brief Returns the delay sequence of a given case.

        @param mode The type of the given case name.
        long case identifier (file:case) or short, with just the
        name.
        @returns A string with the delay sequence of the given case or None if
        the case doesn't exists or not have delaySequence element.
        """
        name += "" if mode == "long" else self._name
        try:
            return self._round_cases[name]
        except KeyError:
            return None

    def get_bpts_name(self):
        """@returns Returns the bpts name"""
        return self._bpts_name

    def set_bpts_name(self, name):
        """@brief Sets the bpts name"""
        self._bpts_name = name

    def get_url(self):
        """@returns The actual connection url"""
        return self.url

    def set_url(self, url):
        """@brief Set the connection url

        @param url The url to connect with the test server.
        """
        self.url = url

    def autodeclare(self):
        """@brief Autodeclare namespaces for BPTS"""
        self._autodeclare(self._dom.\
                          getElementsByTagNameNS(self._NS, 'testCases')[0])

    def copy_info(self, other, dep_dir):
        """@brief Copy connection info from other BPTSFile

        @param other opened BPTSFile object
        @param dep_dir Name of the dependences directory in the proyect
        """
        # Set wsdl and partners and declare new namespaces found in other.
        self._set_dom_wsdl(other._get_dom_wsdl())
        self._set_dom_partners(other._get_dom_partners(), dep_dir)
        self._set_dom_namespaces(other._get_dom_namespaces())

    def save(self):
        """@brief Overload the inherit save. Syncs the dom and the object and
        serializes the bpts."""
        self._sync_data()
        self.serialize()

    ## @name Internal
    ## @{

    def _update_data(self):
        """@brief Reads the bpts and get connection data

        Initializes internal attributes.
        """
        self._bpts_name = self._get_dom_name()
        self._bpts_url = self._get_dom_url()

    def _update_cases(self):
        """@brief Reads the bpts and get all cases.

        Initializes internal lists with cases, round cases and attachs.
        """
        self._cases = []
        self._round_cases.clear()
        self._attach.clear()

        dom_cases = self._dom.getElementsByTagNameNS(self._NS, 'testCase')
        dom_delays = []

        # Find cases
        for case in dom_cases:
            case_name = case.getAttributeNS(self._NS, 'name')
            case_name = case_name.split(':')
            if len(case_name) != 2 :
                case_name = "".join(case_name)
                log.warning(_('idg.bptsfile.bpts.case.name.incorrect.normalize') +
                            case_name)
            else:
                case_name = case_name[0]
            case.setAttributeNS(self._NS, 'name', case_name)
            self._cases.append(case_name)

        # Find send elements with delaySequence attributes
        #   and add it to the dict.
        for s in self._dom.getElementsByTagNameNS(self._NS, 'send'):
            if s.hasAttributeNS(self._NS, 'delaySequence'):
                delay = s.getAttributeNS(self._NS, 'delaySequence')
                p = self._get_parent(s, 'testCase')
                if p is not None:
                    name = p.getAttributeNS(self._NS, 'name')
                    self._round_cases[name] = delay

        # Find dataSource elements with attachments
        #  and add it to the dict.
        dom_case_attach = self._dom.getElementsByTagNameNS(self._NS,\
                                                          'dataSource')
        for a in dom_case_attach:
            case = self._get_parent(a, 'testCase')
            src = a.getAttributeNS(self._NS, 'src')
            type = a.getAttributeNS(self._NS, 'type')
            if case not in self._attach:
                self._attach[case] = []

            self._attach[case].append((src, type))

    def _sync_data(self):
        """@brief Syncs the object state with the dom object"""
        self._set_dom_name(self._bpts_name)
        self._set_dom_url(self._bpts_url)


    def _get_dom_testSuite_son(self, name):
        """@returns testSuite child dom object.

        @param name The name of the element to find inside testSuite.
        """
        return self._get_dom_testSuite.\
                getElementsByTagNameNS(self._NS, name)

    def _get_baseURL(self):
        """@returns the baseURL dom element"""
        try:
            return self._dom.getElementsByTagNameNS(self._NS, 'baseURL')[0]
        except:
            return None

    def _get_dom_testSuite(self):
        """@returns testSuite element dom object"""
        return self._dom.getElementsByTagNameNS(self._NS, 'testSuite')[0]


    def _get_dom_name(self):
        """@returns Returns the name value of the name attribute"""
        return self._dom.getElementsByTagNameNS(self._NS, 'name')[0].nodeValue

    def _set_dom_name(self, name):
        """@brief Establishes the name attribute of the bpts

        @param name The new bpts name.
        """
        self._dom.getElementsByTagNameNS(self._NS, 'name')[0].\
                setAttributeNS(self._NS, 'name', name)


    def _get_dom_url(self):
        """@returns the complete url for connection"""
        return self._get_baseURL().nodeValue

    def _set_dom_url(self, url):
        """@brief Set the complete conection url"""
        self._get_baseURL().nodeValue = url


    def _get_dom_wsdl(self):
        """@returns The wsdl dom object"""
        return self._get_dom_testSuite().\
                getElementsByTagNameNS(self._NS, 'wsdl')[0].nodeValue

    def _set_dom_wsdl(self, value):
        """@brief Sets the wsdl dom values

        @param value The wsdl value with the pat to the wsdl dependence.
        """
        self._get_dom_testSuite().\
                getElementsByTagNameNS(self._NS, 'wsdl')[0].nodeValue = value


    def _get_dom_partners(self):
        """@returns A list with the dom objects of the partner elements."""
        return self._get_dom_testSuite().\
                getElementsByTagNameNS(self._NS, 'partner')

    def _set_dom_partners(self, partners, dep_dir):
        """@brief Adds new partners to the bpts

        @param partners List of partners.
        @parma Name of the dependences dir in the proyect.
        """
        deploy = self._get_dom_testSuite().\
                getElementsByTagNameNS(self._NS, 'deployment')[0]

        for p in partners:
            # Add the namespace prefix manually --------vv
            sub = self._dom.createElementNS(self._NS, 'tes:partner')

            sub.setAttributeNS(self._NS, 'name', p.getAttribute('name'))
            sub.setAttributeNS(self._NS, 'wsdl',\
                               path.join(dep_dir, p.getAttribute('wsdl')))
            deploy.appendChild(sub)

    def _get_dom_namespaces(self):
        """@brief Returns a dict with the prefixes and namespaces
        { pre: uri, ..}

        Omits namespaces with "" or None as prefix or uri.
        """
        dict = {}
        [dict.setdefault(prefix, uri) for prefix, uri
         in self._get_dom_testSuite().attributes.items()
         if uri and prefix]

        return dict

    def _set_dom_namespaces(self, dict):
        """@brief Adds the namespaces declaration given in dict with the form
        of { pre: uri, ..} and adds to the firs element bpts declaration

        @param dict declarations into a dictionary { prefix: uri, ..}
        """
        testSuite = self._get_dom_testSuite()
        for prefix, uri in dict.items():
            if not testSuite.hasAttribute(prefix):
                testSuite.setAttribute(prefix, uri)

    ## @}
