from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPOk,
    HTTPFound,
    HTTPInternalServerError,
    HTTPForbidden,
    HTTPUnauthorized
)

from common import *
import logging
log = logging.getLogger(__name__)

import pymongo
from bson.objectid import ObjectId
from bson import json_util

import traceback


@view_config(route_name='admin_check_email', request_method='GET', renderer='json')
def admin_check_email(request):
    log.debug('GET: /admin/email/{email} - check email address')

    # verify the token and session
    claims = verify_token(request)
    if not claims['isAdmin']:
        raise HTTPUnauthorised

    db = mdb(request)

    doc = db.profiles.find_one({ 'primaryEmail': request.matchdict.get('email') })
    if doc is not None:
        return { 'userdata': { 'name': doc['username'], 'primaryEmail': doc['primaryEmail'], 'secondaryEmail': doc['secondaryEmail'] } }

    doc =  db.profiles.find_one({ 'secondaryEmail': request.matchdict.get('email') })
    if doc is not None:
        return { 'userdata': { 'name': doc['username'], 'primaryEmail': doc['primaryEmail'], 'secondaryEmail': doc['secondaryEmail'] } }

    return { 'userdata': ''}

@view_config(route_name='admin_users', request_method='GET', renderer='json')
def admin_users_get(request):
    log.debug('GET: /admin/users')

    # verify the token and session
    claims = verify_token(request)
    if not claims['isAdmin']:
        raise HTTPUnauthorised

    db = mdb(request)

    apps = get_app_data(request, except_social=True)
    apps = [ { 'name': a.name, 'permission': None } for a in apps ]
    try:
        user_accounts = db.profiles.find()
        users = []
        for u in user_accounts:
            user = {
                'id': str(u['_id']),
                'username': u['username'],
                'primaryEmail': u['primaryEmail'],
                'secondaryEmail': u['secondaryEmail']
            }

            user['apps'] = apps
            if u.has_key('apps'):
                for app in u['apps']:
                    user['apps']['app']['permission'] = app['permission']

            users.append(user)

        return { 'users': users }

    except:
        print '**', traceback.print_exc()
        return {}

@view_defaults(route_name='admin_user', renderer='json')
class AdminUserMgt:

    def __init__(self, request):
        # verify the token and session
        self.claims = verify_token(request)
        if not self.claims['isAdmin']:
            raise HTTPUnauthorised

        self.request = request
        self.db = mdb(request)

    @view_config(request_method='GET')
    def admin_users_get(self):
        log.debug('GET: /admin/user')

        apps = get_app_data(self.request)
        apps = [ { 'name': a.name, 'permission': None } for a in apps ]
        try:
            user_accounts = self.db.profiles.find()
            users = []
            for u in user_accounts:
                user = {
                    'id': str(u['_id']),
                    'username': u['username'],
                    'primaryEmail': u['primaryEmail'],
                    'secondaryEmail': u['secondaryEmail']
                }

                user['apps'] = apps
                if u.has_key('apps'):
                    for app in u['apps']:
                        user['apps']['app']['permission'] = app['permission']
                print user

                users.append(user)

            return { 'users': users }

        except:
            print '**', traceback.print_exc()
            return {}

    @view_config(request_method='POST')
    def admin_user_post(self):
        log.debug('POST: /admin/user')

        try:
            log.debug('Creating new user profile')
            # create the account
            self.db.profiles.insert({
                'username': self.request.json_body.get('username'),
                'primaryEmail': self.request.json_body.get('primaryEmail'),
                'secondaryEmail': self.request.json_body.get('secondaryEmail'),
                'status': 'enabled'
            })
            self.db.profiles.ensure_index('primaryEmail', pymongo.ASCENDING)
            self.db.profiles.ensure_index('secondaryEmail', pymongo.ASCENDING)
            return {}
        except:
            log.debug("Something went wrong trying to create user profile for: %s" % request.json_body)
            print traceback.print_exc()
            raise HTTPInternalServerError

    @view_config(request_method='PUT')
    def admin_user_put(self):
        log.debug('PUT: /admin/user')

        try:
            user_id = self.request.matchdict.get('user')
            doc = self.db.profiles.find_one({ '_id': ObjectId(user_id) })
            action = self.request.json_body.get('action')
            who = doc['username']
            admin = self.claims['fullname']

            if action == 'lockAccount':
                if doc['status'] == 'enabled':
                    status = 'locked'
                    log.debug("'%s (%s)' account locked ['%s]'" % (who, user_id, admin))
                else:
                    status = 'enabled'
                    log.debug("'%s (%s)' account unlocked ['%s]'" % (who, user_id, admin))

                self.db.profiles.update(
                    { '_id': ObjectId(user_id) },
                    { '$set': { 'status': status }}
                )

            elif action == 'denyAccess':
                app = self.request.json_body.get('app')
                log.debug("'%s (%s)' access to '%s' removed ['%s']" % (who, user_id, app, admin))

            elif action == 'allowAccess':
                app = self.request.json_body.get('app')
                log.debug("'%s (%s)' granted access to '%s' ['%s']" % (who, user_id, app, admin))
        except:
            print traceback.print_exc()
            raise HTTPInternalServerError

    @view_config(request_method='DELETE')
    def admin_user_delete(self):
        log.debug('DELETE: /admin/user')

        try:
            user_id = self.request.matchdict.get('user')
            doc = self.db.profiles.find_one( { '_id': ObjectId(user_id) })
            who = doc['username']
            admin = self.claims['fullname']

            log.debug("'%s (%s)' account deleted ['%s']" % (who, user_id, admin))

            result = self.db.profiles.remove( { '_id': ObjectId(self.request.matchdict['user']) })
            return {}
        except:
            print traceback.print_exc()
            raise HTTPInternalServerError


