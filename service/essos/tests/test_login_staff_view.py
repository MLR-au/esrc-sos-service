import unittest
import paste.deploy

from pyramid import testing
from views import login_staff
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPInternalServerError
)

import sys
import os
import os.path

from config import Config
from connectors import CassandraBackend

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class HealthCheckViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()
        conf = Config(settings['app.config'])

        self.arguments = {
            'nodes': conf.app_config['cassandra']['nodes'],
            'user': conf.app_config['cassandra']['user'],
            'pass': conf.app_config['cassandra']['pass'],
            'keyspace': conf.app_config['cassandra']['keyspace']
        }
        c = CassandraBackend(self.arguments)

        self.request.registry.app_config = conf.app_config
        self.request.registry.app_config['cassandra']['session'] = c.session

    def tearDown(self):
        testing.tearDown()

    def test_login_view(self):
        self.request.POST = {
            'username': 'u1',
            'password': 'p1'
        }

        with self.assertRaises(HTTPFound):
            l = login_staff(self.request)

        self.request.GET = {
            'r': 'https://orhm.esrc.info'
        }
        with self.assertRaises(HTTPFound):
            l = login_staff(self.request)

    def test_bad_logins(self):
        self.request.POST = {
            'username': 'u',
            'password': 'p1'
        }
        with self.assertRaises(HTTPFound):
            l = login_staff(self.request)


        self.request.GET = {
            'r': 'https://orhm.esrc.info'
        }
        with self.assertRaises(HTTPFound):
            l = login_staff(self.request)

