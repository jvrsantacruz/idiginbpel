# BPTS File abstractions
# -*- coding: utf-8 -*-

import os.path as path

from file import XMLFile
import util.logger

log = util.logger.getlog('idg.bptsfile')

class TestCase(object):
    """@brief Test case representation"""

    ## Name of the case (long)
    _name = ""
    ## List with the path to related files [ (path, type), ...]
    _attachs = []
    ## String with the case delays sequence
    _delays = ""

    def __init__(self, bpts, dom):
        """@brief Initialize the case.

        @param bpts BPTSFile parent of the case.
        @param dom TestCase dom object with the case (minidom).
        """
        # Check dom element
        if not dom.hasAttribute('name') or not dom.localName == 'testCase':
            log.error(_('idg.bptsfile.test.case.invalid.dom'))
            raise ""

        self._dom = dom
        self._bpts = bpts

        # Get name, attachs and delays
        self._name = dom.getAttribute('name')
        self._find_attachs()
        self._find_delays()

        # If normalized, we only get the test case name
        if self.is_normalized():
            self._name = self._name.split(':')[1]

    def is_normalized(self):
        """@brief Check if the case name is already normalized

        @returns Fale if the format is wrong. None if the file name prefix is
        wrong.
        """
        name = self._dom.getAttribute('name').split(':')
        if len(name) != 2:
            return False

        if name[0] != self.bpts.name():
            return None

    def normalize(self):
        """@brief Normalize the test case name using proyect conventions

        The test case names have a long format FILE:CASE instead of just CASE
        The function will check if the names are already normalized. In that
        case, will do nothing.
        """
        norm = self.is_normalized()
        if norm is False:
            self._name.replace(':', '.')

        if norm is None:
            self._name = self._name.split(':')[1]

        self._dom.setAttribute('name', self.bpts.name() + ':' + self._name)

    def name(self, mode="long"):
        """@returns The name of the test case.

        @param mode long/short mode if the case name is normalized.
        """
        return (self.bpts.name() if mode == "long" else "") + self._name

    def has_attachs(self):
        """@returns If the test case have attachments"""
        return len(self._attachs) != 0

    def get_attachs(self):
        """@returns The list of attachments [(path, type), ..]"""
        return self._attachs

    def has_delays(self):
        """@returns If the test case have delay sequence."""
        return self._delays != ""

    def get_delays(self):
        """@returns A string with the delay sequence."""
        return self._delays

    ## @name Internal
    ## @{

    def _find_attachs(self):
        """@brief Internal function that finds attachs paths"""

        # Clear attach list
        self._attachs = []

        # Find dataSource elements with attachments
        dom_attachs = self._dom.getElementsByTagNameNS(BPTSFile._NS,\
                                                          'dataSource')
        for att in dom_attachs:
            src = att.getAttribute('src')
            type = att.getAttribute('type')
            self._attachs.append((src, type))

    def _find_delays(self):
        """@brief Internal function that finds delaySequences"""
        # Find cases with send elements with delaySequence attributes
        #   and add it to the dict.
        send = self._dom.getElementsByTagNameNS(BPTSFile._NS, 'send')
        if send and send[0].hasAttribute('delaySequence'):
            self._delays = send[0].getAttribute('send')
        else:
            self._delays = ""

    ## @}

class BPTSFile(XMLFile):
    """@brief BPTS test case file common operations"""

    ## Cases list (short case names)
    _cases = []

    ## Round Test Cases list (cases with rounds)
    _round_cases = []

    ## Test Cases with Related files list
    _attach_cases = []

    ## BPTS Namespace
    _NS ='http://www.bpelunit.org/schema/testSuite'

    ## get info copied flag.
    _copied_info = False

    def __init__(self, path_):
        """@brief Initialize and open the BPTS file.

        @param path_ The path to the bpts file.
        """
        XMLFile.__init__(self, path_)
        # Open the file with Minidom
        self.open('md')
        self._update_data()
        self._update_cases()

    def normalize(self):
        """@brief Normalize the btps names to idiginBPEL internal proyect
        conventions.

        Changes the name of the cases up to 'file:case'
        """
        [case.normalize() for case in self._cases]
        #for case in self._dom.getElementsByTagNameNS(self._NS, 'testCase'):
        #    name = case.getAttribute('name').replace(':','.')
        #    case.setAttribute('name', self._name + ':' + name)

    def get_cases(self):
        """@returns Returns the test cases inside the BPTS"""
        return self._cases

    def get_round_cases(self, mode="long"):
        """@brief Returns a list with the cases with more than one execution.

        @param mode long case identifier (file:case) or short, with just the
        name.
        """
        return self._round_cases

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
        """@brief Autodeclare namespaces for BPTS

        Override XMLFile version
        """
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
        domcase = self._dom.getElementsByTagNameNS(self._NS, 'testCase')
        try:
            case = TestCase(self, domcase[0])
        except:
            log.error('EXCEPTIOOONRL!!!!!!')
            traceback.print_exc()

        self._cases = [TestCase(self, domcase) for domcase in\
                           self._dom.getElementsByTagNameNS(self._NS, 'testCase')]
        self._round_cases = [c for c in self._cases if c.has_delays()]
        self._attach_cases = [c for c in self._cases if c.has_attachs()]

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
                setAttribute('name', name)


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

            sub.setAttribute('name', p.getAttribute('name'))
            sub.setAttribute('wsdl',path.join(dep_dir, p.getAttribute('wsdl')))
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
