#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

import pytest
import json
import requests
import copy
import iris_api.bin.iris_ctl as iris_ctl
from click.testing import CliRunner


server = 'http://localhost:16649/'
base_url = server + 'v0/'

sample_db_config = {
    'db': {
        'conn': {
            'str': "%(scheme)s://%(user)s:%(password)s@%(host)s/%(database)s?charset=%(charset)s",
            'kwargs': {
                'scheme': 'mysql+pymysql',
                'user': 'root',
                'password': '',
                'host': '127.0.0.1',
                'database': 'iris',
                'charset': 'utf8'}},
        'kwargs': {
            'pool_recycle': 3600,
            'echo': False,
            'pool_size': 100,
            'max_overflow': 100,
            'pool_timeout': 60
        }}}


def username_header(username):
    return {'X-IRIS-USERNAME': username}


@pytest.fixture(scope='module')
def iris_messages():
    '''List of iris messages'''
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('SELECT `id`, `incident_id` FROM `message` WHERE NOT ISNULL(`incident_id`) LIMIT 3')
        return [dict(id=id, incident_id=incident_id) for (id, incident_id) in cursor]


@pytest.fixture(scope='module')
def iris_incidents():
    '''List of iris incidents'''
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('SELECT `id` FROM `incident` LIMIT 3')
        return [dict(id=id) for (id,) in cursor]


@pytest.fixture(scope='module')
def fake_message_id(iris_messages):
    '''A sample message ID'''
    if iris_messages:
        return iris_messages[0]['id']


@pytest.fixture(scope='module')
def fake_batch_id():
    '''A sample message batch ID'''
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('SELECT `batch` FROM `message` WHERE NOT ISNULL(`incident_id`) AND NOT ISNULL(`batch`) LIMIT 1')
        result = cursor.fetchall()
        if not result:
            return None
        return result[0][0]


@pytest.fixture(scope='module')
def fake_incident_id(iris_messages):
    '''ID of incident corresponding to fake_message_id'''
    if iris_messages:
        return iris_messages[0]['incident_id']


@pytest.fixture(scope='module')
def iris_users():
    '''List of all iris users'''
    re = requests.get(base_url + 'targets/user')
    assert re.status_code == 200
    return re.json()


@pytest.fixture(scope='module')
def iris_teams():
    '''List of all iris teams'''
    re = requests.get(base_url + 'targets/team')
    assert re.status_code == 200
    return re.json()


@pytest.fixture(scope='module')
def iris_applications():
    '''List of all iris applications' metadata'''
    re = requests.get(base_url + 'applications')
    assert re.status_code == 200
    return re.json()


@pytest.fixture(scope='module')
def sample_user(iris_users):
    '''First user in our list of iris users whose length is long enough for filtering'''
    for user in iris_users:
        if len(user) > 2:
            return user


@pytest.fixture(scope='module')
def sample_user2(sample_user, iris_users):
    '''First user in our list of iris users whose length is long enough for filtering and does not start similarly to sample_user'''
    for user in iris_users:
        if user != sample_user and len(user) > 2 and not sample_user.startswith(user[:2]):
            return user


@pytest.fixture(scope='module')
def sample_admin_user():
    '''List of iris messages'''
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('SELECT `name` FROM `target` JOIN `user` on `target`.`id` = `user`.`target_id` WHERE `user`.`admin` = TRUE LIMIT 1')
        result = cursor.fetchone()
        if result:
            return result[0]


@pytest.fixture(scope='module')
def sample_team(iris_teams):
    '''First team in our list of iris teams whose length is long enough for filtering'''
    for team in iris_teams:
        if len(team) > 2:
            return team


@pytest.fixture(scope='module')
def sample_team2(sample_team, iris_teams):
    '''First team in our list of iris teams whose length is long enough for filtering and does not start similarly to sample_team'''
    for team in iris_teams:
        if team != sample_team and len(team) > 2 and not sample_team.startswith(team[:2]):
            return team


@pytest.fixture(scope='module')
def sample_email(sample_user):
    '''Email address of sample_user'''
    re = requests.get(base_url + 'users/' + sample_user, headers=username_header(sample_user))
    assert re.status_code == 200
    data = re.json()
    return data['contacts']['email']


@pytest.fixture(scope='module')
def sample_phone(sample_user):
    '''Email address of sample_user'''
    re = requests.get(base_url + 'users/' + sample_user, headers=username_header(sample_user))
    assert re.status_code == 200
    data = re.json()
    return data['contacts']['call']


@pytest.fixture(scope='module')
def superuser_application():
    '''application which should have 'allow_other_app_incidents' in DB set to 1, allowing it to create incidents as other applications.
       should generally be 'iris-frontend' '''
    return 'iris-frontend'


@pytest.fixture(scope='module')
def sample_application_name(iris_applications, superuser_application):
    '''Name of an application which is not the superuser_application'''
    for application in iris_applications:
        if application['name'] != superuser_application:
            return application['name']


@pytest.fixture(scope='module')
def sample_application_name2(iris_applications, superuser_application, sample_application_name):
    '''Name of an application which is neither sample_application_name or superuser_application'''
    for application in iris_applications:
        if application['name'] not in (superuser_application, sample_application_name):
            return application['name']


@pytest.fixture(scope='module')
def sample_template_name(sample_application_name, sample_application_name2):
    '''A template which is used by sample_application_name but not sample_application_name2'''
    re = requests.get(base_url + 'templates?active=1')
    assert re.status_code == 200
    templates = re.json()
    for template in templates:
        re = requests.get(base_url + 'templates/' + template['name'])
        assert re.status_code == 200
        template_data = re.json()
        if sample_application_name in template_data['content'] and sample_application_name2 not in template_data['content']:
            return template['name']


@pytest.fixture(scope='module')
def sample_plan_name():
    '''List of iris messages'''
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('SELECT `name` FROM `plan_active` LIMIT 1')
        result = cursor.fetchone()
        if result:
            return result[0]


@pytest.fixture(scope='module')
def sample_mode():
    '''List of iris messages'''
    modes = requests.get(base_url + 'modes').json()
    if modes:
        return modes[0]


