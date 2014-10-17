from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPOk,
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden,
    HTTPUnauthorized
)
import ast
import jwt 
import Crypto.PublicKey.RSA as RSA
import json
import traceback

import auth
import time
import uuid
import os
import os.path
import sys
from datetime import datetime, timedelta, date

import logging
log = logging.getLogger(__name__)

import velruse

from pymongo.errors import (
    OperationFailure
)
import pymongo

from config import AppsConfig
from common import *

@view_config(route_name="health_check", request_method="GET", renderer="string")
def health_check(request):
    """ """
    # can we connect to an LDAP server
    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    if ldap.conn is None:
        raise HTTPInternalServerError

    # do we have a working connection to mongo
    try:
        db = mdb(request)
        doc = db.health_check.find_one()
    except:
        raise HTTPInternalServerError

    log.info('LDAP and Mongo cluster seem to be in working order.')
    return 'OK'

@view_config(route_name='home', request_method="GET", renderer='templates/home.mak')
def home(request):
    """The login page

    @method: GET
    @params:
    - GET: r - the redirect URL (the calling app)
    - GET: e - whether the user login failed
    
    """
    # get the url params
    #  if not r param: raise HTTPForbidden

    #  validate the r param: raise HTTPForbidden if not in allowed list

    # get the URL params; these will be blank if unset
    r = request.GET.get('r')
    e = request.GET.get('e')

    if r == None:
        log.error("%s: No redirect URL specified. Raising HTTPForbidden." % request.client_addr)
        raise HTTPForbidden

    # is the redirecting app authorised? if not - redirect to home
    verify_caller(request, r)

    # store the name of the requested app - we need to redirect to it
    request.session['r'] = r

    try:
        # if REMOTE_ADDR is not set in the environment then we have to wonder what the
        #  hell is going in. So - if we get an exception here, then the except clause
        #  is to raise a forbidden error.
        log.info("%s: Login redirect from: '%s'" % (request.client_addr, r))
        return { 'r': r, 'e': e }
    except:
        log.error("%s: Something wrong. Raising HTTPForbidden just in case." % request.client_addr)
        raise HTTPForbidden

@view_config(route_name='login_staff', request_method="POST", renderer='json')
def login_staff(request):
    """Handle a staff login against LDAP

    HTTPForbidden raised if any params missing.

    @method: POST
    @params:
    - POST: username, 
    - POST: password
    - POST: r
    """
    log.info("%s: Staff login attempted" % request.client_addr)
    if (not request.POST.get('username') or not request.POST.get('password')):
        log.error("%s: POST missing username and / or password." % request.client_addr)
        raise HTTPForbidden

    if not request.POST.get('r'):
        log.error("%s: POST missing redirect url." % request.client_addr)
        raise HTTPForbidden
    r = request.POST.get('r')

    # is the redirecting app authorised? if not - redirect to home
    verify_caller(request, r)

    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    result = ldap.authenticate(request.POST['username'], request.POST['password'])

    # if 'not result' means they didn't auth successfully so send
    #  them back to the start (to try again) with a marker (e=True)
    #  to flag that something is wrong.
    if not result:
        log.error("%s: Login failed for: %s." % (request.client_addr, request.POST['username']))
        raise HTTPFound("/?r=%s&e=True" % r)

    # if we get to here then the user has auth'ed successfully
    # grab the user data
    user_data = ldap.get_user_data()

    # is the user actually allowed to access this app?
    allowed = False
    app_groups_allowed = get_app_allow(request, r)
    for g in user_data.groups:
        if g in app_groups_allowed:
            allowed = True

    # handle the login
    if allowed:
        log.info("%s: User '%s' granted access to '%s'. " % (request.client_addr, request.POST['username'], r))
        otc = create_session(request, user_data.username, user_data.fullname, user_data.email, user_data.groups)
        access_allowed(request, r, otc)
    else:
        log.info("%s: User '%s' denied access to '%s'." % (request.client_addr, request.POST['username'], r))
        access_denied(request, r)

