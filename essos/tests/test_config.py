import unittest
import paste.deploy

from pyramid import testing
import sys
import os
import os.path

from config import Config, AppsConfig
from models import *
import time
from datetime import datetime, date
import uuid

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        conf = Config(settings['app.config'])
        self.conf = conf.app_config

    def tearDown(self):
        testing.tearDown()

    def test_config(self):
        self.assertTrue(self.conf.has_key('general'))
        self.assertTrue(self.conf.has_key('ldap'))

    def test_app_configs(self):
        app_configs = os.path.join(os.path.dirname(settings['app.config']), self.conf['general']['apps'])
        for f in os.listdir(app_configs):
            c = AppsConfig(os.path.join(app_configs, f))
            d = c.load()
            if f == 'cnex':
                self.assertEqual(d.name, 'Contextual Network Explorer')
