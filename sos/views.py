from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPOk,
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden,
    HTTPUnauthorized
)
import ast

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

    # do we have a working connection to cassandra
    db = mdb(request)

    # add a trace into the health_check table
    try:
        doc = db.health_check.find_one({ 'name': 'hc' })
        db.health_check.remove(doc['_id'])
    except:
        pass
    db.health_check.insert({ 'name': 'hc' })

    log.debug('Mongo cluster seems to be in working order.')
    return 'OK'

@view_config(route_name='home', request_method="GET", renderer='templates/home.mak')
def home(request):
    """ """
    # get the url params
    #  if not r param: raise HTTPForbidden

    #  validate the r param: raise HTTPForbidden if not in allowed list

    # get the URL params; these will be blank if unset
    r = request.GET.get('r')
    e = request.GET.get('e')

    if r == None:
        raise HTTPForbidden

    # is the redirecting app authorised? if not - redirect to home
    if not verify_caller(request, r):
        raise HTTPForbidden

    try:
        # if REMOTE_ADDR is not set in the environment then we have to wonder what the
        #  hell is going in. So - if we get an exception here, then the except clause
        #  is to raise a forbidden error.
        log.info("Login redirect from: '%s', remote address: %s" % (r, request.environ['REMOTE_ADDR']))
        return { 'r': r, 'e': e }
    except:
        raise HTTPForbidden

@view_config(route_name='login_staff', request_method="POST", renderer='json')
def login_staff(request):
    if (not request.POST.get('username') or not request.POST.get('password')):
        raise HTTPForbidden

    if not request.POST.get('r'):
        raise HTTPForbidden
    r = request.POST.get('r')

    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    result = ldap.authenticate(request.POST['username'], request.POST['password'])


    # if 'not result' means they didn't auth successfully so send
    #  them back to the start (to try again) with a marker (e=True)
    #  to flag that something is wrong.
    if not result:
        raise HTTPFound("/?r=%s&e=True" % r)

    # if we get to here then the user has auth'ed successfully
    # grab the user data
    user_data = ldap.get_user_data()
    log.debug(user_data)

    # grab a handle to the database
    db = mdb(request)

    # ensure we have the required indexes on username and token
    db.session.ensure_index('username', pymongo.ASCENDING)
    db.session.ensure_index('token', pymongo.ASCENDING)
    db.code.ensure_index('token', pymongo.ASCENDING)
    db.code.ensure_index('code', pymongo.ASCENDING)

    # is there already a session? if so - generate a code for that and return it
    doc = db.session.find_one({ 'username': user_data.username })
    try:
        # there's an existing session - generate a code for it and return that
        log.debug('Found existing session')
        token = doc['token']

    except:
        log.debug('Creating a new session')
        # create a session for the user 
        session_lifetime = int(request.registry.app_config['general']['session.lifetime'])
        token = str(uuid.uuid4()).replace('-', '')

        # check to confirm that there isn't already a session with this id in the db
        doc = db.session.find_one({ 'token': token })
        if doc is not None:
            token = str(uuid.uuid4()).replace('-', '')

        db.session.insert({
            'username': user_data.username,
            'fullname': user_data.fullname,
            'token': token,
            'groups': user_data.groups,
            'createdAt': datetime.utcnow(),
            'expiresAt': datetime.utcnow() + timedelta(seconds = session_lifetime)
        })
        try:
            db.session.ensure_index('createdAt', expireAfterSeconds = session_lifetime)
        except OperationFailure:
            db.session.drop_index('createdAt_1')
            db.session.ensure_index('createdAt', expireAfterSeconds = session_lifetime)
    
    log.debug("Looking up the session to see if there's already a one time code tied to it")
    doc = db.code.find_one({ 'token': token })
    try:
        otc = doc['code']
    except:
        log.debug('Generating new one time code')
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


    # is the user actually allowed to access this app?
    allowed = False
    app_groups_allowed = get_app_allow(request, r)
    for g in user_data.groups:
        if g in app_groups_allowed:
            allowed = True

    if allowed:
        login_callback = get_login_callback(request, r)
        log.debug('Returning one time code to the calling application')
        log.debug("Callback: %s/%s, Token: %s, One time code: %s" % (login_callback, otc, token, otc))
        raise HTTPFound("%s/%s" % (login_callback, otc))
    else:
        log.debug('User not allowed to use this application')
        forbidden_callback = get_forbidden_callback(request, r)
        raise HTTPFound("%s" % (forbidden_callback))

@view_config(context='velruse.providers.google_oauth2.GoogleAuthenticationComplete')
def google_login_complete(request):
    session = request.session
    context = request.context
    for k, v in context.profile.items():
        print k, v

    #session['isLoggedIn'] = True
    #session['username'] = context.profile['displayName']
    #session['email'] = context.profile['verifiedEmail']
    raise HTTPFound('/')

@view_config(context='velruse.providers.linkedin.LinkedInAuthenticationComplete')
def linkedin_login_complete(request):
    session = request.session
    context = request.context
    for k, v in context.profile.items():
        print k, v

    #session['isLoggedIn'] = True
    #session['username'] = context.profile['name']['formatted']
    #session['email'] = context.profile['emails'][0]['value']
    #session['email'] = context.profile['verifiedEmail']
    #print context.profile
    raise HTTPFound('/')

def process_social_login(user_data):
    # grab a handle to the database
    db = mdb(request)

@view_config(context='velruse.AuthenticationDenied', renderer="denied.mak")
def login_denied_view(request):
    raise HTTPUnauthorized

@view_config(route_name="retrieve_token", request_method="GET", renderer='json')
def retrieve_token(request):
    # is the code valid?
    code = request.matchdict.get('code')
    if code == None:
        raise HTTPUnauthorized

    log.debug("Code: %s" % code)

    # grab a handle to the database
    db = mdb(request)

    # use the code to lookup the token
    doc = db.code.find_one({ 'code': code })

    if doc is not None:
        # delete the code
        db.code.remove({ 'code': code })
        return doc['token']
    raise HTTPUnauthorized


@view_config(route_name="validate_token", request_method="POST", renderer='json')
def validate_token(request):
    log.debug('Validate token method called')
    if not verify_caller(request, request.referrer):
        raise HTTPUnauthorized

    try:
        token = request.json_body['data']['token']
    except:
        raise HTTPUnauthorized

    # grab a handle to the database
    db = mdb(request)

    doc = db.session.find_one({ 'token': token })
    log.debug('Validate token method returning')
    if doc is not None:
        return {
            'username': doc['username'],
            'fullname': doc['fullname'],
            'expiresAt': str(doc['expiresAt'])
        }

    else:
        log.debug('Forbidden')
        raise HTTPUnauthorized

