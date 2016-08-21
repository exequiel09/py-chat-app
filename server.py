#!/usr/bin/env python

# server.py
#
# Copyright(c) Exequiel Ceasar Navarrete <esnavarrete1@up.edu.ph>
# Licensed under MIT
# Version 1.0.1

import os
import sys
sys.path.insert(0, os.path.abspath('./server'))

from chatserver import ChatServer
from servergui import ServerGUI

app = ServerGUI()
app.setServer(ChatServer())
app.bootstrap('Server GUI')

