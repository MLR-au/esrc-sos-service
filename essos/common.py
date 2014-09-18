from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPOk,
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden,
    HTTPUnauthorized
)
from pyramid.response import Response
import logging
log = logging.getLogger('essos')

import ast
import os
from urlparse import urlparse
from connectors import MongoDBConnection as mdb

from config import AppsConfig

def get_app_data(request):
    app_configs = os.path.join(os.path.dirname(request.registry.settings['app.config']), request.registry.app_config['general']['apps'])
    apps = []
    for f in os.listdir(app_configs):
        c = AppsConfig(os.path.join(app_configs, f))
        d = c.load()
        apps.append(d)
    return apps

def verify_caller(request, r):
    authed_app = False
    if r is not None:
        apps = get_app_data(request)
    
        for app in apps:
            if compare(r, app.url):
                authed_app = True

    return authed_app

def get_login_callback(request, r):
    apps = get_app_data(request)
    for app in apps:
        if compare(r, app.url):
            return app.login_callback

def compare(a, b):
    # expects a couple of urls - urlparse will be used to 
    #  split the components for comparison
    a = urlparse(a)
    b = urlparse(b)
    if a.scheme == b.scheme and a.netloc == b.netloc and a.path == b.path:
        return True
    else:
        return False

def lockout_ip(request):
    db = mdb(request)
    doc = db.lockout.find_one( { 'ip': request.client_addr })
    if doc is not None:
        pass
    else:
        db.lockout.insert({
            'ip':  request.client_addr,
            'attempts': [ datetime.utcnow() ]
        })
    
    
