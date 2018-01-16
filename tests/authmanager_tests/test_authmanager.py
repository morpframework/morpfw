import nose
import morepath
from webtest import TestApp as Client
from morp.authmanager.app import App
from morp.authmanager import create_app
from morp.authmanager.authpolicy import JWTWithAPIKeyIdentityPolicy
from more.jwtauth import JWTIdentityPolicy
import json
import yaml
import os
import copy
from more.basicauth import BasicAuthIdentityPolicy
import time


def get_client(app, config='settings.yml', **kwargs):
    if isinstance(config, str):
        with open(os.path.join(os.path.dirname(__file__), config)) as f:
            settings = yaml.load(f)
    else:
        settings = config

    def get_identity_policy():
        return JWTWithAPIKeyIdentityPolicy(master_secret='secret', leeway=10,
                                           allow_refresh=True)

    def verify_identity(identity):
        return True

    kwargs = {}
    appobj = create_app(app, settings, get_identity_policy=get_identity_policy,
                        verify_identity=verify_identity, **kwargs)
    c = Client(appobj)
    return c


def _test_authentication(c):
    r = c.post_json('/api/v1/user/+register',
                    {'username': 'admin',
                     'password': 'admin',
                     'password_validate': 'admin'})

    assert r.json == {'status': 'success'}

    r = c.get('/api/v1/user/+login')

    assert r.json['schema']['title'] == 'credential'

    login = r.json['links'][0]
    assert login['rel'] == 'login'
    assert login['type'] == 'POST'

    r = c.post_json(login['href'], {
        'username': 'admin',
        'password': 'admin'
    })

    assert r.json == {
        'status': 'success'
    }

    jwttoken = r.headers.get('Authorization').split()[1]

    r = c.post_json('/api/v1/user/+login', {
        'username': 'invaliduser',
        'password': 'invalidpassword'
    }, expect_errors=True)

    assert r.json == {
        'status': 'error',
        'error': {
            'code': 401,
            'message': 'Invalid Username / Password'
        }
    }

    r = c.post_json('/api/v1/user/+login', {
        'username': 'admin',
        'password': 'invalidpassword'
    }, expect_errors=True)

    assert r.json == {
        'status': 'error',
        'error': {
            'code': 401,
            'message': 'Invalid Username / Password'
        }
    }

    # from now on we login as admin

    c.authorization = ('JWT', jwttoken)

    # lets test refreshing token
    time.sleep(2)

    r = c.get('/api/v1/user/+refresh_token')

    n = r.headers.get('Authorization').split()

    assert c.authorization[1] != n[1]

    c.authorization = ('JWT', n[1])

    r = c.get('/api/v1/user/admin')

    assert r.json['data']['username'] == 'admin'
    assert r.json['data']['groups'] == ['__default__']
    assert r.json['data']['state'] == 'active'

    r = c.get('/api/v1/user/unknownuser', expect_errors=True)

    assert r.status_code == 404

    r = c.get('/api/v1/user/')

    assert r.json['schema']['title'] == 'user'

    r = c.post_json('/api/v1/user/+register',
                    {'username': 'user1',
                     'password': 'password',
                     'password_validate': 'password'})

    assert r.json == {'status': 'success'}

    r = c.post_json('/api/v1/user/+register',
                    {'username': 'user2',
                     'password': 'password',
                     'password_validate': 'password'})

    assert r.json == {'status': 'success'}

    r = c.post_json('/api/v1/user/+register',
                    {'username': 'user1',
                     'password': {'hello': 'world'}},
                    expect_errors=True)

    assert r.status_code == 422

    r = c.post_json('/api/v1/user/+register',
                    {'username': 'user1',
                     'password': 'password',
                     'password_validate': 'password'},
                    expect_errors=True)

    assert r.status_code == 422
    assert r.json['status'] == 'error'
    assert r.json['error']['type'] == 'UserExistsError'

    r = c.get('/api/v1/user/user1')

    assert r.json['data']['username'] == 'user1'
    assert r.json['data']['groups'] == ['__default__']
    assert r.json['data']['state'] == 'active'
    assert 'password' not in r.json['data'].keys()

    r = c.post_json('/api/v1/user/+login', {
        'username': 'user1',
        'password': 'password'
    })

    assert r.status_code == 200

    r = c.post_json(
        '/api/v1/user/user1/+statemachine', {'transition': 'deactivate'})

    r = c.get('/api/v1/user/user1')

    assert r.json['data']['username'] == 'user1'
    assert r.json['data']['groups'] == ['__default__']
    assert r.json['data']['state'] == 'inactive'

    r = c.post_json('/api/v1/user/+login', {
        'username': 'user1',
        'password': 'password'
    }, expect_errors=True)

    assert r.status_code == 401

    r = c.post_json(
        '/api/v1/user/user1/+statemachine', {'transition': 'activate'})

    r = c.post_json('/api/v1/user/user1/',
                    {'password': 'newpass'}, expect_errors=True)

    assert r.status_code == 422

    r = c.post_json('/api/v1/user/user1/',
                    {'username': 'newusername'}, expect_errors=True)

    assert r.status_code == 422

    r = c.post_json('/api/v1/user/user1/+change_password', {
        'password': 'password', 'new_password': 'newpass',
        'new_password_validate': 'newpass'
    })

    assert r.status_code == 200

    r = c.post_json('/api/v1/user/+login', {
        'username': 'user1',
        'password': 'newpass'
    })

    assert r.status_code == 200

    # api keys
    r = c.post_json('/api/v1/apikey/',
                    {'label': 'samplekey', 'password': 'admin'})

    key_identity = r.json['data']['api_identity']
    key_secret = r.json['data']['api_secret']
    key_uuid = r.json['data']['uuid']
    assert len(key_identity) == 32
    assert len(key_secret) == 32
    assert r.json['data']['username'] == 'admin'

    r = c.get('/api/v1/apikey/%s' % key_uuid)

    assert key_identity == r.json['data']['api_identity']
    assert key_secret == r.json['data']['api_secret']
    assert key_uuid == r.json['data']['uuid']

    c.authorization = None

    # user1 shouldnt see admin's apikey
    r = c.post_json(login['href'], {
        'username': 'user1',
        'password': 'newpass'
    })

    c.authorization = ('JWT', r.headers.get('Authorization').split()[1])

    r = c.get('/api/v1/apikey/+search')

    assert len(r.json['results']) == 0

    c.authorization = None

    r = c.post_json(
        '/api/v1/user/user1/+statemachine', {'transition': 'deactivate'},
        expect_errors=True)

    assert r.status_code == 403

    r = c.post_json(
        '/api/v1/user/user1/+statemachine',
        {'transition': 'deactivate'}, headers=[
            ('X-API-KEY', '.'.join([key_identity, key_secret]))
        ])

    assert r.status_code == 200

    c.authorization = ('JWT', jwttoken)
    r = c.get('/api/v1/group/')

    assert r.json['schema']['title'] == 'group'

    r = c.post_json('/api/v1/group/', {'groupname': 'group1'})

    assert r.json['data']['groupname'] == 'group1'

    r = c.post_json('/api/v1/group/', {'groupname': 'group1'},
                    expect_errors=True)

    assert r.json['status'] == 'error'
    assert r.json['error']['type'] == 'GroupExistsError'

    r = c.get('/api/v1/group/group1')

    assert r.json['data']['groupname'] == 'group1'

    r = c.post_json('/api/v1/group/group1/+grant',
                    {'mapping': {'user1': ['member']}})

    assert r.json == {'status': 'success'}

    r = c.get('/api/v1/user/user1')

    assert list(sorted(r.json['data']['groups'])) == [
        '__default__', 'group1']

    r = c.get('/api/v1/group/group1/+members')

    assert r.json == {
        'users': [
            {'username': 'user1',
             'links': [{
                 'rel': 'self',
                 'type': 'GET',
                 'href': 'http://localhost/api/v1/user/user1'}],
             'roles': ['member']}]
    }

    r = c.post_json('/api/v1/group/group1/+grant', {'mapping': {
        'user1': ['manager']
    }})

    assert r.json == {'status': 'success'}

    r = c.get('/api/v1/group/group1/+members')

    assert r.json['users'][0]['roles'] == ['member', 'manager']

    r = c.post_json('/api/v1/group/group1/+grant', {'mapping': {
        'user1': ['editor']
    }})

    assert r.json == {'status': 'success'}

    r = c.get('/api/v1/group/group1/+members')

    assert sorted(r.json['users'][0]['roles']
                  ) == sorted(['member', 'editor', 'manager'])

    r = c.get('/api/v1/user/user1/+roles')

    assert sorted(r.json['group1']) == sorted(['member', 'editor', 'manager'])

    r = c.post_json('/api/v1/group/group1/+revoke',
                    {'mapping': {
                        'user1': ['manager']
                    }})

    assert r.json == {'status': 'success'}

    r = c.get('/api/v1/group/group1/+members')

    assert r.json['users'][0]['roles'] == ['member', 'editor']

    r = c.post_json('/api/v1/group/group1/+revoke', {
        'mapping': {'user1': ['editor', 'member']}
    })

    assert r.json == {'status': 'success'}

    r = c.get('/api/v1/group/group1/+members')

    assert len(r.json['users']) == 0

    r = c.delete('/api/v1/user/user1')

    assert r.json == {'status': 'success'}

    r = c.get('/api/v1/user/user1', expect_errors=True)

    assert r.status_code == 404