def create_incident_with_message(application, plan, target, mode):
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('''INSERT INTO `incident` (`plan_id`, `created`, `context`, `current_step`, `active`, `application_id`)
                          VALUES (
                            (SELECT `plan_id` from `plan_active` WHERE `name` = %(plan)s),
                            NOW(),
                            "{}",
                            0,
                            TRUE,
                            (SELECT `id` FROM `application` WHERE `name` = %(application)s)
                          )''', {'application': application, 'plan': plan})
        incident_id = cursor.lastrowid
        assert incident_id
        cursor.execute('''INSERT INTO `message` (`created`, `application_id`, `target_id`, `priority_id`, `mode_id`, `active`, `incident_id`)
                          VALUES(
                                  NOW(),
                                  (SELECT `id` FROM `application` WHERE `name` = %(application)s),
                                  (SELECT `id` FROM `target` WHERE `name` = %(target)s),
                                  (SELECT `id` FROM `priority` WHERE `name` = 'low'),
                                  (SELECT `id` FROM `mode` WHERE `name` = %(mode)s),
                                  TRUE,
                                  %(incident_id)s
                          )''', {'application': application, 'target': target, 'mode': mode, 'incident_id': incident_id})
        assert cursor.lastrowid
        conn.commit()
        return incident_id


def test_api_acls(sample_user, sample_user2):
    re = requests.get(base_url + 'users/' + sample_user)
    assert re.status_code == 401
    assert re.json()['title'] == 'Username must be specified for this action'

    re = requests.get(base_url + 'users/' + sample_user, headers=username_header(sample_user2))
    assert re.status_code == 401
    assert re.json()['title'] == 'This user is not allowed to access this resource'

    re = requests.get(base_url + 'users/' + sample_user, headers=username_header(sample_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'users/' + sample_user2, headers=username_header(sample_user2))
    assert re.status_code == 200


def test_api_bad_application():
    re = requests.post(base_url + 'incidents', headers={'Authorization': 'hmac fakeapplication123234234:abc'})
    assert re.status_code == 401


def test_api_response_phone_call(fake_message_id, fake_incident_id, sample_phone):
    if not all([fake_message_id, fake_incident_id, sample_phone]):
        pytest.skip('We do not have enough data in DB to do this test')

    data = {
        'AccountSid': 'AC18c416864ab02cdd51b8129a7cbaff1e',
        'To': sample_phone,
        'ToZip': 15108,
        'FromState': 'CA',
        'Digits': 2,
        'From': '+16504222677'
    }

    re = requests.post(base_url + 'response/twilio/calls', params={
        'message_id': fake_message_id,
    }, data=data)
    assert re.status_code == 200
    assert re.content == '{"app_response":"Iris incident(%s) claimed."}' % fake_incident_id


def test_api_response_batch_phone_call(fake_batch_id, sample_phone):
    if not all([fake_batch_id, sample_phone]):
        pytest.skip('Failed finding a batch ID to use for tests')

    data = {
        'AccountSid': 'AC18c416864ab02cdd51b8129a7cbaff1e',
        'To': sample_phone,
        'ToZip': 15108,
        'FromState': 'CA',
        'Digits': '2',
        'From': '+16504222677',
    }

    re = requests.post(base_url + 'response/twilio/calls', params={
        'message_id': fake_batch_id,
    }, data=data)
    assert re.status_code == 200
    assert re.content == '{"app_response":"All iris incidents claimed for batch id %s."}' % fake_batch_id


def test_api_response_sms(fake_message_id, fake_incident_id, sample_phone):
    if not all([fake_message_id, fake_incident_id, sample_phone]):
        pytest.skip('Failed finding a batch ID to use for tests')

    base_body = {
        'AccountSid': 'AC18c416864ab02cdd51b8129a7cbaff1e',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': sample_phone,
    }

    data = base_body.copy()
    data['Body'] = '%s    claim arg1 arg2' % fake_message_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.content == '{"app_response":"Iris incident(%s) claimed."}' % fake_incident_id

    data = base_body.copy()
    data['Body'] = 'Claim   %s claim arg1 arg2' % fake_message_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.content == '{"app_response":"Iris incident(%s) claimed."}' % fake_incident_id

    data = base_body.copy()
    data['Body'] = fake_message_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid response'


def test_api_response_batch_sms(fake_batch_id):
    if not fake_batch_id:
        pytest.skip('Failed finding a batch ID to use for tests')

    base_body = {
        'AccountSid': 'AC18c416864ab02cdd51b8129a7cbaff1e',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': '+14123706122',
    }

    data = base_body.copy()
    data['Body'] = '%s claim arg1 arg2' % fake_batch_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.content == '{"app_response":"All iris incidents claimed for batch id %s."}' % fake_batch_id

    data = base_body.copy()
    data['Body'] = '%s claim arg1 arg2' % '*(fasdf'
    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 400


def test_api_response_claim_all(sample_user, sample_phone, sample_application_name, sample_application_name2, sample_plan_name, sample_email):
    if not all([sample_user, sample_phone, sample_application_name, sample_plan_name]):
        pytest.skip('Not enough data for this test')

    sms_claim_all_body = {
        'AccountSid': 'AC18c416864ab02cdd51b8129a7cbaff1e',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': sample_phone,
        'Body': 'claim all'
    }

    email_claim_all_payload = {
        'body': 'claim all',
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }

    # Clear out any existing unclaimed incidents, so they don't interfere with these tests
    re = requests.post(base_url + 'response/twilio/messages', data=sms_claim_all_body)
    assert re.status_code in [400, 200]  # 400 if there are no unclaimed incidents.

    # Verify SMS with two incidents from the same app
    incident_id_1 = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'sms')
    assert incident_id_1

    incident_id_2 = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'sms')
    assert incident_id_2

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    re = requests.post(base_url + 'response/twilio/messages', data=sms_claim_all_body)
    assert re.status_code == 200
    assert re.json()['app_response'] in ('Iris Incidents claimed: %s, %s' % (incident_id_1, incident_id_2),
                                         'Iris Incidents claimed: %s, %s' % (incident_id_2, incident_id_1))

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    # Verify email with two incidents from the same app
    incident_id_1 = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'email')
    assert incident_id_1

    incident_id_2 = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'email')
    assert incident_id_2

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    re = requests.post(base_url + 'response/gmail', json=email_claim_all_payload)
    assert re.status_code == 204

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    # Verify SMS with two incidents from different apps
    incident_id_1 = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'sms')
    assert incident_id_1

    incident_id_2 = create_incident_with_message(sample_application_name2, sample_plan_name, sample_user, 'sms')
    assert incident_id_2

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    # Response will be two lines, one for each application and its claimed incidents
    re = requests.post(base_url + 'response/twilio/messages', data=sms_claim_all_body)
    assert re.status_code == 200
    assert set(re.json()['app_response'].splitlines()) == {'%s: Iris Incidents claimed: %s' % (sample_application_name, incident_id_1),
                                                           '%s: Iris Incidents claimed: %s' % (sample_application_name2, incident_id_2)}

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    # Verify email with two incidents from different apps
    incident_id_1 = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'email')
    assert incident_id_1

    incident_id_2 = create_incident_with_message(sample_application_name2, sample_plan_name, sample_user, 'email')
    assert incident_id_2

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    re = requests.post(base_url + 'response/gmail', json=email_claim_all_payload)
    assert re.status_code == 204

    re = requests.get(base_url + 'incidents/%s' % incident_id_1)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    re = requests.get(base_url + 'incidents/%s' % incident_id_2)
    assert re.status_code == 200
    assert re.json()['active'] == 0


