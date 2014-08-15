from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPOk,
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden,
    HTTPUnauthorized
)
from pyramid.response import Response
import ast

import auth
import time
import uuid
import os
import os.path
import sys
from datetime import datetime, timedelta, date

import logging
log = logging.getLogger('essos')

from pymongo.errors import (
    OperationFailure
)
import pymongo
import velruse

from connectors import MongoDBConnection as mdb
from config import AppsConfig
from common import *

@view_config(route_name="health_check", request_method="GET", renderer="string")
def health_check(request):
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
    #  validate the r param if exists and redirect to bare home domain if it's not a 
    #  verified application - ie one of ours
    # check that the user is known and just take them straight to their profile
    #  page if they are

    # get the URL params; these will be blank if unset
    r = request.GET.get('r')
    e = request.GET.get('e')

    # is the redirecting app authorised? if not - redirect to home
    if r and not validate_app_redirect(request, r):
        raise HTTPFound('/')

    user = check_user_known(request)
    if user:
        # send the user on
        move_the_user_on(request, r, user['token'])

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
    user = check_user_known(request)
    if (not request.POST.get('username') and not request.POST.get('pasword')) and not user:
        raise HTTPFound('/')

    lc = request.registry.app_config['ldap']
    ldap = auth.LDAP(lc['servers'], lc['base'], lc['binduser'], lc['bindpass'])
    result = ldap.authenticate(request.POST['username'], request.POST['password'])

    r = request.POST.get('r')

    # if 'not result' means they didn't auth successfully so send
    #  them back to the start (to try again) with a marker (e=True)
    #  to flag that something is wrong.
    if not result:
        lockout_ip(request)
        if r:
            raise HTTPFound("/?r=%s&e=True" % r)
        else:
            raise HTTPFound('/?e=True')

    # grab the user data
    data = ldap.get_user_data()

    # if we get to here then the user has auth'ed successfully
    db = mdb(request)

    # do they have a session?
    doc = db.session.find_one({ 'username': data.username })
    if doc is not None:
        move_the_user_on(request, r, doc['token'])

    else:
        # ensure we have the required indexes on username and token
        db.session.ensure_index('username', pymongo.ASCENDING)
        db.session.ensure_index('token', pymongo.ASCENDING)

        # no session found for the current user so we need to create one
        session_lifetime = int(request.registry.app_config['general']['session.lifetime'])
        token = uuid.uuid4()
        db.session.insert({
            'username': data.username,
            'fullname': data.fullname,
            'token': token,
            'groups': data.groups,
            'createdAt': datetime.utcnow()
        })
        try:
            db.session.ensure_index('createdAt', expireAfterSeconds = session_lifetime)
        except OperationFailure:
            db.session.drop_index('createdAt_1')
            db.session.ensure_index('createdAt', expireAfterSeconds = session_lifetime)

    move_the_user_on(request, r, token)

    return {}

@view_config(route_name="logout", request_method="GET", renderer='jsonp')
def logout(request):
    log.debug('logout called')
    db = mdb(request)
    token = request.cookies.get('EAT')
    db.session.remove(token=token)

    delete_cookie(request)
    raise HTTPFound('/', headers=request.response.headers)

@view_config(route_name="profile", request_method="GET", renderer='templates/profile.mak')
def profile(request):
    log.debug("%s: profile view" % request.client_addr)
    # grab the users token and verify
    # redirect to login page if no token or invalid
    # display app list otherwise
    user = check_user_known(request)
    if not user:
        raise HTTPFound('/')

    # generate the app data list and return that to the profile page
    apps = get_app_data(request)
    allowed_apps = []
    for app in apps:
        s1 = set(app.allow)
        s2 = set(user['groups'])
        if s1.intersection(s2):
            allowed_apps.append(app)
    return  { 'apps': allowed_apps, 'fullname': user['fullname'] }

@view_config(route_name="retrieve_token", request_method="GET", renderer='jsonp')
def retrieve_token(request):
    # only set the allow origin header if the referrer is one of our apps
    if validate_app_redirect(request, request.referrer):
        request.response.headers['Access-Control-Allow-Origin'] = request.referrer
    else:
        return {}

    code = request.matchdict.get('code')
    session = CSession(request)
    orm = ORM(session)
    data = orm.query('session_by_code',
        where = [ "\"code\" = %s" % code ]
    )
    if data:
        #orm.delete('session_by_code',
        #    where = [ "\"code\" = %s" % code ]
        #)
        return { 'token': str(data[0].token) }

    raise HTTPUnauthorized

@view_config(route_name="validate_token", request_method="POST", renderer='json')
def validate_token(request):
    token = request.json_body['data']['token']
    session = CSession(request)
    orm = ORM(session)
    data = orm.query('session_by_token',
        where = [ "\"token\" = %s" % token ]
    )
    resp = Response(headers=request.response.headers)
    if data:    
        data = data[0]
        resp.json_body = { 'session': 'active', 'username': data.username, 'fullname': data.fullname, 'is_admin': data.is_admin}
        return resp

    raise HTTPUnauthorized

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


@view_config(context='velruse.AuthenticationDenied', renderer="denied.mak")
def login_denied_view(request):
    raise HTTPFound('/')
