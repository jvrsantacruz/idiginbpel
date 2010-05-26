# BPTS File abstractions
# -*- coding: utf-8 -*-

import os.path as path
import copy

from file import XMLFile
import util.logger

log = util.logger.getlog('idg.bptsfile')

class Attach(object):
    """@brief File attached to a TestCase"""

    ## Properties of the attached file.
    _properties = {}
    ## Path to the attached file.
    _path = None
    ## Attach type
    _type = None
    ## Dom representation
    _dom = None
    ## Related Test Case
    _case = None

    def __init__(self, dom, case):
        """@brief Initialize an attach

        @param dom The minidom dataSource node
        @param case TestCase instance
        """
        self._dom = dom
        self._path = dom.getAttribute('src')
        self._type = dom.getAttribute('type')

        for prop in dom.getElementsByTagNameNS(BPTSFile._NS, 'property'):
            self._properties[prop.getAttribute('name')] = prop.nodeValue

    def rm(self):
        """@brief Remove the attach from dom"""
        self._dom.parentNode.removeChild(self._dom)

    def src(self):
        """@brief Returns attach src"""
        return self._path

    def type(self):
        """@brief Returns attach type"""
        return self._type

    def properties(self):
        """@brief Returns attach properties into a dict {name: value}"""
        return self._properties

class TestCase(object):
    """@brief Test case representation"""

    ## Name of the case (long)
    _name = ""
    ## List with Attach objects
    _attachs = []
    ## String with the case delays sequence
    _delays = ""
    ## Asociated BPTSFile
    _bpts = None

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

        # Find dom attributes
        self._send_dom = dom.getElementsByTagNameNS(BPTSFile._NS, 'send')

        # Get name, attachs and delays
        self._name = dom.getAttribute('name')
        self._find_attachs()
        self._find_delays()

        # If normalized, we only get the test case name
        if self.is_normalized():
            self._name = self._name.split(':')[1]

    def __str__(self):
        """@returns The long name of the case"""
        if self.is_normalized is None:
            return self._name
        else:
            return self._bpts.name() + ':' + self._name

    def is_normalized(self):
        """@brief Check if the case name is already normalized

        @returns Fale if the format is wrong. None if the file name prefix is
        wrong.
        """
        name = self._dom.getAttribute('name').split(':')
        if len(name) != 2:
            return False

        if name[0] != self._bpts.name():
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

        self._dom.setAttribute('name', self._bpts.name() + ':' + self._name)

    def name(self, mode="long"):
        """@returns The name of the test case.

        @param mode long/short/file mode if the case name is normalized.

        Formats:
            short namecase
            file  namefile
            long  namefile:namecase
        """
        # If the case was previously normalized in another file but not in this
        # file, is_normalized will return None
        norm = self.is_normalized() is not None
        spname = self._name.split(':')
        filename = self._bpts.name() if norm else spname[0]
        casename = self._name if norm else spname[1]

        if mode == "long":
            return filename + casename
        elif mode == "file":
            return filename
        else:
            return casename

    def file(self):
        """@returns The bpts file"""
        return self._bpts

    def has_attachs(self):
        """@returns If the test case have attachments"""
        return len(self._attachs) != 0

    def get_attachs(self):
        """@returns The list of attachments"""
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

        for a in self._dom.getElementsByTagNameNS(BPTSFile._NS, 'dataSource'):
            self._attachs.append(Attach(a,self))

    def _set_attach(self, attach):
        """@brief Append a new attachment to the case

        @param attach Attach object to add.
        """
        # Append a new attachment
        a_dom = attach._dom.cloneNode()
        self._send_dom.appendChild(a_dom)
        self._attachs.append(Attach(a_dom))

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

    ## Test Cases list
    _cases = []

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
        dom = self.open('md')
        if dom is None:
            raise ""
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

    def add_case(self, dom):
        """@brief Adds a new case to the bpts"""
        self._cases.append(TestCase(self, dom))

        # Remove from old tree and add to this bpts
        #dom.parentNode.removeChild(dom)
        self._get_dom_testcases.appendChild(dom)

    def rm_case(self, name):
        """@brief Removes a case from the bpts"""
        cases = [case for case in self._cases if str(name) == name]

        # Remove from dom and delete from cases
        for c in cases:
            c._dom.parentNode.removeChild(c)
            del c

    def rm_all(self):
        """@brief Removes all cases from the bpts"""
        [self.rm_case(str(c)) for c in self._cases]

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
        self._autodeclare(self._get_dom_testcases())

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

        self._cases = [TestCase(self, domcase) for domcase in\
                self._dom.getElementsByTagNameNS(self._NS, 'testCase')]

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

    def _set_dom_name(self, value):
        """@brief Establishes the name attribute of the bpts

        @param value The new bpts name.
        """
        name = self._dom.getElementsByTagNameNS(self._NS, 'name')[0]
        self._set_text(name, value)

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
        wsdl = self._get_dom_testSuite().\
                getElementsByTagNameNS(self._NS, 'wsdl')[0]
        self._set_text(wsdl, value)

    def _get_dom_testcases(self):
        """@returns the dom testCases"""
        return self._dom.getElementsByTagNameNS(self._NS, 'testCases')[0]


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
