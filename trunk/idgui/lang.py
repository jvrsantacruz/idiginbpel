# -*- coding: utf-8 -*-
# Traducción

import gettext
import os

trans_domain = "idgui"
locale_dir = os.path.abspath('../locale')
gettext.install(trans_domain, locale_dir)
