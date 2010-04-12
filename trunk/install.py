#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Installs (or update) IdiginBPEL and Takuan
    use: install.py [idg|takuan|both]
"""

import os
import sys
import stat
import subprocess
import shutil
import urllib2 

import logging
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                    level = logging.DEBUG)
log = logging.getLogger("")

# Idiginbpel repository url
__IDG_REPO_URL__ = 'https://forja.rediris.es/svn/cusl4-idigin/tags/stable'

# Idiginbpel directory (where the code will be placed)
__IDG_NAME_DIR__ = 'IdiginBPEL'
__IDG_DIR__ = os.path.join(os.environ['HOME'], __IDG_NAME_DIR__)

# Idiginbpel user data directory path at home
__IDG_HOME_NAME_DIR__ = '.idiginbpel'
__IDG_HOME_DIR__ = os.path.join(os.environ['HOME'], __IDG_HOME_NAME_DIR__)

# Idiginbpel config file and user skel directory
__IDG_CONFIG__ = os.path.join(__IDG_DIR__, 'share', 'config.xml')

# Detect if is already installed
__IDG_INSTALLED__ = os.path.exists(__IDG_DIR__)
__IDG_INSTALLED_HOME__ = os.path.exists(__IDG_HOME_DIR__)

# Takuan install script name
__TAKUAN_SCRIPT__ = 'install_takuan.sh'
# Takuan install script url from FM repository
__TAKUAN_INSTALL_URL__ = 'https://neptuno.uca.es/redmine/projects/sources-fm/repository/raw/trunk/scripts/install.sh'

# Installation options ('idg', 'takuan', 'both')
# We accept to install only one of them in order to make updates
__INSTALL_OPTS__ = 'both'
__INSTALL_TAKUAN_FLAG__ = True
__INSTALL_IDG_FLAG__ = True

# Arguments with installation options
if len(sys.argv) > 1 :
    __INSTALL_OPTS__ = sys.argv[1]

    # Check the option
    if __INSTALL_OPTS__ not in ('idg', 'takuan', 'both') :
        log.error('Unkwown option: %s' % __INSTALL_OPTS__)
        log.info('install.py [idg|takuan|both]')
        sys.exit()

    __INSTALL_TAKUAN_FLAG__ = __INSTALL_OPTS__ != 'idg'
    __INSTALL_IDG_FLAG__ = __INSTALL_OPTS__ != 'takuan'


# The script itself ------------------------------ 

log.info('-------- IdiginBPEL installation ---------')
log.info('--------------    xxxxx   ----------------')
log.info('Installing at: %s' % os.environ['HOME'])
log.info('Installing Takuan: (%s)' % __INSTALL_TAKUAN_FLAG__)
log.info('Installing IdiginBPEL: (%s)' % __INSTALL_IDG_FLAG__)

if __INSTALL_IDG_FLAG__ :
    log.info('IdiginBPEL code at: %s' % __IDG_DIR__)
    log.info('IdiginBPEL user data dir at: %s' % __IDG_HOME_DIR__)

log.info("")

if __INSTALL_IDG_FLAG__ :

        # Download the Idiginbpel code from repository
    # if the directory already exists, just update
    log.info('Fetching the code from repository')
    if __IDG_INSTALLED__ :
        log.info('Updating an already installed version')
        cmd = ('svn', 'update') 
        cwd = __IDG_DIR__
    else:
        cmd = ('svn', 'checkout', __IDG_REPO_URL__, __IDG_NAME_DIR__)
        cwd = os.environ['HOME']

    log.info(cmd)

    if subprocess.call(cmd, cwd = os.environ['HOME']) != 0 :
        log.error("Can't download IdiginBPEL from the repository")

    # Create Idiginbpel user data directory 
    log.info('Creating user data dir: %s' % __IDG_HOME_DIR__)
    if not __IDG_INSTALLED_HOME__ :
        # Create user data directory 
        os.makedirs(os.path.join(__IDG_HOME_DIR__, 'proy'))

        # Configure. Copy config file 
        log.info('Generating a new config.xml at %s' % __IDG_HOME_DIR__)
        shutil.copy(__IDG_CONFIG__, __IDG_HOME_DIR__)
    else :
        log.warning('Idiginbpel user data directory already exists')

if __INSTALL_TAKUAN_FLAG__ :
    # Fetch the takuan install script
    log.info('Fetching the takuan install script from FM repository')
    log.info(__TAKUAN_INSTALL_URL__)
    try : 
        req = urllib2.urlopen(__TAKUAN_INSTALL_URL__)
    except :
        log.error("Can't fetch takuan install script at: %s" %
              __TAKUAN_INSTALL_URL__)
        sys.exit()

    # Write the script into a file
    try:
        f = open(__TAKUAN_SCRIPT__, 'w')
        f.write(req.read())
        f.close()
    except:
        log.error("Can't write the takuan install script into a file: %s"
                  % __TAKUAN_SCRIPT__)
        sys.exit()

    # Execution perms (0700)
    os.chmod(__TAKUAN_SCRIPT__, stat.S_IEXEC | stat.S_IWRITE | stat.S_IREAD)

    # Run the takuan install script
    log.info('Running takuan install script')
    cmd = ('./' + __TAKUAN_SCRIPT__, 'takuan')
    log.info(cmd)
    if subprocess.call(cmd) != 0 :
        log.error("Takuan script execution failed")
