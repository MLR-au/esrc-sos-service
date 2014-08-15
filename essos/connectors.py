from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pyramid.httpexceptions import HTTPInternalServerError
import time
import logging
log = logging.getLogger('essos')

def MongoDBConnection(request):
    client = request.registry.app_config['mongodb']['client']
    db = request.registry.app_config['mongodb']['db']
    return client[db]

class MongoBackend:
    def __init__(self):
        pass

    def connect(self, conf):
        # set up the mongo connection
        try:
            self.client = MongoClient(conf['nodes'], replicaset=conf['replica_set'], w=conf['write_concern'])
            self.client.admin.authenticate(conf['user'], conf['pass'])
            log.debug("Connection to Mongo cluster instantiated.")
        except ConnectionFailure:
            log.error("Can't connect to MongoDB at this time. Check the cluster.")
            raise HTTPInternalServerError
