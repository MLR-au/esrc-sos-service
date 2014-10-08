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
    """Check email address against exisiting profiles

    @method: GET
    @params:
    - GET: email

    @ returns:
        { 'userdata': user data if email already in an existing profile }
    """
    # verify the token and session
    claims = verify_token(request)
    if not claims['admin']:
        raise HTTPUnauthorised

    db = mdb(request)

    doc = db.profiles.find_one( {'$or': [ { 'primaryEmail': request.matchdict.get('email') }, { 'secondaryEmail': request.matchdict.get('email') } ] })
    if doc is not None:
        return { 'userdata': { 'name': doc['username'], 'primaryEmail': doc['primaryEmail'], 'secondaryEmail': doc['secondaryEmail'] } }

    return { 'userdata': '' }

@view_config(route_name='admin_users', request_method='GET', renderer='json')
def admin_users_get(request):
    """Get all user profiles

    @method: GET
    @params:

    @returns:
        { 'users': list of users }
    """

    # verify the token and session
    claims = verify_token(request)
    if not claims['admin']:
        raise HTTPUnauthorised

    db = mdb(request)

    apps = get_app_data(request, except_social=True)
    apps = [ { 'name': a.name, 'permission': None } for a in apps ]

    user_accounts = db.profiles.find().sort('username', pymongo.ASCENDING)
    users = []
    for u in user_accounts:
        user_id = u['_id']
        user = u 
        
        # Build a new apps dictionary based on sos's configuration
        user_apps = {}
        for app in apps:
            user_apps[app['name']] = 'deny'

        # pull existing configuration back in
        try:
            for app in u['apps']:
                user_apps[app] = u['apps'][app]
        except:
            pass
        user['apps'] = user_apps
        user['_id'] = str(user['_id'])
        
        # save the updated apps dict back into the profile
        db.profiles.update(
            { '_id': ObjectId(user_id) },
            { '$unset': { 'apps': "" }}
        )
        db.profiles.update(
            { '_id': ObjectId(user_id) },
            { '$set': { 'apps': user_apps }}
        )

        users.append(user)

    return { 'users': users }

@view_defaults(route_name='admin_user', renderer='json')
class AdminUserMgt:
    """Manage the account and permissions of a social user"""


    def __init__(self, request):
        # verify the token and session
        self.claims = verify_token(request)
        if not self.claims['admin']:
            raise HTTPUnauthorised

        self.request = request
        self.db = mdb(request)

    @view_config(request_method='GET')
    def admin_users_get(self):
        """Get the data for a user

        @params:
        """
        log.info('GET: /admin/user')

    @view_config(request_method='POST')
    def admin_user_post(self):
        """Create a profile for a social user

        @method: POST
        @params:
        - json_body - username: The users' name. Only really used in the admin app.
        - json_body - primaryEmail: A social email address for the user.
        - json_body - secondaryEmail: Another social email address for the user.

        @returns:
        { 'userdata': user data object from mongo }
        """

        try:
            # verify there isn't already a user with any of the defined email addresses.
            doc = self.db.profiles.find_one( { 'primaryEmail': self.request.json_body.get('primaryEmail') } )
            if doc is not None:
                doc['_id'] = str(doc['_id'])
                return { 'userdata': doc }

            if self.request.json_body.get('secondaryEmail') is not None:
                doc = self.db.profiles.find_one( { 'secondaryEmail': self.request.json_body.get('secondaryEmail') } )
                if doc is not None:
                    doc['_id'] = str(doc['_id'])
                    return { 'userdata': doc }

            log.info("%s: Creating new user profile." % self.request.client_addr)
            # create the account
            self.db.profiles.insert({
                'username': self.request.json_body.get('username'),
                'primaryEmail': self.request.json_body.get('primaryEmail'),
                'secondaryEmail': self.request.json_body.get('secondaryEmail'),
                'status': 'enabled'
            })
            self.db.profiles.ensure_index('primaryEmail', pymongo.ASCENDING)
            self.db.profiles.ensure_index('secondaryEmail', pymongo.ASCENDING)

            # return the updated profile data
            doc = self.db.profiles.find_one({ 'primaryEmail': self.request.json_body.get('primaryEmail') })
            doc['_id'] = str(doc['_id'])

            return { 'userdata': doc }
        except:
            log.error("%s: Something went wrong trying to create user profile for: %s" % (self.request.client_addr, selfrequest.json_body))
            log.error(traceback.print_exc())
            raise HTTPInternalServerError

    @view_config(request_method='PUT')
    def admin_user_put(self):
        """Update the profile for a social user

        @method: PUT
        @params:
        - GET: user_id: the Mongo ObjectID for the user
        - PUT: action: lockAccount | denyAccess | allowAccess

        @returns:
        { 'userdata': user data object from mongo }
        """

        try:
            user_id = self.request.matchdict.get('user')
            doc = self.db.profiles.find_one({ '_id': ObjectId(user_id) })
            action = self.request.json_body.get('action')
            who = doc['username']
            admin = self.claims['fullname']

            if action == 'lockAccount':
                if doc['status'] == 'enabled':
                    status = 'locked'
                    log.info("%s: '%s (%s)' account locked by '%s'" % (self.request.client_addr, who, user_id, admin))
                else:
                    status = 'enabled'
                    log.info("%s: '%s (%s)' account unlocked by '%s'" % (self.request.client_addr, who, user_id, admin))

                # update the user's profile
                self.db.profiles.update(
                    { '_id': ObjectId(user_id) },
                    { '$set': { 'status': status }}
                )

            elif action == 'denyAccess':
                app = self.request.json_body.get('app')
                log.info("%s: '%s (%s)' access to '%s' removed by '%s'" % (self.request.client_addr, who, user_id, app, admin))

                doc = self.db.profiles.find_one(
                    { '_id': ObjectId(user_id) },
                    { 'apps': True }
                )
                apps = doc['apps']
                apps[app] = 'deny'

                # update the user's profile
                self.db.profiles.update(
                    { '_id': ObjectId(user_id) },
                    { '$set': { 'apps': apps }}
                )

            elif action == 'allowAccess':
                app = self.request.json_body.get('app')
                log.info("%s: '%s (%s)' granted access to '%s' by '%s'" % (self.request.client_addr, who, user_id, app, admin))

                doc = self.db.profiles.find_one(
                    { '_id': ObjectId(user_id) },
                    { 'apps': True }
                )
                apps = doc['apps']
                apps[app] = 'allow'

                # update the user's profile
                self.db.profiles.update(
                    { '_id': ObjectId(user_id) },
                    { '$set': { 'apps': apps }}
                )

            # return the updated profile data
            doc = self.db.profiles.find_one({ '_id': ObjectId(user_id) })
            doc['_id'] = str(doc['_id'])

            return { 'userdata': doc }

        except:
            print traceback.print_exc()
            raise HTTPInternalServerError

    @view_config(request_method='DELETE')
    def admin_user_delete(self):
        """Delete the profile of a social user

        @method: DELETE
        @params
        - GET: user_id: the Mongo ObjectID for the user

        @returns:
        { }
        """

        try:
            user_id = self.request.matchdict.get('user')
            doc = self.db.profiles.find_one( { '_id': ObjectId(user_id) })
            who = doc['username']
            admin = self.claims['fullname']

            log.info("'%s (%s)' account deleted ['%s']" % (who, user_id, admin))

            result = self.db.profiles.remove( { '_id': ObjectId(self.request.matchdict['user']) })
            return {}
        except:
            print traceback.print_exc()
            raise HTTPInternalServerError