@view_config(context='velruse.providers.google_oauth2.GoogleAuthenticationComplete')
def google_login_complete(request):
    session = request.session
    context = request.context
    #for k, v in context.profile.items():
    #    print k, v

    username = context.profile['verifiedEmail']
    fullname = context.profile['displayName']

    # verify the user has a profile - raise forbidden otherwise
    db = mdb(request)

    log.info("%s: Google Login. Looking for profile with email '%s'" % (request.client_addr, username))
    doc = db.profiles.find_one({ '$or': [
        { 'primaryEmail': username }, { 'secondaryEmail': username }
    ]})
    if doc is None:
        access_denied(request, request.session['r'])

    # get app data
    app = get_app_name(request, request.session['r'])

    # if app is None - then a social user is trying to access the sign on service
    #  management app and that's a no no.
    if app is None:
        access_denied(request, request.session['r'])

    if doc['apps'][app] == 'allow':
        # verify user allowed to use app - redirect to forbidden otherwise
        # check user account not locked
        if doc['status'] != 'locked':
            # create session and get on with it
            otc = create_session(request, username, fullname, username)
            access_allowed(request, request.session['r'], otc)

    # if we get to here for any reason - access has been denied
    access_denied(request, request.session['r'])

@view_config(context='velruse.providers.linkedin.LinkedInAuthenticationComplete')
def linkedin_login_complete(request):
    session = request.session
    context = request.context
    #for k, v in context.profile.items():
    #    print k, v

    username = context.profile['emails'][0]['value']
    fullname = context.profile['name']['formatted']

    # verify the user has a profile - raise forbidden otherwise
    db = mdb(request)

    log.info("%s: LinkedIn Login. Looking for profile with email '%s'" % (request.client_addr, username))
    doc = db.profiles.find_one({ '$or': [
        { 'primaryEmail': username }, { 'secondaryEmail': username }
    ]})
    if doc is None:
        access_denied(request, request.session['r'])

    # get app data
    app = get_app_name(request, request.session['r'])

    # if app is None - then a social user is trying to access the sign on service
    #  management app and that's a no no.
    if app is None:
        access_denied(request, request.session['r'])

    if doc['apps'][app] == 'allow':
        # verify user allowed to use app - redirect to forbidden otherwise
        # check user account not locked
        if doc['status'] != 'locked':
            # create session and get on with it
            otc = create_session(request, username, fullname, username)
            access_allowed(request, request.session['r'], otc)

    # if we get to here for any reason - access has been denied
    access_denied(request, request.session['r'])

def create_session(request, username, fullname, email, groups=None):
    # grab a handle to the database
    db = mdb(request)

    # ensure we have the required indexes on username and token
    db.session.ensure_index('username', pymongo.ASCENDING)
    db.session.ensure_index('token', pymongo.ASCENDING)
    db.code.ensure_index('token', pymongo.ASCENDING)
    db.code.ensure_index('code', pymongo.ASCENDING)

    # is there already a session? if so - generate a code for that and return it
    doc = db.session.find_one({ 'username': username })
    try:
        # there's an existing session - generate a code for it and return that
        token = doc['token']
        log.info("%s: Found existing session for '%s'." % (request.client_addr, username))

    except:
        log.info("%s: Creating a new session for '%s'." % (request.client_addr, username))
        # create a session for the user 
        session_lifetime = int(request.registry.app_config['general']['session.lifetime'])
        token = str(uuid.uuid4()).replace('-', '')

        # check to confirm that there isn't already a session with this id in the db
        doc = db.session.find_one({ 'token': token })
        if doc is not None:
            token = str(uuid.uuid4()).replace('-', '')

        db.session.insert({
            'username': username,
            'fullname': fullname,
            'email': email,
            'token': token,
            'groups': groups,
            'createdAt': datetime.utcnow()
        })
        ### in order for the document to expire the indexed field must be a 
        ###  UTC timestamp. See pymongo docs for createIndex, ensureIndex
        ### http://api.mongodb.org/python/current/api/pymongo/collection.html
        try:
            db.session.ensure_index('createdAt', expireAfterSeconds = session_lifetime)
        except OperationFailure:
            db.session.drop_index('createdAt_1')
            db.session.ensure_index('createdAt', expireAfterSeconds = session_lifetime)
    
    log.info("%s: Looking up the session to see if there's already a one time code tied to it." % request.client_addr)
    doc = db.code.find_one({ 'token': token })
    try:
        otc = doc['code']
    except:
        log.info("%s: Generating new one time code." % request.client_addr)
        otc = str(uuid.uuid4()).replace('-', '')
        db.code.insert({
            'token': token,
            'code': otc,
            'createdAt': datetime.utcnow()
        })
        try:
            db.code.ensure_index('createdAt', expireAfterSeconds = 5)
        except OperationFailure:
            db.code.drop_index('createdAt_1')
            db.code.ensure_index('createdAt', expireAfterSeconds = 5)

    # return one time code to the caller
    return otc

