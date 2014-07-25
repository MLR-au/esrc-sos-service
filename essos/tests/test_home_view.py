import unittest
import paste.deploy
import collections

from pyramid import testing
from views import home
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden
)

import sys
import os
import os.path
from config import Config

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class HomeViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()
        self.request.registry.settings['app.config'] = settings['app.config']
        conf = Config(settings['app.config'])
        self.request.registry.app_config = conf.app_config

    def tearDown(self):
        testing.tearDown()

    def test_home(self):

        with self.assertRaises(HTTPForbidden):
            h = home(self.request)

        self.request.environ = {
            'REMOTE_ADDR': '192.168.190.23'
        }
        h = home(self.request)
        self.assertEqual(h['r'], '')

        self.request.GET = {
            'r': 'https://ohrm.esrc.info'
        }
        with self.assertRaises(HTTPFound):
            h = home(self.request)

        self.request.GET = {
            'e': True
        }
        h = home(self.request)
        self.assertEqual(h['e'], True)
        
