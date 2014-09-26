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
log = logging.getLogger(__name__)

import ast
import os
from urlparse import urlparse
from connectors import MongoDBConnection as mdb

import jwt
import Crypto.PublicKey.RSA as RSA
import json
import traceback

from config import AppsConfig

def get_app_data(request, except_social=False):
    app_configs = os.path.join(os.path.dirname(request.registry.settings['app.config']), request.registry.app_config['general']['apps'])
    apps = []
    for f in os.listdir(app_configs):
        c = AppsConfig(os.path.join(app_configs, f))
        d = c.load()
        if not (except_social and d.deny_social):
            apps.append(d)
    return apps

def verify_caller(request, r):
    authed_app = False

    # if r has been provided
    if r is not None:

        # does r match the referrer?
        if compare(r, request.referer):

            # is r known to us as an app
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

def get_forbidden_callback(request, r):
    apps = get_app_data(request)
    for app in apps:
        if compare(r, app.url):
            return app.forbidden_callback

def get_app_allow(request, r):
    apps = get_app_data(request)
    for app in apps:
        if compare(r, app.url):
            return app.allow

def get_app_admins(request, r):
    apps = get_app_data(request)
    for app in apps:
        if compare(r, app.url):
            return app.admins


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
    
def verify_token(request):

    # get the token or raise Unauthorized if none
    try:
        token = request.headers['Authorization']
        token = token.split()[1]
    except:
        log.debug("Couldn't get token from headers")
        raise HTTPUnauthorized

    # load the pub and private keys
    path = os.path.dirname(request.registry.settings.get('app.config'))
    config = request.registry.app_config['general']

    f = open(os.path.join(path, config['jwt.pub']), 'r')
    public_key = f.read()
    f.close()

    public_key = RSA.importKey(public_key)
    #print dir(public_key)

    # verify the jwt
    try:
        log.debug("Verifying JWT.")
        headers, claims = jwt.process_jwt(json.dumps(token))
        #log.debug(claims)
    except:
        log.debug("Couldn't verify JWT. Raising unauthorised.")
        raise HTTPUnauthorized

    # grab a handle to the database
    db = mdb(request)

    log.debug("Checking auth token still valid.")
    token = claims['token']
    doc =  db.session.find_one({ 'token': token })
    if doc is None:
        log.debug("No session found for auth token.")
        raise HTTPUnauthorized

    return claims

