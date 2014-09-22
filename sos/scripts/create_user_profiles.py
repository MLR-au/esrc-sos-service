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
import random
import string

import os
here = os.getcwd()
settings = paste.deploy.appconfig('config:' + os.path.join(os.path.dirname(here), 'development.ini'))

char_set = string.ascii_letters + string.digits

conf = Config(settings['app.config'])
arguments = {
    'nodes': conf.app_config['cassandra']['nodes'],
    'user': conf.app_config['cassandra']['user'],
    'pass': conf.app_config['cassandra']['pass'],
    'keyspace': conf.app_config['cassandra']['keyspace']
}
c = CassandraBackend(arguments)
session = c.session

def get(n):
    sample = ''.join(random.sample(char_set, n))
    return sample

orm = ORM(session)
for i in range(0, 200):
    uid = uuid.uuid4()
    username = get(5)
    fullname = username + ' ' + get(20)
    email = username + '@example.com'

    orm.insert('profile_by_id',
        fields = [ 'id', 'username', 'fullname', 'primary_email' ],
        data = [ uid, username, fullname, email ]
    )
    orm.insert('profile_by_name',
        fields = [ 'username', 'id' ],
        data = [ username, uid ]
    )
    orm.insert('profile_by_email',
        fields = [ 'email', 'id' ],
        data = [ email, uid ]
    )