def access_allowed(request, r, otc):
    login_callback = get_login_callback(request, r)
    log.info("%s: Returning one time code to: %s." % (request.client_addr, r))
    raise HTTPFound("%s/%s" % (login_callback, otc))

def access_denied(request, r):
    log.info("%s: User not allowed to use this application: %s" % (request.client_addr, r))
    forbidden_callback = get_forbidden_callback(request, r)
    raise HTTPFound("%s" % (forbidden_callback))

@view_config(context='velruse.AuthenticationDenied', renderer="denied.mak")
def login_denied_view(request):
    log.info("%s: Social login denied." % request.client_addr)
    raise HTTPUnauthorized

@view_config(route_name="retrieve_token", request_method="GET", renderer='json')
def retrieve_token(request):
    """Retrieve a token with the one time code

    @method: GET
    @params:
    - GET: code: the one time code
    - GET: r: the calling app

    @returns
    - JSON Web Token
    """
    # is the code valid?
    code = request.matchdict.get('code')
    if code == None:
        log.error("%s: No code supplied. Raising HTTPUnauthorized" % request.client_addr)
        raise HTTPUnauthorized

    # Is the caller allowed?
    r = request.GET.get('r')
    verify_caller(request, r)

    log.info("%s: Retrieve token for '%s'" % (request.client_addr, code))

    # grab a handle to the database
    db = mdb(request)

    # use the code to lookup the token
    doc = db.code.find_one({ 'code': code })

    if doc is None:
        # no document found for code
        log.info("%s: Code: %s not found. Raising Unauthorized" % (request.client_addr, code))
        raise HTTPUnauthorized

    # delete the code
    log.info("%s: Found token. Removing OTC" % request.client_addr)
    db.code.remove({ 'code': code })

    # use the token to get the user data
    token = doc['token']

    doc = db.session.find_one({ 'token': token })
    if doc is None:
        # no document found for token
        log.info("%s: Couldn't find session for token. Raising Unauthorized." % request.client_addr)
        raise HTTPUnauthorised

    # load the pub and private keys
    path = os.path.dirname(request.registry.settings.get('app.config'))
    config = request.registry.app_config['general']

    f = open(os.path.join(path, config['jwt.priv']), 'r')
    private_key = f.read()
    f.close()

    private_key = RSA.importKey(private_key)
    #print dir(private_key)

    admins = get_app_admins(request, r)
    is_admin = False
    if doc['groups'] is not None:
        for g in doc['groups']:
            if g in admins:
                is_admin = True

    user_data = {
        'fullname': doc['fullname'],
        'email': doc['email'],
        'admin': is_admin,
        'token': doc['token']
    }


    # generate the jwt
    session_lifetime = int(request.registry.app_config['general']['session.lifetime'])
    log.info("%s: Creating JWT for '%s'." % (request.client_addr, user_data['fullname']))
    token = jwt.generate_jwt(user_data, private_key, 'PS256', timedelta(seconds=session_lifetime))

    log.info("%s: Returning JWT." % request.client_addr)
    return token

@view_config(route_name="validate_token", request_method="GET", renderer='json')
def validate_token(request):
    """Validate a token

    Returns claims from token if token verifies successfully.

    @params:
    - None
    """
    log.info("%s: Validate token method called." % request.client_addr)

    # verify the token and session
    claims = verify_token(request)

    log.info("%s: Token for '%s (%s)' valid. Session still ok." % (request.client_addr, claims['fullname'], claims['email']))
    return { 'claims': claims }


