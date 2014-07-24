import unittest
import paste.deploy

from pyramid import testing
import sys
import os
import os.path

from config import Config
from connectors import CassandraBackend
import cassandra
from models import *
import time
from datetime import datetime, date
import uuid

import os
here = os.path.dirname(__file__)
settings = paste.deploy.appconfig('config:' + os.path.join(here, '../../', 'development.ini'))

class CassandraTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        conf = Config(settings['app.config'])
        self.arguments = {
            'nodes': conf.app_config['cassandra']['nodes'],
            'user': conf.app_config['cassandra']['user'],
            'pass': conf.app_config['cassandra']['pass'],
            'keyspace': conf.app_config['cassandra']['keyspace']
        }
        c = CassandraBackend(self.arguments)
        self.session = c.session

    def tearDown(self):
        testing.tearDown()

    def test_establish_session(self):
        c = CassandraBackend(self.arguments)
        session = c.session
        self.assertEqual(session.keyspace, self.arguments['keyspace'])
        self.assertIsInstance(session.cluster, cassandra.cluster.Cluster)

    def test_load_models(self):
        for t in [ 'session_by_token', 'session_by_name', 'health_check', ]:
            self.session.execute("DROP TABLE %s;" % t)
        m = Models(self.session)

    def test_orm_insert_bad_call(self):
        orm = ORM(self.session)
        t = 'dummy'
        d = 'dummy'
        with self.assertRaises(TypeError):
            orm.insert('session_by_token',
                fields = 'token',
                data = [ t, d ]
            )
        with self.assertRaises(TypeError):
            orm.insert('session_by_token',
                fields = [ 'token', 'username' ],
                data = "t and d" 
            )
        with self.assertRaises(ValueError):
            orm.insert('session_by_token',
                fields = [ 'token', 'userna,e' ],
                data = [ d ]
            )

    def test_orm_query_bad_call(self):
        orm = ORM(self.session)
        t = 'dummy'
        d = 'dummy'
        with self.assertRaises(TypeError):
            orm.query('session_by_token',
                fields = 'token',
                where = [ t, d ]
            )
        with self.assertRaises(TypeError):
            orm.query('session_by_token',
                fields = [ 'token', 'username' ],
                where= "t and d" 
            )
        
    def test_orm_insert(self):
        orm = ORM(self.session)

        t = uuid.uuid4()
        username = 'test'
        fullname = 'Test User'
        orm.insert('session_by_token',
            fields = [ 'token', 'fullname', 'username', 'is_admin' ],
            data = [ t, fullname, username, True]
        )
        orm.insert('session_by_name',
            fields = [ 'username', 'token' ],
            data = [ username, t ]
        )
        data = orm.query('session_by_token',
            [ 'token', 'username' ],
            [ '"token" = ' +  str(t) ]
        )
        self.assertEqual(1, len(data))
        for row in data:
            self.assertEqual(t, row.token)
            self.assertEqual(username, row.username)

        data = orm.query('session_by_name',
            [ 'token' ],
            [ '"username" = \'mlarosa\'' ]
        )
        for row in data:
            self.assertEqual(t, row.token)

    def test_orm_insert_with_ttl(self):
        orm = ORM(self.session)

        orm.insert('health_check',
            fields = [ 'date', 'timestamp', 'request_time' ],
            data = [ str(date.today()), datetime.utcnow(), 0.34],
            ttl = '30'
        )
        data = orm.query('health_check',
            fields = [ 'timestamp', 'request_time' ],
        ) 
        