def test_api_response_claim_last(sample_user, sample_phone, sample_application_name, sample_plan_name, sample_email):
    if not all([sample_user, sample_phone, sample_application_name, sample_plan_name]):
        pytest.skip('Not enough data for this test')

    # Verify SMS
    incident_id = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'sms')
    assert incident_id

    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    sms_body = {
        'AccountSid': 'AC18c416864ab02cdd51b8129a7cbaff1e',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': sample_phone,
        'Body': 'claim last'
    }

    re = requests.post(base_url + 'response/twilio/messages', data=sms_body)
    assert re.status_code == 200

    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    # Verify email
    incident_id = create_incident_with_message(sample_application_name, sample_plan_name, sample_user, 'email')
    assert incident_id

    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200
    assert re.json()['active'] == 1

    data = {
        'body': 'claim last',
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 204

    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200
    assert re.json()['active'] == 0


def test_api_response_email(fake_message_id, sample_email):
    if not all([fake_message_id, sample_email]):
        pytest.skip('Failed finding a batch ID to use for tests')

    data = {
        'body': '%s claim' % fake_message_id,
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 204

    data = {
        'body': 'claim %s' % fake_message_id,
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 204

    data = {
        'body': 'claim',
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'Re: %s Alert That Is Firing' % fake_message_id}
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 204


def test_api_response_invalid_email(fake_message_id):
    if not fake_message_id:
        pytest.skip('Failed finding a batch ID to use for tests')

    data = {
        'body': '%s claim' % fake_message_id,
        'headers': [
            {'name': 'From', 'value': 'fakeemail_123@foo.bar'},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 400


def test_api_response_gmail_one_click(fake_message_id, sample_email):
    if not all([fake_message_id, sample_email]):
        pytest.skip('Failed finding a batch ID to use for tests')

    re = requests.post(base_url + 'response/gmail-oneclick', json={
        'msg_id': fake_message_id,
        'email_address': sample_email,
        'cmd': 'claim'
    })
    assert re.status_code == 204

    re = requests.post(base_url + 'response/gmail-oneclick', json={
        'msg_id': 'fakemessageid',
        'email_address': sample_email,
        'cmd': 'claim'
    })
    assert re.status_code == 400

    re = requests.post(base_url + 'response/gmail-oneclick', json={})
    assert re.status_code == 400


def test_api_response_batch_email(fake_batch_id, sample_email):
    if not fake_batch_id:
        pytest.skip('Failed finding a batch ID to use for tests')

    data = {
        'body': '%s claim' % fake_batch_id,
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 204

    data = {
        'body': 'claim %s' % fake_batch_id,
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 204

    data = {
        'body': u'I\u0131d claim',
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 400


def test_plan_routing():
    re = requests.get(base_url + 'plans/TESTDOOOOT')
    assert re.content == ""
    assert re.status_code == 404


def test_post_plan(sample_user, sample_team, sample_template_name):
    data = {
        "creator": sample_user,
        "name": sample_user + "-test-foo",
        "description": "Test plan for e2e test",
        "threshold_window": 900,
        "threshold_count": 10,
        "aggregation_window": 300,
        "aggregation_reset": 300,
        "steps": [
            [
                {
                    "role": "team",
                    "target": sample_team,
                    "priority": "low",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name
                },
                {
                    "role": "oncall-primary",
                    "target": sample_team,
                    "priority": "high",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name
                },
            ],
            [
                {
                    "role": "oncall-primary",
                    "target": sample_team,
                    "priority": "urgent",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name
                },
                {
                    "role": "team",
                    "target": sample_team,
                    "priority": "medium",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name
                },
            ]
        ],
        "isValid": True
    }
    # sort list so it's easier to compare
    data['steps'][0] = sorted(data['steps'][0], key=lambda x: x['priority'])
    data['steps'][1] = sorted(data['steps'][1], key=lambda x: x['priority'])
    data['steps'] = sorted(data['steps'], key=lambda x: x[0]['priority'] + x[1]['priority'])

    # Test post to plans endpoint (create plan)
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 201
    plan_id = re.content.strip()
    new_data = requests.get(base_url + 'plans/' + str(plan_id)).json()
    assert new_data['name'] == data['name']
    assert new_data['creator'] == data['creator']
    assert new_data['description'] == data['description']
    assert len(new_data['steps']) == len(data['steps'])
    new_data['steps'][0] = sorted(new_data['steps'][0], key=lambda x: x['priority'])
    new_data['steps'][1] = sorted(new_data['steps'][1], key=lambda x: x['priority'])
    new_data['steps'] = sorted(new_data['steps'], key=lambda x: x[0]['priority'] + x[1]['priority'])
    for k in ('role', 'target', 'priority', 'wait', 'repeat', 'template'):
        assert new_data['steps'][0][0][k] == data['steps'][0][0][k]
        assert new_data['steps'][0][1][k] == data['steps'][0][1][k]
        assert new_data['steps'][1][0][k] == data['steps'][1][0][k]
        assert new_data['steps'][1][1][k] == data['steps'][1][1][k]

    # Test post to plan endpoint (mark active/inactive)
    re = requests.post(base_url + 'plans/' + plan_id, json={'active': 0})
    assert re.status_code == 200
    assert re.content == '0'

    # Malformed requests
    re = requests.post(base_url + 'plans/' + plan_id, json={})
    assert re.status_code == 400

    re = requests.post(base_url + 'plans/' + plan_id, json={'active': 'fakeint'})
    assert re.status_code == 400

    re = requests.get(base_url + 'plans?active=0&name__contains=%s-test-foo&creator__eq=%s' % (sample_user, sample_user))
    assert re.status_code == 200
    # >= 1 because no database cleanup after test
    assert len(re.json()) >= 1

    re = requests.post(base_url + 'plans/' + plan_id, json={'active': 1})
    assert re.status_code == 200
    assert re.content == '1'

    # Test get plan endpoint (plan search)
    re = requests.get(base_url + 'plans?active=1&name__contains=%s-test-foo' % sample_user)
    assert re.status_code == 200
    assert len(re.json()) == 1

    # Test limit clause
    re = requests.get(base_url + 'plans?active=0&limit=1')
    assert re.status_code == 200
    assert len(re.json()) == 1

    # Test errors
    bad_step = {"role": "foo",
                "target": sample_team,
                "priority": "medium",
                "wait": 600,
                "repeat": 0,
                "template": sample_template_name}
    # Test bad role
    data['steps'][0][0] = bad_step
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 400
    assert re.json()['description'] == 'Role not found for step 1'

    # Test bad target
    bad_step['role'] = 'user'
    bad_step['target'] = 'nonexistentUser'
    data['steps'][0][0] = bad_step
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 400
    assert re.json()['description'] == 'Target nonexistentUser not found for step 1'

    # Test bad priority
    bad_step['target'] = sample_team
    bad_step['priority'] = 'foo'
    data['steps'][0][0] = bad_step
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 400
    assert re.json()['description'] == 'Priority not found for step 1'


def test_post_invalid_step_role(sample_user, sample_team, sample_template_name):
    data = {
        'creator': sample_user,
        'name': sample_user + '-test-foo',
        'description': 'Test plan for e2e test',
        'threshold_window': 900,
        'threshold_count': 10,
        'aggregation_window': 300,
        'aggregation_reset': 300,
        'steps': [
            [
                {
                    'role': 'oncall-primary',
                    'target': sample_user,
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_template_name
                },
            ],
        ],
        'isValid': True
    }
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 400
    assert re.json() == {'description': 'Role oncall-primary is not appropriate for target %s in step 1' % sample_user, 'title': 'Invalid role'}

    data = {
        'creator': sample_user,
        'name': sample_user + '-test-foo',
        'description': 'Test plan for e2e test',
        'threshold_window': 900,
        'threshold_count': 10,
        'aggregation_window': 300,
        'aggregation_reset': 300,
        'steps': [
            [
                {
                    'role': 'user',
                    'target': sample_team,
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_template_name
                },
            ],
        ],
        'isValid': True
    }
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 400
    assert re.json() == {'description': 'Role user is not appropriate for target %s in step 1' % sample_team, 'title': 'Invalid role'}


def test_post_incident(sample_user, sample_team, sample_application_name, sample_template_name):
    data = {
        "creator": sample_user,
        "name": sample_user + "-test-incident-post",
        "description": "Test plan for e2e test",
        "threshold_window": 900,
        "threshold_count": 10,
        "aggregation_window": 300,
        "aggregation_reset": 300,
        "steps": [
            [
                {
                    "role": "team",
                    "target": sample_team,
                    "priority": "low",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name
                },
                {
                    "role": "oncall-primary",
                    "target": sample_team,
                    "priority": "high",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name
                },
            ],
        ],
        "isValid": True
    }
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 201

    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    incident_id = int(re.content)
    assert re.status_code == 201
    re = requests.get(base_url + 'incidents/%s' % re.content.strip())
    assert re.status_code == 200

    re = requests.post(base_url + 'incidents/%d' % (incident_id, ), json={
        'owner': sample_user,
        'plan': sample_user + '-test-incident-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 200
    assert re.json() == {'owner': sample_user, 'incident_id': incident_id, 'active': False}


def test_post_incident_change_application(sample_user, sample_application_name, sample_application_name2, superuser_application):

    # superuser_application (iris-frontend) is allowed to create incidents as other apps, so this works
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-post',
        'context': {},
        'application': sample_application_name,
    }, headers={'Authorization': 'hmac %s:abc' % superuser_application})
    incident_id = int(re.content)
    assert re.status_code == 201
    re = requests.get(base_url + 'incidents/%s' % re.content.strip())
    assert re.status_code == 200
    assert re.json()['application'] == sample_application_name

    re = requests.post(base_url + 'incidents/%d' % (incident_id, ), json={
        'owner': sample_user,
        'plan': sample_user + '-test-incident-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 200
    assert re.json() == {'owner': sample_user, 'incident_id': incident_id, 'active': False}

    # sample_application_name2 is not allowed to make plans as sample_application_name, so this will fail
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-post',
        'context': {},
        'application': sample_application_name2,
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 403

    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-post',
        'context': {},
        'application': 'fakeapp234234',
    }, headers={'Authorization': 'hmac %s:abc' % superuser_application})
    assert re.status_code == 400


def test_post_incident_without_apps(sample_user, sample_team, sample_template_name, sample_application_name2):
    data = {
        "creator": sample_user,
        "name": sample_user + "-test-incident-post",
        "description": "Test plan for e2e test",
        "threshold_window": 900,
        "threshold_count": 10,
        "aggregation_window": 300,
        "aggregation_reset": 300,
        "steps": [
            [
                {
                    "role": "team",
                    "target": sample_team,
                    "priority": "low",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name
                },
            ],
        ],
        "isValid": True
    }
    re = requests.post(base_url + 'plans', json=data)
    assert re.status_code == 201

    # The application in sample_application_name2 does not have any sample_template_name templates, so this
    # will fail
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name2})
    assert re.status_code == 400


def test_post_incident_invalid_plan_name(sample_application_name):
    re = requests.post(base_url + 'incidents', json={
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 400

    re = requests.post(base_url + 'incidents', json={
        'plan': 'foo-123-xyz-adskhpb',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 404


def test_create_invalid_template(sample_user, sample_application_name):
    valid_template = {
        "creator": sample_user,
        "name": "test template",
        "content": {
            sample_application_name: {
                "call": {"subject": "", "body": "{{nodes}}"},
                "email": {"subject": "123", "body": "123"},
                "im": {"subject": "", "body": "123"},
                "sms": {"subject": "", "body": "123"}
            }
        }
    }

    invalid_template = valid_template.copy()
    del invalid_template['creator']
    re = requests.post(base_url + 'templates', json=invalid_template)
    assert re.status_code == 400
    assert re.json()['title'] == 'creator argument missing'

    invalid_template = valid_template.copy()
    del invalid_template['name']
    re = requests.post(base_url + 'templates', json=invalid_template)
    assert re.status_code == 400
    assert re.json()['title'] == 'name argument missing'


def test_active_incidents():
    re = requests.get(base_url + 'incidents?active=1')
    assert re.status_code == 200
    assert isinstance(re.json(), list)


def test_filter_incidents_by_creator(sample_user, sample_user2):
    re = requests.get(base_url + 'incidents?target=%s&target=%s' % (sample_user, sample_user2))
    assert re.status_code == 200
    data = re.json()
    assert isinstance(data, list)

    re = requests.get(base_url + 'incidents?target=' + sample_user)
    assert re.status_code == 200
    data = re.json()
    assert isinstance(data, list)


def test_api_get_nested_context(sample_user, sample_team, sample_template_name, sample_application_name):
    re = requests.post(base_url + 'plans', json={
        'name': 'test_nested_plan',
        'description': 'foo',
        'step_count': 0,
        'threshold_window': 1,
        'threshold_count': 1,
        'aggregation_window': 1,
        'aggregation_reset': 1,
        'steps': [
            [
                {
                    "role": "team",
                    "target": sample_team,
                    "priority": "low",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name
                },
            ],
        ],
        'creator': sample_user,
    })
    assert re.status_code == 201

    ctx = {
        "nodes": [
            {
                "device": "abc2-efg01.nw.example.com",
                "type": "BFD",
                "message": "bar",
                "component": "NA"
            },
        ],
    }
    re = requests.post(base_url + 'incidents', json={
        'plan': 'test_nested_plan',
        'context': ctx,
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})

    assert re.status_code == 201
    iid = re.content.strip()

    re = requests.get(base_url + 'incidents/' + iid)
    assert re.status_code == 200
    assert re.json()['context']['nodes'] == ctx['nodes']


def test_large_incident_context(sample_user, sample_application_name):
    re = requests.post(base_url + 'plans', json={
        'name': 'test_nested_plan',
        'description': 'foo',
        'step_count': 0,
        'threshold_window': 1,
        'threshold_count': 1,
        'aggregation_window': 1,
        'aggregation_reset': 1,
        'steps': [],
        'creator': sample_user,
    })
    assert re.status_code == 201

    ctx = {
        "nodes": [
            {
                "device": "abc2-efg01.nw.example.com" * 10000,
                "type": "BFD",
                "message": "bar",
                "component": "NA"
            },
        ],
    }
    re = requests.post(base_url + 'incidents', json={
        'plan': 'test_nested_plan',
        'context': ctx,
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})

    assert re.status_code == 400
    assert re.json()['title'] == 'Context too long'


def test_get_user_modes(sample_user, sample_application_name):
    session = requests.Session()
    session.headers = username_header(sample_user)

    re = session.get(base_url + 'users/modes/' + sample_user)
    assert re.status_code == 200
    assert sorted(re.json()) == sorted(['high', 'urgent', 'medium', 'low'])

    re = session.get(base_url + 'users/modes/%s?application=%s' % (sample_user, sample_application_name))
    assert re.status_code == 200
    assert sorted(re.json()) == sorted(['high', 'urgent', 'medium', 'low'])


def test_get_messages(iris_messages):
    if len(iris_messages) < 3:
        pytest.skip('Skipping this test as we don\'t have enough message IDs')

    re = requests.get(base_url + 'messages?id__in=' + ', '.join(str(m['id']) for m in iris_messages[:3])).json()
    assert len(re) == 3

    re = requests.get(base_url + 'messages?limit=1&id__in=' + ', '.join(str(m['id']) for m in iris_messages[:3])).json()
    assert len(re) == 1

    re = requests.get(base_url + 'messages?id__in=%s' % iris_messages[1]['id']).json()
    assert len(re) == 1
    assert re[0]['id'] == iris_messages[1]['id']

    re = requests.get(base_url + 'messages/%s' % iris_messages[0]['id']).json()
    assert re['id'] == iris_messages[0]['id']


def test_get_messages_not_found():
    re = requests.get(base_url + 'messages/0')
    assert re.status_code == 404


def test_get_incident(iris_incidents):
    if len(iris_incidents) < 3:
        pytest.skip('Skipping this test as we don\'t have enough incidents')

    re = requests.get(base_url + 'incidents?id__in=' + ', '.join(str(m['id']) for m in iris_incidents[:3])).json()
    assert len(re) == 3

    re = requests.get(base_url + 'incidents?limit=1&fields=id&id__in=' + ', '.join(str(m['id']) for m in iris_incidents[:3])).json()
    assert len(re) == 1

    re = requests.get(base_url + 'incidents?id__in=%s' % iris_incidents[1]['id']).json()
    assert len(re) == 1
    assert re[0]['id'] == iris_incidents[1]['id']

    re = requests.get(base_url + 'incidents/%s' % iris_incidents[0]['id']).json()
    assert re['id'] == iris_incidents[0]['id']

    re = requests.get(base_url + 'incidents/fakeid')
    assert re.status_code == 400

    re = requests.get(base_url + 'incidents/-1')
    assert re.status_code == 404


def test_post_user_modes(sample_user):
    session = requests.Session()
    session.headers = username_header(sample_user)

    change_to = {
        'high': 'default',
        'urgent': 'default',
        'medium': 'im',
        'low': 'call'
    }
    re = session.post(base_url + 'users/modes/' + sample_user, json=change_to)
    assert re.status_code == 200

    re = session.get(base_url + 'users/modes/' + sample_user)
    assert re.status_code == 200
    assert re.json() == change_to

    # Now test update/delete functionality
    change_to['medium'] = 'call'
    change_to['low'] = 'default'
    re = session.post(base_url + 'users/modes/' + sample_user, json=change_to)
    assert re.status_code == 200

    re = session.get(base_url + 'users/modes/' + sample_user)
    assert re.status_code == 200
    assert re.json() == change_to


def test_post_target_application_modes(sample_user, sample_application_name):
    session = requests.Session()
    session.headers = username_header(sample_user)

    mode_data = {
        'application': sample_application_name,
        'high': 'default',
        'urgent': 'default',
        'medium': 'im',
        'low': 'call'
    }
    modes = mode_data.copy()
    del modes['application']
    re = session.post(base_url + 'users/modes/' + sample_user,
                      json=mode_data)
    assert re.status_code == 200

    re = session.get(base_url + 'users/modes/%s?application=%s' % (sample_user, sample_application_name))
    assert re.status_code == 200
    assert re.json() == modes

    # Now test update/delete functionality
    mode_data['medium'] = 'call'
    mode_data['low'] = 'default'
    modes = mode_data.copy()
    del modes['application']

    re = session.post(base_url + 'users/modes/' + sample_user, json=mode_data)
    assert re.status_code == 200

    re = session.get(base_url + 'users/modes/%s?application=%s' % (sample_user, sample_application_name))
    assert re.status_code == 200
    assert re.json() == modes


def test_post_target_multiple_application_modes(sample_user, sample_application_name, sample_application_name2):
    session = requests.Session()
    session.headers = username_header(sample_user)

    # Set priorities for two apps in batch, as well as global defaults
    modes_per_app = {
        'per_app_modes': {
            sample_application_name: {
                'high': 'sms',
                'urgent': 'call',
                'medium': 'im',
                'low': 'call'
            },
            sample_application_name2: {
                'high': 'email',
                'urgent': 'email',
                'medium': 'im',
                'low': 'call'
            },
        },
        'high': 'call',
        'urgent': 'call',
        'medium': 'call',
        'low': 'call'
    }
    re = session.post(base_url + 'users/modes/' + sample_user, json=modes_per_app)
    assert re.status_code == 200

    re = session.get(base_url + 'users/' + sample_user)
    assert re.status_code == 200
    result = re.json()
    assert modes_per_app['per_app_modes'] == result['per_app_modes']
    assert all(result['modes'][key] == modes_per_app[key] for key in ['high', 'urgent', 'medium', 'low'])

    # Now try deleting both custom apps by setting all to default
    modes_per_app_delete = {
        'per_app_modes': {
            sample_application_name: {
                'high': 'default',
                'urgent': 'default',
                'medium': 'default',
                'low': 'default'
            },
            sample_application_name2: {
                'high': 'default',
                'urgent': 'default',
                'medium': 'default',
                'low': 'default'
            },
        },
        'high': 'default',
        'urgent': 'default',
        'medium': 'default',
        'low': 'default'
    }

    re = session.post(base_url + 'users/modes/' + sample_user, json=modes_per_app_delete)
    assert re.status_code == 200

    re = session.get(base_url + 'users/' + sample_user)
    assert re.status_code == 200
    result = re.json()
    assert {} == result['per_app_modes'] == result['modes']


def test_create_template(sample_user, sample_application_name):
    post_payload = {
        'creator': sample_user,
        'name': 'test_template',
        'content': {
            sample_application_name: {
                'sms': {'subject': '', 'body': 'test_sms'},
                'im': {'subject': '', 'body': 'test_im'},
                'call': {'subject': '', 'body': 'test_call'},
                'email': {'subject': 'email_subject', 'body': 'email_body'}
            }
        },
    }

    re = requests.post(base_url + 'templates/', json=post_payload)
    assert re.status_code == 201
    template_id = int(re.text)

    re = requests.get(base_url + 'templates/%d' % template_id)
    assert re.status_code == 200
    data = re.json()

    re = requests.get(base_url + 'templates/faketemplatethatdoesnotexist')
    assert re.status_code == 404

    for key in ['name', 'creator', 'content']:
        assert post_payload[key] == data[key]

    re = requests.post(base_url + 'templates/%d' % template_id, json={'active': 0})
    assert re.status_code == 200

    re = requests.post(base_url + 'templates/%d' % template_id, json={'active': 'sdfdsf'})
    assert re.status_code == 400

    re = requests.post(base_url + 'templates/%d' % template_id, json={})
    assert re.status_code == 400

    re = requests.get(base_url + 'templates?name=test_template&creator=%s&active=0' % sample_user)
    assert re.status_code == 200
    data = re.json()
    assert len(data) >= 1

    re = requests.get(base_url + 'templates?limit=1&name=test_template&creator=%s&active=0' % sample_user)
    assert re.status_code == 200
    data = re.json()
    assert len(data) == 1

    re = requests.post(base_url + 'templates/%d' % template_id, json={'active': 1})
    assert re.status_code == 200

    re = requests.get(base_url + 'templates?name=test_template&creator=%s&active=1' % sample_user)
    assert re.status_code == 200
    data = re.json()
    assert len(data) == 1


def test_get_targets(sample_user, sample_user2, sample_team, sample_team2):
    re = requests.get(base_url + 'targets')
    assert re.status_code == 200
    assert sample_user in re.json()

    re = requests.get(base_url + 'targets/team')
    assert re.status_code == 200
    assert sample_team in re.json()

    re = requests.get(base_url + 'targets/team?startswith=' + sample_team[:3])
    data = re.json()
    assert re.status_code == 200
    assert sample_team in data
    assert sample_team2 not in data

    re = requests.get(base_url + 'targets/user?startswith=' + sample_user[:3])
    data = re.json()
    assert re.status_code == 200
    assert sample_user in data
    assert sample_user2 not in data


@pytest.mark.skip(reason="reanble this test when we can programatically create noc user in the test")
def test_post_plan_noc(sample_user, sample_team, sample_application_name):
    data = {
        'creator': sample_user,
        'name': sample_user + '-test-foo',
        'description': 'Test plan for e2e test',
        'threshold_window': 900,
        'threshold_count': 10,
        'aggregation_window': 300,
        'aggregation_reset': 300,
        'steps': [],
        'isValid': True
    }

    invalid_steps = [
        [
            [
                {
                    'role': 'user',
                    'target': 'noc',
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_application_name
                }
            ],
            [
                {
                    'role': 'oncall-primary',
                    'target': sample_team,
                    'priority': 'high',
                    'wait': 300,
                    'repeat': 1,
                    'template': sample_application_name
                },
            ]
        ],
        [
            [
                {
                    'role': 'user',
                    'target': 'noc',
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_application_name
                },
            ]
        ],
    ]

    valid_steps = [
        [
            [
                {
                    'role': 'user',
                    'target': sample_user,
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_application_name
                }
            ],
        ],

        [
            [
                {
                    'role': 'user',
                    'target': sample_user,
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_application_name
                }
            ],
            [
                {
                    'role': 'manager',
                    'target': sample_team,
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_application_name
                }
            ],
            [
                {
                    'role': 'user',
                    'target': 'noc',
                    'priority': 'low',
                    'wait': 600,
                    'repeat': 0,
                    'template': sample_application_name
                }
            ],
        ],
    ]

    for steps in invalid_steps:
        _data = copy.deepcopy(data)
        _data['steps'] = steps
        re = requests.post(base_url + 'plans', json=_data)
        assert re.status_code == 400

    for steps in valid_steps:
        _data = copy.deepcopy(data)
        _data['steps'] = steps
        re = requests.post(base_url + 'plans', json=_data)
        assert re.status_code == 201


def test_get_applications(sample_application_name):
    app_keys = set(['variables', 'required_variables', 'name', 'context_template', 'summary_template', 'sample_context', 'default_modes', 'supported_modes', 'owners'])
    # TODO: insert application data before get
    re = requests.get(base_url + 'applications/' + sample_application_name)
    assert re.status_code == 200
    app = re.json()
    assert isinstance(app, dict)
    assert set(app.keys()) == app_keys

    re = requests.get(base_url + 'applications')
    assert re.status_code == 200
    apps = re.json()
    assert isinstance(apps, list)
    assert len(apps) > 0
    for app in apps:
        assert set(app.keys()) == app_keys


def test_update_reprioritization_settings(sample_user):
    session = requests.Session()
    session.headers = username_header(sample_user)

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': '1', 'duration': '120'})
    assert re.status_code == 200
    re = session.get(base_url + 'users/reprioritization/' + sample_user)
    assert re.status_code == 200
    rules = re.json()
    assert len(rules) == 1
    rule = rules[0]
    assert rule['src_mode'] == 'call'
    assert rule['dst_mode'] == 'sms'
    assert rule['count'] == 1
    assert rule['duration'] == 120

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'fakesrc', 'dst_mode': 'sms', 'count': '1', 'duration': '120'})
    assert re.json()['title'] == 'Invalid source mode.'
    assert re.status_code == 400

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'fakedst', 'count': '1', 'duration': '120'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid destination mode.'

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'missingargs': 'foo'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Missing argument'

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': '1', 'duration': '1'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid duration'

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': '1', 'duration': '3601'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid duration'

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': '1', 'duration': 'fakeint'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid duration'

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': 'fakeint', 'duration': '3600'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid count'

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': '-10', 'duration': '3600'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid count'

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': '300', 'duration': '3600'})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid count'


def test_delete_reprioritization_settings(sample_user):
    session = requests.Session()
    session.headers = username_header(sample_user)

    re = session.post(base_url + 'users/reprioritization/' + sample_user,
                      json={'src_mode': 'call', 'dst_mode': 'sms', 'count': '1', 'duration': '120'})
    assert re.status_code == 200

    re = session.get(base_url + 'users/reprioritization/' + sample_user)
    assert re.status_code == 200
    assert 'call' in set(rule['src_mode'] for rule in re.json())

    re = session.delete(base_url + 'users/reprioritization/%s/call' % sample_user)
    assert re.status_code == 200

    re = session.get(base_url + 'users/reprioritization/' + sample_user)
    assert re.status_code == 200
    assert 'call' not in set(rule['src_mode'] for rule in re.json())

    re = session.delete(base_url + 'users/reprioritization/%s/call' % sample_user)
    assert re.status_code == 404


def test_get_modes():
    re = requests.get(base_url + 'modes')
    assert re.status_code == 200
    data = re.json()
    assert 'sms' in data
    assert 'email' in data
    assert 'call' in data
    assert 'im' in data
    assert 'drop' not in data


def test_get_target_roles():
    re = requests.get(base_url + 'target_roles')
    assert re.status_code == 200
    data = re.json()
    expected_set = set(['oncall-primary', 'manager', 'team', 'user', 'oncall-secondary'])
    assert expected_set <= set([r['name'] for r in data])


def test_get_priorities():
    re = requests.get(base_url + 'priorities')
    assert re.status_code == 200
    data = re.json()
    data = set([d['name'] for d in data])
    assert 'low' in data
    assert 'medium' in data
    assert 'high' in data
    assert 'urgent' in data


def test_get_user(sample_user, sample_email, sample_admin_user):
    re = requests.get(base_url + 'users/' + sample_user, headers=username_header(sample_user))
    assert re.status_code == 200
    data = re.json()
    assert data.viewkeys() == {'teams', 'modes', 'per_app_modes', 'admin', 'contacts', 'name'}
    assert data['contacts']['email'] == sample_email
    assert data['name'] == sample_user

    re = requests.get(base_url + 'users/' + sample_admin_user, headers=username_header(sample_admin_user))
    assert re.status_code == 200
    assert re.json()['admin'] is True


def test_healthcheck():
    with open('/tmp/status', 'w') as f:
        f.write('GOOD')
    re = requests.get(server + 'healthcheck')
    assert re.status_code == 200
    assert re.content == 'GOOD'


def test_stats():
    re = requests.get(base_url + 'stats')
    assert re.status_code == 200
    data = re.json()
    for key in ['total_active_users', 'total_messages_sent_today', 'total_incidents_today', 'total_messages_sent', 'total_incidents', 'total_plans']:
        assert key in data
        assert isinstance(data[key], int)


def test_post_notification(sample_user, sample_application_name):
    re = requests.post(base_url + 'notifications', json={})
    assert re.status_code == 400
    assert 'Missing required atrributes' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
    })
    assert re.status_code == 400
    assert 'Both priority and mode are missing' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'priority': 'fakepriority'
    })
    assert re.status_code == 400
    assert 'Invalid priority' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'mode': 'fakemode'
    })
    assert re.status_code == 400
    assert 'Invalid mode' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'priority': 'low'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'


def test_modify_applicaton_quota(sample_application_name, sample_admin_user, sample_plan_name):
    if not all([sample_application_name, sample_admin_user, sample_plan_name]):
        pytest.skip('We do not have enough data in DB to do this test')

    body = {
        'hard_quota_threshold': 5,
        'soft_quota_threshold': 3,
        'hard_quota_duration': 60,
        'soft_quota_duration': 60,
        'plan_name': sample_plan_name,
        'target_name': sample_admin_user,
        'wait_time': 10
    }

    re = requests.post(base_url + 'applications/%s/quota' % sample_application_name, json=body, headers=username_header(sample_admin_user))
    assert re.status_code == 201

    re = requests.get(base_url + 'applications/%s/quota' % sample_application_name)
    assert re.status_code == 200

    data = re.json()
    assert all(data[key] == body[key] for key in body)

    body['hard_quota_duration'] = 66
    body['soft_quota_duration'] = 65

    re = requests.post(base_url + 'applications/%s/quota' % sample_application_name, json=body, headers=username_header(sample_admin_user))
    assert re.status_code == 201

    re = requests.get(base_url + 'applications/%s/quota' % sample_application_name)
    assert re.status_code == 200

    data = re.json()
    assert all(data[key] == body[key] for key in body)

    re = requests.delete(base_url + 'applications/%s/quota' % sample_application_name, headers=username_header(sample_admin_user))
    assert re.status_code == 204

    re = requests.get(base_url + 'applications/%s/quota' % sample_application_name)
    assert re.status_code == 404


def test_modify_application(sample_application_name, sample_admin_user, sample_user, sample_mode):
    if not all([sample_application_name, sample_admin_user, sample_user, sample_mode]):
        pytest.skip('We do not have enough data in DB to do this test')

    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.status_code == 200
    current_settings = re.json()

    temp_test_variable = 'testvar2'

    if temp_test_variable not in current_settings['variables']:
        current_settings['variables'].append(temp_test_variable)

    try:
        json.loads(current_settings['sample_context'])
    except ValueError:
        current_settings['sample_context'] = '{}'

    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.status_code == 200
    assert set(re.json()['variables']) == set(current_settings['variables'])

    current_settings['variables'] = list(set(current_settings['variables']) - {temp_test_variable})

    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.status_code == 200
    assert set(re.json()['variables']) == set(current_settings['variables'])

    current_settings['sample_context'] = 'sdfdsf234234'
    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'sample_context must be valid json'

    # Take sample_user out of list of owners and set that
    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.status_code == 200
    current_settings = re.json()
    current_settings['owners'] = list(set(current_settings['owners']) - {sample_user})
    assert sample_user not in current_settings['owners']
    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    # Verify that user isn't there
    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert sample_user not in re.json()['owners']

    # add it back to the list of owners and ensure it's there
    current_settings['owners'] = list(set(current_settings['owners']) | {sample_user})
    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.status_code == 200
    current_settings = re.json()
    assert sample_user in current_settings['owners']

    # Same for mode
    current_settings['supported_modes'] = list(set(current_settings['supported_modes']) - {sample_mode})
    assert sample_mode not in current_settings['supported_modes']

    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    # Verify that mode isn't there
    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert sample_mode not in re.json()['supported_modes']

    # Put it back and verify
    current_settings['supported_modes'] = list(set(current_settings['supported_modes']) | {sample_mode})
    assert sample_mode in current_settings['supported_modes']

    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    # Verify that mode is there
    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert sample_mode in re.json()['supported_modes']


@pytest.mark.skip(reason="Re-enable this when we don't hard-code primary keys")
class TestDelete(object):
    def setup_method(self, method):
        with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
            cursor.execute("INSERT INTO template(`id`, `name`, `created`, `user_id`)"
                           "VALUES (1, 'foobar', '2015-09-25 22:54:31', 8)")
            cursor.execute("INSERT INTO plan(`id`, `name`, `created`, `user_id`, `step_count`)"
                           "VALUES (2, 'foobar', '2015-09-25 22:54:31', 8, 3)")
            cursor.execute("INSERT INTO plan_active (`name`, `plan_id`) VALUES ('foobar', 2)")
            cursor.execute("INSERT INTO message(`id`, `created`, `application_id`, "
                           "`target_id`, `plan_id`, `priority_id`, `template_id`)"
                           "VALUES (1, '2015-09-25 22:54:31', 8, 8, 2, 8, 1)")
            cursor.execute("INSERT INTO plan_notification(id, plan_id, step, template_id, target_id, role_id, priority_id)"
                           "VALUES (1, 2, 1, 1, 8, 8, 8)")
            cursor.execute("INSERT INTO incident(`id`, `plan_id`, `created`, `application_id`, `current_step`, `active`)"
                           "VALUES (1, 2, '2015-09-25 22:54:31', 8, 1, 1)")
            conn.commit()

    def teardown_method(self, method):
        with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
            cursor.execute("DELETE FROM plan_notification WHERE id = 1")
            cursor.execute("DELETE FROM message WHERE id = 1")
            cursor.execute("DELETE FROM incident WHERE id = 1")
            cursor.execute("DELETE FROM plan_active WHERE plan_id = 2")
            cursor.execute("DELETE FROM template WHERE id = 1")
            cursor.execute("DELETE FROM plan WHERE id = 2")
            conn.commit()

    def test_delete_template(self):
        # Test for correct error output
        runner = CliRunner()
        result = runner.invoke(iris_ctl.template, ['delete', 'foobar', '--config=../configs/config.dev.yaml'], input='y\n')
        assert result.exit_code == 1
        assert 'messages with ids:\n[1]' in result.output_bytes
        assert 'plans with ids:\n[2]' in result.output_bytes

        with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
            # Test failure with only message referencing template
            cursor.execute("DELETE FROM plan_notification WHERE id = 1")
            conn.commit()
            result = runner.invoke(iris_ctl.template, ['delete', 'foobar', '--config=../configs/config.dev.yaml'],
                                   input='y\n')
            assert result.exit_code == 1

            # Test failure with only plan referencing template
            cursor.execute("INSERT INTO plan_notification(id, plan_id, step, template_id, target_id, role_id, priority_id)"
                           "VALUES (1, 29, 1, 1, 8, 8, 8)")
            cursor.execute("DELETE FROM message WHERE id = 1")
            conn.commit()
            result = runner.invoke(iris_ctl.template, ['delete', 'foobar', '--config=../configs/config.dev.yaml'],
                                   input='y\n')
            assert result.exit_code == 1

            # Test success
            cursor.execute("DELETE FROM plan_notification WHERE id = 1")
            conn.commit()
            result = runner.invoke(iris_ctl.template, ['delete', 'foobar', '--config=../configs/config.dev.yaml'],
                                   input='y\n')
            cursor.execute("SELECT id FROM template WHERE name = 'foobar'")
            assert cursor.rowcount == 0
            assert result.exit_code == 0

    def test_delete_plan(self):
        # Test for correct error output
        runner = CliRunner()
        result = runner.invoke(iris_ctl.plan, ['delete', 'foobar', '--config=../configs/config.dev.yaml'], input='y\n')
        assert result.exit_code == 1
        assert 'messages with ids:\n[1]' in result.output_bytes
        assert 'incidents with ids:\n[1]' in result.output_bytes

        with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
            # Test failure with only message referencing plan
            cursor.execute("DELETE FROM incident WHERE id = 1")
            conn.commit()
            result = runner.invoke(iris_ctl.plan, ['delete', 'foobar', '--config=../configs/config.dev.yaml'],
                                   input='y\n')
            assert result.exit_code == 1

            # Test failure with only incident referencing plan
            cursor.execute("INSERT INTO incident(`id`, `plan_id`, `created`, `application_id`, `current_step`, `active`)"
                           "VALUES (1, 2, '2015-09-25 22:54:31', 8, 1, 1)")
            cursor.execute("DELETE FROM message WHERE id = 1")
            conn.commit()
            result = runner.invoke(iris_ctl.plan, ['delete', 'foobar', '--config=../configs/config.dev.yaml'],
                                   input='y\n')
            assert result.exit_code == 1

            # Test success
            cursor.execute("DELETE FROM incident WHERE id = 1")
            conn.commit()
            result = runner.invoke(iris_ctl.plan, ['delete', 'foobar', '--config=../configs/config.dev.yaml'],
                                   input='y\n')
            cursor.execute("SELECT id FROM plan WHERE name = 'foobar'")
            assert cursor.rowcount == 0
            cursor.execute("SELECT plan_id FROM plan_active WHERE name ='foobar'")
            assert cursor.rowcount == 0
            cursor.execute("SELECT id FROM plan_notification WHERE plan_id = 2")
            assert result.exit_code == 0
