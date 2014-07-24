from cassandra import auth, policies
from cassandra.cluster import Cluster

import time

from models import Models

class CassandraBackend:
    def __init__(self, arguments):
        self.nodes = arguments['nodes']
        self.user = arguments['user']
        self.passwd = arguments['pass']
        self.keyspace = arguments['keyspace']

        auth_provider = auth.PlainTextAuthProvider(username=self.user, password=self.passwd)
        cluster = Cluster(self.nodes, auth_provider=auth_provider, executor_threads=len(self.nodes))
        cluster.set_core_connections_per_host(policies.HostDistance.LOCAL, 1)
        self.session = cluster.connect()
        self.session.set_keyspace(self.keyspace)

        # load the models - it's up to the model to handle exceptions gracefully
        m = Models(self.session)
