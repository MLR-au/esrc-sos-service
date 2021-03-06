import unittest
import paste.deploy

from pyramid import testing
from views import health_check
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPInternalServerError
)

import sys
import os
import os.path

from config import Config

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class HealthCheckViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()
        conf = Config(settings['app.config'])

        self.request.registry.app_config = conf.app_config

    def tearDown(self):
        testing.tearDown()

    def test_health_check(self):
        hc = health_check(self.request)
        self.assertEqual(hc, 'OK')
        

    def test_health_check_fails(self):
        self.request.registry.app_config['ldap']['servers'] = [ 'no host' ]
        with self.assertRaises(HTTPInternalServerError):
            hc = health_check(self.request)
