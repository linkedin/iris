#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

import pytest
import json
import requests
import copy
import logging
import iris.bin.iris_ctl as iris_ctl
import iris.bin.app_stats as app_stats

from click.testing import CliRunner
import uuid
import socket


server = 'http://localhost:16649/'
sender_address = ('localhost', 2321)
base_url = server + 'v0/'
ui_url = server

invalid_role = '_invalid_role'
invalid_user = '_invalid_user'
invalid_mailing_list = '_invalid_mailing_list'

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
        cursor.execute('SELECT `id`, `incident_id` FROM `message` WHERE NOT ISNULL(`incident_id`) AND NOT ISNULL(`destination`) ORDER BY `id` DESC LIMIT 3')
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
        cursor.execute('''SELECT `batch`
                          FROM `message`
                          WHERE NOT ISNULL(`incident_id`)
                              AND NOT ISNULL(`batch`) LIMIT 1''')
        result = cursor.fetchall()
        if not result:
            return None
        return result[0][0]


@pytest.fixture(scope='module')
def fake_iris_number():
    return '+1 444-444-4444'


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
def iris_mailing_lists():
    '''List of all iris mailing-lists'''
    re = requests.get(base_url + 'targets/mailing-list')
    assert re.status_code == 200
    return re.json()


@pytest.fixture(scope='module')
def iris_applications():
    '''List of all iris applications' metadata'''
    re = requests.get(base_url + 'applications')
    assert re.status_code == 200
    return re.json()


@pytest.fixture(scope='module')
def sample_mailing_list_0(iris_mailing_lists):
    return iris_mailing_lists[0]


@pytest.fixture(scope='module')
def sample_mailing_list_1(iris_mailing_lists):
    return iris_mailing_lists[1]


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
def sample_phone2(sample_user2):
    '''Email address of sample_user2'''
    re = requests.get(base_url + 'users/' + sample_user2, headers=username_header(sample_user2))
    assert re.status_code == 200
    data = re.json()
    return data['contacts']['call']


@pytest.fixture(scope='module')
def superuser_application():
    '''
    application which should have 'allow_other_app_incidents' in DB set to 1,
    allowing it to create incidents as other applications. should generally be 'iris'
    '''
    return 'iris'


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
def sample_plan_name(sample_application_name):
    '''Get a plan name that is guaranteed to work with our sample_application_name'''

    if not sample_application_name:
        return None

    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute(
            '''SELECT `name`
               FROM `plan_active` WHERE
               EXISTS (
                   SELECT 1
                   FROM `plan_notification`
                   JOIN `template` ON `template`.`name` = `plan_notification`.`template`
                   JOIN `template_content` ON `template_content`.`template_id` = `template`.`id`
                   WHERE `plan_notification`.`plan_id` = `plan_active`.`plan_id`
                   AND `template_content`.`application_id` = (
                       SELECT `id` FROM `application` WHERE `name` = %s
                   )
               ) LIMIT 1''',
            [sample_application_name])
        result = cursor.fetchone()
        if result:
            return result[0]


@pytest.fixture(scope='module')
def sample_plan_name2(sample_application_name2, sample_application_name):
    '''Get a plan name that is guaranteed to work with our sample_application_name2 and guaranteed to not work with sample_application_name'''

    if not sample_application_name2 or not sample_application_name:
        return None

    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('''SELECT `name`
                          FROM `plan_active` WHERE
                          EXISTS (
                              SELECT 1 FROM
                              `plan_notification`
                              JOIN `template` ON `template`.`name` = `plan_notification`.`template`
                              JOIN `template_content` ON `template_content`.`template_id` = `template`.`id`
                              WHERE `plan_notification`.`plan_id` = `plan_active`.`plan_id`
                              AND `template_content`.`application_id` = (SELECT `id` FROM `application` WHERE `name` = %s)
                          )
                          AND NOT EXISTS(
                              SELECT 1 FROM
                              `plan_notification`
                              JOIN `template` ON `template`.`name` = `plan_notification`.`template`
                              JOIN `template_content` ON `template_content`.`template_id` = `template`.`id`
                              WHERE `plan_notification`.`plan_id` = `plan_active`.`plan_id`
                              AND `template_content`.`application_id` = (SELECT `id` FROM `application` WHERE `name` = %s)
                          ) LIMIT 1''', [sample_application_name2, sample_application_name])
        result = cursor.fetchone()
        if result:
            return result[0]


@pytest.fixture(scope='module')
def sample_mode():
    '''List of iris messages'''
    modes = requests.get(base_url + 'modes').json()
    if modes:
        return modes[0]


@pytest.fixture(scope='module')
def sample_priority():
    ''' A sample priority '''
    priorities = requests.get(base_url + 'priorities').json()
    if priorities:
        return priorities[0]['name']


def create_incident_with_message(application, plan, targets, mode):

    if isinstance(targets, list):
        multiple_users = True
    else:
        targets = [targets]
        multiple_users = False

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
        conn.commit()

        users_to_messages = {}

        for target in targets:
            cursor.execute('''INSERT INTO `message` (`created`, `application_id`, `target_id`, `priority_id`, `mode_id`, `active`, `incident_id`)
                              VALUES(
                                      NOW(),
                                      (SELECT `id` FROM `application` WHERE `name` = %(application)s),
                                      (SELECT `id` FROM `target` WHERE `name` = %(target)s AND `type_id` = (SELECT `id` FROM `target_type` WHERE `name` = 'user')),
                                      (SELECT `id` FROM `priority` WHERE `name` = 'low'),
                                      (SELECT `id` FROM `mode` WHERE `name` = %(mode)s),
                                      TRUE,
                                      %(incident_id)s
                              )''', {'application': application, 'target': target, 'mode': mode, 'incident_id': incident_id})
            message_id = cursor.lastrowid
            assert message_id
            users_to_messages[target] = message_id
            conn.commit()

        if multiple_users:
            return incident_id, users_to_messages
        else:
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


def test_api_response_phone_call(fake_message_id, fake_incident_id, sample_phone, fake_iris_number):
    if not all([fake_message_id, fake_incident_id, sample_phone]):
        pytest.skip('We do not have enough data in DB to do this test')

    data = {
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'To': sample_phone,
        'ToZip': 15108,
        'FromState': 'CA',
        'Digits': 2,
        'From': fake_iris_number,
    }

    re = requests.post(base_url + 'response/twilio/calls', params={
        'message_id': fake_message_id,
    }, data=data)
    assert re.status_code == 200
    assert re.json()['app_response'].startswith('Iris incident(%s) claimed' % fake_incident_id)


def test_api_response_batch_phone_call(fake_batch_id, sample_phone, fake_iris_number):
    if not all([fake_batch_id, sample_phone]):
        pytest.skip('Failed finding a batch ID to use for tests')

    data = {
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'To': sample_phone,
        'ToZip': 15108,
        'FromState': 'CA',
        'Digits': '2',
        'From': fake_iris_number,
    }

    re = requests.post(base_url + 'response/twilio/calls', params={
        'message_id': fake_batch_id,
    }, data=data)
    assert re.status_code == 200
    assert re.content.decode('utf-8') == '{"app_response":"All iris incidents claimed for batch id %s."}' % fake_batch_id


def test_api_response_sms(fake_message_id, fake_incident_id, sample_phone):
    if not all([fake_message_id, fake_incident_id, sample_phone]):
        pytest.skip('Failed finding a batch ID to use for tests')

    base_body = {
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': sample_phone,
    }

    data = base_body.copy()
    data['Body'] = '%s    claim arg1 arg2' % fake_message_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.json()['app_response'].startswith('Iris incident(%s) claimed' % fake_incident_id)

    data = base_body.copy()
    data['Body'] = 'Claim   %s claim arg1 arg2' % fake_message_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.json()['app_response'].startswith('Iris incident(%s) claimed' % fake_incident_id)

    data = base_body.copy()
    data['Body'] = fake_message_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid response'

    data = base_body.copy()
    data['Body'] = 'f'

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.json()['app_response'] == 'Sincerest apologies'


def test_api_response_batch_sms(fake_batch_id, sample_phone):
    if not fake_batch_id:
        pytest.skip('Failed finding a batch ID to use for tests')

    base_body = {
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': sample_phone,
    }

    data = base_body.copy()
    data['Body'] = '%s claim arg1 arg2' % fake_batch_id

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.content.decode('utf-8') == '{"app_response":"All iris incidents claimed for batch id %s."}' % fake_batch_id

    data = base_body.copy()
    data['Body'] = '%s claim arg1 arg2' % '*(fasdf'
    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 400


def test_api_response_claim_all(sample_user, sample_phone, sample_application_name, sample_application_name2, sample_plan_name, sample_email):
    if not all([sample_user, sample_phone, sample_application_name, sample_plan_name]):
        pytest.skip('Not enough data for this test')

    sms_claim_all_body = {
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': sample_phone,
        'Body': 'claim all'
    }

    sms_claim_all_body_2 = {
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
        'From': sample_phone,
        'Body': 'a'
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
    assert re.status_code == 200

    # Shouldn't be any incidents. Verify response in this case.
    re = requests.post(base_url + 'response/twilio/messages', data=sms_claim_all_body)
    assert re.status_code == 200
    assert re.json()['app_response'] == 'No active incidents to claim.'

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
    assert re.json()['app_response'] in ('Iris Incidents claimed (2): %s, %s' % (incident_id_1, incident_id_2),
                                         'Iris Incidents claimed (2): %s, %s' % (incident_id_2, incident_id_1))

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

    # Verify SMS with two incidents from different apps, using one-letter response
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
    re = requests.post(base_url + 'response/twilio/messages', data=sms_claim_all_body_2)
    assert re.status_code == 200
    assert set(re.json()['app_response'].splitlines()) == {'%s: Iris Incidents claimed (1): %s' % (sample_application_name, incident_id_1),
                                                           '%s: Iris Incidents claimed (1): %s' % (sample_application_name2, incident_id_2)}

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
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
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
        'body': 'l',
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


def test_api_response_already_claimed(sample_user, sample_phone, sample_user2, sample_phone2, sample_application_name, sample_plan_name, sample_email):
    incident_id, message_ids = create_incident_with_message(sample_application_name, sample_plan_name, [sample_user, sample_user2], 'sms')
    assert incident_id
    assert message_ids

    base_body = {
        'AccountSid': 'ACBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
        'ToZip': 15108,
        'FromState': 'CA',
        'ApiVersion': '2010-04-01',
    }

    # First user should be able to the claim the incident without issue using claim all
    data = base_body.copy()
    data['Body'] = 'claim all'
    data['From'] = sample_phone

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.json()['app_response'] == 'Iris Incidents claimed (1): %s' % incident_id

    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200
    assert re.json()['active'] == 0

    # Second person trying to claim all should get no incidents found
    data = base_body.copy()
    data['Body'] = 'claim all'
    data['From'] = sample_phone2

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.json()['app_response'] == 'No active incidents to claim.'

    # They try again using claim by ID and that incident was already claimed by first person
    data = base_body.copy()
    data['Body'] = 'claim %s' % message_ids[sample_user2]
    data['From'] = sample_phone2

    re = requests.post(base_url + 'response/twilio/messages', data=data)
    assert re.status_code == 200
    assert re.json()['app_response'] == 'Iris incident(%s) claimed, previously claimed by %s.' % (incident_id, sample_user)


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
        'body': 'I\u0131d claim',
        'headers': [
            {'name': 'From', 'value': sample_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }
    re = requests.post(base_url + 'response/gmail', json=data)
    assert re.status_code == 400


def test_plan_routing():
    re = requests.get(base_url + 'plans/TESTDOOOOT')
    assert re.content == b""
    assert re.status_code == 404


def test_post_plan(sample_user, sample_team, sample_template_name):
    re = requests.post(base_url + 'plans', json={'name': ' '})
    assert re.status_code == 400
    assert re.json()['description'] == 'Empty plan name'

    re = requests.post(base_url + 'plans', json={'name': '1234'})
    assert re.status_code == 400
    assert re.json()['description'] == 'Plan name cannot be a number'

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
                    "template": sample_template_name,
                    "optional": 0
                },
                {
                    "role": "oncall-primary",
                    "target": sample_team,
                    "priority": "high",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name,
                    "optional": 1
                },
            ],
            [
                {
                    "role": "oncall-primary",
                    "target": sample_team,
                    "priority": "urgent",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name,
                },
                {
                    "role": "team",
                    "target": sample_team,
                    "priority": "medium",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name,
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
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201
    plan_id = re.content.strip().decode('utf-8')
    new_data = requests.get(base_url + 'plans/' + plan_id).json()
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
    assert re.content == b'0'

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
    assert re.content == b'1'

    # Test get plan endpoint (plan search)
    re = requests.get(base_url + 'plans?active=1&name__contains=%s-test-foo' % sample_user)
    assert re.status_code == 200
    assert len(re.json()) == 1

    # Test get plan endpoint with invalid fields
    re = requests.get(base_url + 'plans?active=1&name__contains=%s-test-foo&foo=bar' % sample_user)
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
                "template": sample_template_name,
                "optional": 0}
    # Test bad role
    data['steps'][0][0] = bad_step
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json()['description'] == 'Role not found for step 1'

    # Test bad target
    bad_step['role'] = 'user'
    bad_step['target'] = invalid_user
    data['steps'][0][0] = bad_step
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json()['description'] == 'Target %s not found for step 1' % invalid_user

    # Test bad priority
    bad_step['target'] = sample_team
    bad_step['priority'] = 'foo'
    data['steps'][0][0] = bad_step
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json()['description'] == 'Priority not found for step 1'

    # Test bad all optional
    bad_step['role'] = 'team'
    bad_step['target'] = sample_team
    bad_step['priority'] = 'medium'
    bad_step['optional'] = 1
    data['steps'][0][0] = bad_step
    data['steps'][0][1] = bad_step
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json()['description'] == 'You must have at least one non-optional notification per step. Step 1 has none.'


def test_post_dynamic_plan(sample_user, sample_team, sample_template_name):
    data = {
        "creator": sample_user,
        "name": sample_user + "-test-dynamic-foo",
        "description": "Test plan for e2e test",
        "threshold_window": 900,
        "threshold_count": 10,
        "aggregation_window": 300,
        "aggregation_reset": 300,
        "steps": [
            [
                {
                    "dynamic_index": 0,
                    "priority": "low",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name,
                },
                {
                    "dynamic_index": 1,
                    "priority": "high",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name,
                },
            ],
            [
                {
                    "dynamic_index": 0,
                    "priority": "urgent",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name,
                },
                {
                    "dynamic_index": 1,
                    "priority": "medium",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name,
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
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201
    plan_id = int(re.content.strip())
    new_data = requests.get(base_url + 'plans/' + str(plan_id)).json()
    assert new_data['name'] == data['name']
    assert new_data['creator'] == data['creator']
    assert new_data['description'] == data['description']
    assert len(new_data['steps']) == len(data['steps'])
    new_data['steps'][0] = sorted(new_data['steps'][0], key=lambda x: x['priority'])
    new_data['steps'][1] = sorted(new_data['steps'][1], key=lambda x: x['priority'])
    new_data['steps'] = sorted(new_data['steps'], key=lambda x: x[0]['priority'] + x[1]['priority'])
    for k in ('dynamic_index', 'priority', 'wait', 'repeat', 'template'):
        assert new_data['steps'][0][0][k] == data['steps'][0][0][k]
        assert new_data['steps'][0][1][k] == data['steps'][0][1][k]
        assert new_data['steps'][1][0][k] == data['steps'][1][0][k]
        assert new_data['steps'][1][1][k] == data['steps'][1][1][k]

    # Test errors
    bad_step = {"dynamic_index": 100,
                "priority": "medium",
                "wait": 600,
                "repeat": 0,
                "template": sample_template_name,
                "optional": 0}
    # Test bad dynamic target index
    data['steps'][0][0] = bad_step
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json()['description'] == 'Dynamic target numbers must span 0..n without gaps'


def test_delete_plan(sample_user, sample_team, sample_template_name, sample_application_name):
    re = requests.delete(base_url + 'plans/fake-plan-name-12345', headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'No plan matched'

    re = requests.delete(base_url + 'plans/02342342412345', headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'No plan matched'

    data = {
        'creator': sample_user,
        'name': sample_user + '-test-to-delete',
        'description': 'Test plan for e2e test',
        'threshold_window': 900,
        'threshold_count': 10,
        'aggregation_window': 300,
        'aggregation_reset': 300,
        'steps': [
            [
                {
                    'role': 'team',
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

    # Test creating and deleting by ID
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201
    plan_id = int(re.content.strip())
    assert plan_id

    re = requests.get(base_url + 'plans/%s' % plan_id)
    assert re.status_code == 200

    re = requests.delete(base_url + 'plans/%s' % plan_id, headers=username_header(sample_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'plans/%s' % plan_id)
    assert re.status_code == 404

    # Test creating and deleting by name
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201
    plan_id = int(re.content.strip())
    assert plan_id

    re = requests.get(base_url + 'plans/%s' % plan_id)
    assert re.status_code == 200

    re = requests.delete(base_url + 'plans/%s' % data['name'], headers=username_header(sample_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'plans/%s' % plan_id)
    assert re.status_code == 404

    # Test failing to delete because incidents
    data_cant_kill = data.copy()
    data_cant_kill['name'] += '-but-cant'

    re = requests.post(base_url + 'plans', json=data_cant_kill, headers=username_header(sample_user))
    assert re.status_code == 201
    plan_id = int(re.content.strip())
    assert plan_id

    assert create_incident_with_message(sample_application_name, data_cant_kill['name'], sample_user, 'email')

    re = requests.delete(base_url + 'plans/%s' % data_cant_kill['name'], headers=username_header(sample_user))
    assert re.status_code == 400
    assert 'incidents have been created using it' in re.json()['title']


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
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
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
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 400
    assert re.json() == {'description': 'Role user is not appropriate for target %s in step 1' % sample_team, 'title': 'Invalid role'}


def test_post_incident(sample_user, sample_team, sample_application_name, sample_template_name, superuser_application):
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
                    "template": sample_template_name,
                    "optional": 0
                },
                {
                    "role": "oncall-primary",
                    "target": sample_team,
                    "priority": "high",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name,
                    "optional": 0
                },
            ],
        ],
        "isValid": True
    }
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201

    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    incident_id = int(re.content)
    assert re.status_code == 201
    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200

    # Test claiming incident
    re = requests.post(base_url + 'incidents/%d' % (incident_id, ), json={
        'owner': sample_user,
        'plan': sample_user + '-test-incident-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % superuser_application})
    assert re.status_code == 200
    assert re.json() == {'owner': sample_user, 'incident_id': incident_id, 'active': False}

    # Test claim via batch endpoint
    re = requests.post(base_url + 'incidents/claim', json={
        'owner': sample_user,
        'incident_ids': [incident_id]
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 200
    assert re.json() == {'owner': sample_user, 'claimed': [incident_id], 'unclaimed': []}

    # Invalid claim owner
    re = requests.post(base_url + 'incidents/%d' % incident_id, json={
        'owner': invalid_user,
    }, headers={'Authorization': 'hmac %s:abc' % superuser_application})
    assert re.status_code == 400
    assert re.json()['title'] == 'Invalid claim: no matching owner'


def test_post_dynamic_incident(sample_user, sample_team, sample_application_name, sample_template_name):
    data = {
        "creator": sample_user,
        "name": sample_user + "-test-incident-dynamic-post",
        "description": "Test plan for e2e test",
        "threshold_window": 900,
        "threshold_count": 10,
        "aggregation_window": 300,
        "aggregation_reset": 300,
        "steps": [
            [
                {
                    "dynamic_index": 0,
                    "priority": "low",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name,
                    "optional": 0
                },
                {
                    "dynamic_index": 1,
                    "priority": "high",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name,
                    "optional": 0
                },
            ],
        ],
        "isValid": True
    }
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201

    # Create incident
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-dynamic-post',
        'context': {},
        'dynamic_targets': [{'role': 'user', 'target': sample_user},
                            {'role': 'team', 'target': sample_team}]
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    incident_id = int(re.content)
    assert re.status_code == 201
    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200

    # Claim
    re = requests.post(base_url + 'incidents/%d' % (incident_id, ), json={
        'owner': sample_user,
    }, headers=username_header(sample_user))
    assert re.status_code == 200
    assert re.json() == {'owner': sample_user, 'incident_id': incident_id, 'active': False}

    # Test errors
    # Invalid role:target combination
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-dynamic-post',
        'context': {},
        'dynamic_targets': [{'role': 'user', 'target': sample_user},
                            {'role': 'user', 'target': sample_team}]
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 400
    assert re.json() == {'description': 'invalid role %s for target %s' % ('user', sample_team),
                         'title': 'Invalid incident'}

    # Not enough targets
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-dynamic-post',
        'context': {},
        'dynamic_targets': [{'role': 'user', 'target': sample_user}]
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 400
    assert re.json() == {'title': 'Invalid number of dynamic targets'}

    # No targets specified
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-dynamic-post',
        'context': {}
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 400
    assert re.json() == {'title': 'Invalid number of dynamic targets'}

    # Too many targets
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-dynamic-post',
        'context': {},
        'dynamic_targets': [{'role': 'user', 'target': sample_user},
                            {'role': 'user', 'target': sample_team},
                            {'role': 'user', 'target': sample_user}]
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 400
    assert re.json() == {'title': 'Invalid number of dynamic targets'}


def test_post_incident_change_application(sample_user, sample_application_name, sample_application_name2, superuser_application):

    # superuser_application (iris-frontend) is allowed to create incidents as other apps, so this works
    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-incident-post',
        'context': {},
        'application': sample_application_name,
    }, headers={'Authorization': 'hmac %s:abc' % superuser_application})
    incident_id = int(re.content)
    assert re.status_code == 201
    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200
    assert re.json()['application'] == sample_application_name

    re = requests.post(base_url + 'incidents/%d' % (incident_id, ), json={
        'owner': sample_user,
        'plan': sample_user + '-test-incident-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % superuser_application})
    assert re.status_code == 200
    assert re.json() == {'owner': sample_user, 'incident_id': incident_id, 'active': False}

    # sample_application_name2 is not allowed to make incidents as sample_application_name, so this will fail
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
                    "template": sample_template_name,
                    "optional": 0
                },
            ],
        ],
        "isValid": True
    }
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
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
                    "template": sample_template_name,
                    "optional": 0
                },
            ],
        ],
        'creator': sample_user,
    }, headers=username_header(sample_user))
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

    re = requests.get(base_url + 'incidents/' + iid.decode('utf-8'))
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
    }, headers=username_header(sample_user))
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
    assert re.json()['title'] == 'Context too large. 250198 is larger than limit 65535'


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


def test_get_invalid_incident(iris_incidents):
    if len(iris_incidents) < 1:
        pytest.skip('Skipping this test as we don\'t have enough incidents')

    re = requests.get(base_url + 'incidents?id=job')
    assert re.status_code == 400
    assert b'id should be <class \'int\'>' in re.content


def test_post_user_modes(sample_user):
    session = requests.Session()
    session.headers = username_header(sample_user)

    change_to = {
        'high': 'default',
        'urgent': 'default',
        'medium': 'slack',
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
        'medium': 'slack',
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
                'medium': 'slack',
                'low': 'call'
            },
            sample_application_name2: {
                'high': 'email',
                'urgent': 'email',
                'medium': 'slack',
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
                'slack': {'subject': '', 'body': 'test_slack'},
                'call': {'subject': '', 'body': 'test_call'},
                'email': {'subject': 'email_subject', 'body': 'email_body'}
            }
        },
    }

    re = requests.post(base_url + 'templates/', json=post_payload, headers=username_header(sample_user))
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

    re = requests.get(base_url + 'targets/user?name=' + sample_user)
    data = re.json()
    assert re.status_code == 200
    assert sample_user in data
    assert sample_user2 not in data

    re = requests.get(base_url + 'targets/team?name=' + sample_team)
    data = re.json()
    assert re.status_code == 200
    assert sample_team in data
    assert sample_team2 not in data


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
    app_keys = set([
        'variables', 'required_variables', 'name', 'context_template', 'summary_template',
        'sample_context', 'default_modes', 'supported_modes', 'owners', 'title_variable',
        'mobile_template', 'custom_sender_addresses', 'categories'])
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
    assert 'slack' in data
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
    assert data.keys() == {'teams', 'modes', 'per_app_modes', 'admin', 'contacts', 'name', 'template_overrides'}
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
    assert re.content == b'GOOD'


def test_stats():
    re = requests.get(base_url + 'stats')
    assert re.status_code == 200

    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        # run stats script
        app_stats.logger.setLevel(logging.ERROR)
        app_stats.stats_task(conn, cursor)
        # check that gobal stats were initiated
        cursor.execute('SELECT DISTINCT statistic FROM global_stats')
        # there should be 10 unique statistics calculated
        assert cursor.rowcount == 10


def test_app_stats(sample_application_name):

    re = requests.get(base_url + 'applications/sfsdf232423fakeappname/stats')
    assert re.status_code == 400

    re = requests.get(base_url + 'applications/%s/stats' % sample_application_name)
    assert re.status_code == 200

    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        # run stats script
        app_stats.stats_task(conn, cursor)
        app_stats.logger.setLevel(logging.ERROR)
        # check that app stats were initialized
        cursor.execute('SELECT DISTINCT statistic FROM application_stats')
        # there should be 22 unique statistics calculated
        assert cursor.rowcount == 22


def test_post_invalid_notification(sample_user, sample_application_name):
    # The iris-api in this case will send a request to iris-sender's
    # rpc endpoint. Don't bother if sender isn't working.
    try:
        sock = socket.socket()
        sock.connect(sender_address)
        sock.close()
    except socket.error:
        pytest.skip('Skipping this test as sender is not running/reachable.')

    re = requests.post(base_url + 'notifications', json={})
    assert re.status_code == 400
    assert 'Missing required atrributes' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'body': 'foo'
    })
    assert re.status_code == 400
    assert 'Priority, mode, and category are missing' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'priority': 'fakepriority',
        'body': 'foo'
    })
    assert re.status_code == 400
    assert 'Invalid priority' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'mode': 'fakemode',
        'body': 'foo'
    })
    assert re.status_code == 400
    assert 'Invalid mode' in re.text

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'priority': 'low',
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 400
    assert re.json()['title'] == 'body, template, and email_html are missing, so we cannot construct message.'

    re = requests.post(base_url + 'notifications', json={
        'role': invalid_role,
        'target': sample_user,
        'subject': 'test',
        'priority': 'low',
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 400
    assert re.json()['description'] == 'INVALID role:target'

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': invalid_user,
        'subject': 'test',
        'priority': 'low',
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 400
    assert re.json()['description'] == 'INVALID role:target'

    re = requests.post(base_url + 'notifications', json={
        'role': 'literal_target',
        'target': 'sample_mailinglist@email.com',
        'subject': 'test',
        'priority': 'low',
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 400
    assert re.json()['title'] == 'INVALID mode not set for literal_target role'

    re = requests.post(base_url + 'notifications', json={
        'role': 'literal_target',
        'target': 'sample_mailinglist@email.com',
        'subject': 'test',
        'mode': 'email',
        'priority': 'low',
        'email_html': 'foobar',
        'body': '',
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 400
    assert re.json()['title'] == 'INVALID role literal_target does not support priority or category'

    re = requests.post(base_url + 'notifications', json={
        'mode': 'email',
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'email_html': ['foo']
    })
    assert re.status_code == 400
    assert 'email_html needs to be a string' in re.text


def test_post_notification(sample_user, sample_team, sample_application_name):
    # The iris-api in this case will send a request to iris-sender's
    # rpc endpoint. Don't bother if sender isn't working.
    try:
        sock = socket.socket()
        sock.connect(sender_address)
        sock.close()
    except socket.error:
        pytest.skip('Skipping this test as sender is not running/reachable.')

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'priority': 'low',
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.text == '[]'
    assert re.status_code == 200

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'priority': 'low',
        'mode': 'email',
        'email_html': 'foobar',
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'priority': 'low',
        'mode': 'email',
        'email_html': 'foobar',
        'body': '',
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'

    re = requests.post(base_url + 'notifications', json={
        'role': 'literal_target',
        'target': 'sample_mailinglist@email.com',
        'subject': 'test',
        'mode': 'email',
        'email_html': 'foobar',
        'body': '',
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'

    # Multi-recipent notification should succeed
    re = requests.post(base_url + 'notifications', json={
        'target_list': [{'role': 'user', 'target': sample_user},
                        {'role': 'team', 'target': sample_team},
                        {'role': 'literal_target', 'target': 'foobar@example.com', 'bcc': True}],
        'subject': 'test',
        'mode': 'email',
        'body': 'foo'},
        headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'
    assert re.status_code == 200
    assert re.text == '[]'

    # Multi-recipent notification with all literal targets should succeed
    re = requests.post(base_url + 'notifications', json={
        'target_list': [{'role': 'literal_target', 'target': 'barbaz@example.com'},
                        {'role': 'literal_target', 'target': 'foobar@example.com'}],
        'subject': 'test',
        'mode': 'email',
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'

    # Multi-recipent notification with one invalid target should still succeed
    re = requests.post(base_url + 'notifications', json={
        'target_list': [{'role': 'user', 'target': 'invalid-user-foobar'},
                        {'role': 'user', 'target': sample_user}],
        'subject': 'test',
        'mode': 'email',
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'

    # Should return 400 for multi-recipient notification specifying priority
    re = requests.post(base_url + 'notifications', json={
        'target_list': [{'role': 'user', 'target': sample_user},
                        {'role': 'team', 'target': sample_team},
                        {'role': 'literal_target', 'target': 'foobar@example.com'}],
        'subject': 'test',
        'priority': 'low',
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 400

    # Should return 400 for multi-recipient notification with missing subject
    re = requests.post(base_url + 'notifications', json={
        'target_list': [{'role': 'user', 'target': sample_user},
                        {'role': 'team', 'target': sample_team},
                        {'role': 'literal_target', 'target': 'foobar@example.com'}],
        'body': 'foo'
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 400


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
    assert re.status_code == 200
    assert re.json() == {}


def test_modify_application(sample_application_name, sample_admin_user, sample_user, sample_mode, sample_priority):
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

    # Same for default mode per priority per this app

    # Wipe the default modes
    current_settings['default_modes'] = {}
    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    # Verify none are set
    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.json()['default_modes'] == {}

    # Set one
    current_settings['default_modes'] = {sample_priority: sample_mode}
    re = requests.put(base_url + 'applications/%s' % sample_application_name, json=current_settings, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    # Verify its set
    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.json()['default_modes'] == {sample_priority: sample_mode}
    assert re.status_code == 200


def test_create_application(sample_admin_user, sample_application_name):
    if not all([sample_admin_user, sample_application_name]):
        pytest.skip('We do not have enough data in DB to do this test')

    re = requests.post(base_url + 'applications', json={'name': sample_application_name}, headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'This app already exists'

    temp_app_name = 'e2e-temp-app'

    # Ensure the app doesn't exist before we begin
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('''DELETE FROM `application` WHERE `name` = %s''', temp_app_name)
        conn.commit()

    re = requests.get(base_url + 'applications/%s' % temp_app_name)
    assert re.status_code == 400
    assert re.json()['title'] == 'Application %s not found' % temp_app_name

    re = requests.post(base_url + 'applications', json={'name': temp_app_name}, headers=username_header(sample_admin_user))
    assert re.status_code == 201
    assert re.json()['id']

    re = requests.get(base_url + 'applications/%s' % temp_app_name)
    assert re.status_code == 200

    # Ensure the random key got created correctly
    re = requests.get(base_url + 'applications/%s/key' % temp_app_name, headers=username_header(sample_admin_user))
    assert re.status_code == 200
    assert len(re.json()['key']) == 64

    # Kill the temp app
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('''DELETE FROM `application` WHERE `name` = %s''', temp_app_name)
        conn.commit()

    re = requests.get(base_url + 'applications/%s' % temp_app_name)
    assert re.status_code == 400
    assert re.json()['title'] == 'Application %s not found' % temp_app_name


def test_application_plans(sample_user, sample_template_name, sample_application_name, sample_application_name2):
    if not all([sample_admin_user, sample_application_name, sample_application_name2]):
        pytest.skip('We do not have enough data in DB to do this test')

    plan_name = sample_user + '-test-foo'
    data = {
        "creator": sample_user,
        "name": plan_name,
        "description": "Test plan for e2e test",
        "threshold_window": 900,
        "threshold_count": 10,
        "aggregation_window": 300,
        "aggregation_reset": 300,
        "steps": [
            [
                {
                    "role": "user",
                    "target": sample_user,
                    "priority": "low",
                    "wait": 600,
                    "repeat": 0,
                    "template": sample_template_name,
                    "optional": 0
                }
            ]
        ],
        "isValid": True
    }
    # Create plan
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201

    # Check that plan appears for sample app 1
    re = requests.get(base_url + 'applications/%s/plans' % sample_application_name)
    assert re.status_code == 200
    resp_data = re.json()
    plan_names = {plan['name'] for plan in resp_data}
    assert plan_name in plan_names

    # Check that plan appears with name filter
    re = requests.get(base_url + 'applications/%s/plans?name__startswith=%s' % (sample_application_name, plan_name))
    assert re.status_code == 200
    resp_data = re.json()
    plan_names = {plan['name'] for plan in resp_data}
    assert plan_name in plan_names

    # Check that plan does not appear for sample app 2
    re = requests.get(base_url + 'applications/%s/plans' % sample_application_name2)
    assert re.status_code == 200
    resp_data = re.json()
    plan_names = {plan['name'] for plan in resp_data}
    assert plan_name not in plan_names


def test_rename_application(sample_admin_user, sample_application_name, sample_application_name2):
    if not all([sample_admin_user, sample_application_name, sample_application_name2]):
        pytest.skip('We do not have enough data in DB to do this test')

    temp_app_name = 'e2e-rename-app'

    # Test the sanity checks
    re = requests.put(base_url + 'applications/%s/rename' % temp_app_name,
                      json={},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'Missing new_name from post body'

    re = requests.put(base_url + 'applications/%s/rename' % temp_app_name,
                      json={'new_name': temp_app_name},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'New and old app name are identical'

    re = requests.put(base_url + 'applications/fakeapp123/rename',
                      json={'new_name': temp_app_name},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'No rows changed; old app name incorrect'

    # Rename our sample app to the new temp name
    re = requests.put(base_url + 'applications/%s/rename' % sample_application_name,
                      json={'new_name': temp_app_name},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s' % temp_app_name)
    assert re.status_code == 200

    # Ensure the old version doesn't exist anymore
    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.status_code == 400
    assert re.json()['title'] == 'Application %s not found' % sample_application_name

    # Put it back now
    re = requests.put(base_url + 'applications/%s/rename' % temp_app_name,
                      json={'new_name': sample_application_name},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s' % sample_application_name)
    assert re.status_code == 200

    # Ensure we can't rename over another app
    re = requests.put(base_url + 'applications/%s/rename' % sample_application_name,
                      json={'new_name': sample_application_name2},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'Destination app name likely already exists'


def test_delete_application(sample_admin_user):
    if not sample_admin_user:
        pytest.skip('We do not have enough data in DB to do this test')

    temp_app_name = 'e2e-delete-app'

    # Ensure we don't already have it
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('''DELETE FROM `application` WHERE `name` = %s''', temp_app_name)
        conn.commit()

    re = requests.get(base_url + 'applications/%s' % temp_app_name)
    assert re.status_code == 400
    assert re.json()['title'] == 'Application %s not found' % temp_app_name

    # Create application
    re = requests.post(base_url + 'applications', json={'name': temp_app_name}, headers=username_header(sample_admin_user))
    assert re.status_code == 201
    assert re.json()['id']

    re = requests.get(base_url + 'applications/%s' % temp_app_name)
    assert re.status_code == 200

    # Delete it
    re = requests.delete(base_url + 'applications/%s' % temp_app_name, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    # Is it really gone?
    re = requests.get(base_url + 'applications/%s' % temp_app_name)
    assert re.status_code == 400
    assert re.json()['title'] == 'Application %s not found' % temp_app_name


def test_view_app_key(sample_application_name, sample_admin_user):
    re = requests.get(base_url + 'applications/%s/key' % sample_application_name)
    assert re.status_code == 401
    assert re.json()['title'] == 'You must be a logged in user to view this app\'s key'

    re = requests.get(base_url + 'applications/fakeapp124324/key', headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'Key for this application not found'

    re = requests.get(base_url + 'applications/%s/key' % sample_application_name, headers=username_header(sample_admin_user))
    assert re.status_code == 200
    assert re.json().keys() == {'key'}


def test_change_app_key(sample_application_name, sample_admin_user):
    re = requests.post(base_url + 'applications/%s/rekey' % sample_application_name)
    assert re.status_code == 401
    assert re.json()['title'] == 'You must be a logged in user to re-key this app'

    re = requests.post(base_url + 'applications/%s/rekey' % 'fakeapp123', headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'Re-key failed; secondary key does not exist or invalid app name'

    re = requests.post(base_url + 'applications/%s/rekey' % sample_application_name, headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'Re-key failed; secondary key does not exist or invalid app name'

    re = requests.post(base_url + 'applications/%s/secondary' % sample_application_name, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s/secondary' % sample_application_name, headers=username_header(sample_admin_user))
    assert re.status_code == 200
    secondary_key = re.json()['key']
    assert secondary_key

    re = requests.get(base_url + 'applications/%s/key' % sample_application_name, headers=username_header(sample_admin_user))
    old_key = re.json()['key']
    assert old_key

    re = requests.post(base_url + 'applications/%s/rekey' % sample_application_name, headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s/key' % sample_application_name, headers=username_header(sample_admin_user))
    assert re.status_code == 200
    new_key = re.json()['key']
    assert new_key

    assert old_key != new_key
    assert new_key == secondary_key


def test_twilio_delivery_update(fake_message_id):
    if not fake_message_id:
        pytest.skip('We do not have enough data in DB to do this test')

    # Wouldn't surprise me if this is how twilio actually generates the SID on their end
    message_sid = uuid.uuid4().hex

    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('''DELETE FROM `twilio_delivery_status` WHERE `message_id` = %s''', fake_message_id)
        cursor.execute('''INSERT INTO `twilio_delivery_status` (`twilio_sid`, `message_id`)
                          VALUES (%s, %s)''', (message_sid, fake_message_id))
        conn.commit()

    re = requests.post(base_url + 'twilio/deliveryupdate', data={'MessageSid': message_sid, 'MessageStatus': 'delivered'})
    assert re.status_code == 204

    re = requests.get(base_url + 'messages/%s' % fake_message_id)
    assert re.status_code == 200
    assert re.json()['twilio_delivery_status'] == 'delivered'


def test_twilio_retry(fake_message_id):
    if not fake_message_id:
        pytest.skip('We do not have enough data in DB to do this test')

    message_sid = uuid.uuid4().hex

    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('''DELETE FROM `twilio_delivery_status` WHERE `message_id` = %s''', fake_message_id)
        cursor.execute('''INSERT INTO `twilio_delivery_status` (`twilio_sid`, `message_id`)
                          VALUES (%s, %s)''', (message_sid, fake_message_id))
        cursor.execute('''DELETE FROM `twilio_retry` WHERE `retry_id` = %(msg_id)s OR `message_id` = %(msg_id)s''',
                       {'msg_id': fake_message_id})
        conn.commit()

    re = requests.post(base_url + 'twilio/deliveryupdate', data={'MessageSid': message_sid, 'MessageStatus': 'failed'})
    assert re.status_code == 204

    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('SELECT `message_id`, `retry_id` FROM `twilio_retry` WHERE `message_id` = %s', fake_message_id)
        assert cursor.rowcount == 1
        row = cursor.fetchone()
        assert row[0] == fake_message_id
        retry_id = row[1]
        cursor.execute('SELECT EXISTS(SELECT 1 FROM `message` WHERE `id` = %s)', retry_id)
        assert cursor.fetchone()[0] == 1
        retry_sid = uuid.uuid4().hex
        cursor.execute('''INSERT INTO `twilio_delivery_status` (`twilio_sid`, `message_id`)
                          VALUES (%s, %s)''', (retry_sid, retry_id))
        conn.commit()

    re = requests.post(base_url + 'twilio/deliveryupdate', data={'MessageSid': retry_sid, 'MessageStatus': 'failed'})
    assert re.status_code == 204

    # Check failed retry doesn't create another retry
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('SELECT `message_id`, `retry_id` FROM `twilio_retry` WHERE `message_id` = %s', retry_id)
        assert cursor.rowcount == 0
        # Clean up retry message
        cursor.execute('DELETE FROM `message` WHERE `id` = %s', retry_id)
        conn.commit()

    re = requests.get(base_url + 'messages/%s' % fake_message_id)
    assert re.status_code == 200
    assert re.json()['twilio_delivery_status'] == 'failed'


def test_configure_email_incidents(sample_application_name, sample_application_name2, sample_plan_name, sample_plan_name2, sample_email, sample_admin_user):
    if not (sample_application_name and sample_application_name2):
        pytest.skip('Need at least two applications to do this test')
    if not (sample_plan_name and sample_plan_name2):
        pytest.skip('Need at least one plan using each of the sample applications: %s, %s' % (
            sample_application_name, sample_application_name2
        ))
    if not sample_email or not sample_admin_user:
        pytest.skip('We do not have enough data in DB to do this test')

    # Test wiping incident email addresses for an app
    re = requests.put(base_url + 'applications/%s/incident_emails' % sample_application_name,
                      json={},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s/incident_emails' % sample_application_name)
    assert re.status_code == 200
    assert re.json() == {}

    # Block trying to set a users email to create an incident
    re = requests.put(base_url + 'applications/%s/incident_emails' % sample_application_name,
                      json={sample_email: sample_plan_name},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'These email addresses are also user\'s email addresses which is not allowed: %s' % sample_email

    special_email = 'specialfoo@foomail.com'

    # Test setting an email address + plan name combination for an app successfully
    re = requests.put(base_url + 'applications/%s/incident_emails' % sample_application_name,
                      json={special_email: sample_plan_name},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.get(base_url + 'applications/%s/incident_emails' % sample_application_name)
    assert re.status_code == 200
    assert re.json()[special_email] == sample_plan_name

    # Block one application stealing another application's email
    re = requests.put(base_url + 'applications/%s/incident_emails' % sample_application_name2,
                      json={special_email: sample_plan_name2},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'These email addresses are already in use by another app: %s' % special_email

    # Block using an unsupported plan for a specific app
    re = requests.put(base_url + 'applications/%s/incident_emails' % sample_application_name,
                      json={special_email: sample_plan_name2},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 400
    assert re.json()['title'] == 'Failed adding %s -> %s combination. This plan does not have any templates which support this app.' % (special_email, sample_plan_name2)


def test_create_incident(sample_plan_name, sample_application_name):
    re = requests.post(base_url + 'incidents',
                       json={"plan": sample_plan_name, "context": {}},
                       headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    assert re.status_code == 201
    incident_id = re.json()
    assert incident_id
    re = requests.get(base_url + 'incidents/%d' % incident_id)
    assert re.status_code == 200


def test_create_incident_by_email(sample_application_name, sample_plan_name, sample_plan_name2, sample_admin_user):
    if not sample_application_name or not sample_plan_name or not sample_plan_name2 or not sample_email:
        pytest.skip('We do not have enough data in DB to do this test')

    special_email = 'irisfoobar@fakeemail.com'

    # Ensure this email is configured properly.
    re = requests.put(base_url + 'applications/%s/incident_emails' % sample_application_name,
                      json={special_email: sample_plan_name},
                      headers=username_header(sample_admin_user))
    assert re.status_code == 200

    email_make_incident_payload = {
        'body': 'This is a new test incident with a test message to be delivered to people.',
        'headers': [
            {'name': 'From', 'value': 'foo@bar.com'},
            {'name': 'To', 'value': special_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }

    re = requests.post(base_url + 'response/gmail', json=email_make_incident_payload)
    assert re.status_code == 204
    assert re.headers['X-IRIS-INCIDENT'].isdigit()

    re = requests.get(base_url + 'incidents/%s' % re.headers['X-IRIS-INCIDENT'])
    assert re.status_code == 200
    data = re.json()
    assert data['context']['body'] == email_make_incident_payload['body']
    assert data['context']['email'] == [special_email]
    assert data['context']['subject'] == 'fooject'
    assert data['application'] == sample_application_name
    assert data['plan'] == sample_plan_name

    # Try it again with a customized fancy To header
    email_make_incident_payload = {
        'body': 'This is a new test incident with a test message to be delivered to people.',
        'headers': [
            {'name': 'From', 'value': 'foo@bar.com'},
            {'name': 'To', 'value': 'Email Mailing List Of Doom <%s>' % special_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }

    re = requests.post(base_url + 'response/gmail', json=email_make_incident_payload)
    assert re.status_code == 204
    assert re.headers['X-IRIS-INCIDENT'].isdigit()

    # Also try creating an incident with an an email that's a reply to the
    # thread, which shouldn't work
    email_make_incident_payload = {
        'body': 'This string should not become an incident',
        'headers': [
            {'name': 'From', 'value': 'foo@bar.com'},
            {'name': 'To', 'value': special_email},
            {'name': 'Subject', 'value': 'fooject'},
            {'name': 'In-Reply-To', 'value': 'messagereference'},
        ]
    }

    re = requests.post(base_url + 'response/gmail', json=email_make_incident_payload)
    assert re.status_code == 204
    assert re.headers['X-IRIS-INCIDENT'] == 'Not created (email reply not fresh email)'

    # Also try creating an incident with a plan target'ing an unsupported app,
    # which will cause problems later
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute(
            '''INSERT INTO `incident_emails` (`email`, `plan_name`, `application_id`)
               VALUES (
                   %(email)s,
                   %(plan)s,
                   (SELECT `id` FROM `application` WHERE `name` = %(application)s)
               )
               ON DUPLICATE KEY UPDATE `application_id` = (
                       SELECT `id` FROM `application` WHERE `name` = %(application)s
                    ),
                    `plan_name` = %(plan)s''',
            {
                'application': sample_application_name,
                'plan': sample_plan_name2,
                'email': special_email
            })
        conn.commit()

    email_make_incident_payload = {
        'body': 'This string should not become an incident',
        'headers': [
            {'name': 'From', 'value': 'foo@bar.com'},
            {'name': 'To', 'value': special_email},
            {'name': 'Subject', 'value': 'fooject'},
        ]
    }

    re = requests.post(base_url + 'response/gmail', json=email_make_incident_payload)
    assert re.status_code == 204
    assert re.headers['X-IRIS-INCIDENT'] == 'Not created (no template actions for this app)'

    # Clean up that deliberately broken DB entry
    with iris_ctl.db_from_config(sample_db_config) as (conn, cursor):
        cursor.execute('DELETE FROM `incident_emails` WHERE `email` = %s', [special_email])
        conn.commit()


def test_ui_routes_redirect(sample_user, sample_admin_user):
    # When not logged in, various pages redirect to login page
    re = requests.get(ui_url + 'user', allow_redirects=False)
    assert re.status_code == 302
    assert re.headers['Location'] == '/login/?next=%2Fuser'

    re = requests.get(ui_url + 'incidents', allow_redirects=False)
    assert re.status_code == 302
    assert re.headers['Location'] == '/login/?next=%2Fincidents'

    re = requests.get(ui_url, allow_redirects=False)
    assert re.status_code == 302
    assert re.headers['Location'] == '/login/'


def test_ui_route_login_page(sample_user, sample_admin_user):
    # And login page displays itself
    re = requests.get(ui_url + 'login', allow_redirects=False)
    assert re.status_code == 200


def test_ui_routes(sample_user, sample_admin_user):
    # And allows itself to work & login & set the beaker session cookie
    re = requests.post(ui_url + 'login', allow_redirects=False, data={'username': sample_user, 'password': 'foo'})
    assert re.status_code == 302
    assert re.headers['Location'] == '/incidents'
    assert 'iris-auth' in re.cookies

    # Similarly it obeys the next GET param
    re = requests.post(ui_url + 'login/?next=%2Fuser', allow_redirects=False, data={'username': sample_user, 'password': 'foo'})
    assert re.status_code == 302
    assert re.headers['Location'] == '/user'
    assert 'iris-auth' in re.cookies

    # When logged in, home page redirects to /incidents
    re = requests.get(ui_url, allow_redirects=False, headers=username_header(sample_user))
    assert re.status_code == 302
    assert re.headers['Location'] == '/incidents'

    # And other pages display themselves, and have the username specified in javascript
    re = requests.get(ui_url + 'incidents', allow_redirects=False, headers=username_header(sample_user))
    assert re.status_code == 200
    assert re.headers['content-type'] == 'text/html'
    assert ' appData.user = "%s";' % sample_user in re.text

    # When passed an admin user, the admin flag should be "true"
    re = requests.get(ui_url + 'incidents', allow_redirects=False, headers=username_header(sample_admin_user))
    assert re.status_code == 200
    assert re.headers['content-type'] == 'text/html'
    assert ' appData.user = "%s";' % sample_admin_user in re.text
    assert ' appData.user_admin = true;' in re.text

    # And logout redirects to login page
    re = requests.get(ui_url + 'logout', allow_redirects=False, headers=username_header(sample_user))
    assert re.status_code == 302
    assert re.headers['Location'] == '/login'

    # And login redirects to home page
    re = requests.get(ui_url + 'login', allow_redirects=False, headers=username_header(sample_user))
    assert re.status_code == 302
    assert re.headers['Location'] == '/incidents'

    # Test actual login + logout session using beaker's cookies in requests session, rather than using the header trick:
    session = requests.Session()

    re = session.post(ui_url + 'login', allow_redirects=False, data={'username': sample_user, 'password': 'foo'})
    assert re.status_code == 302
    assert re.headers['Location'] == '/incidents'
    assert 'iris-auth' in session.cookies

    re = session.get(ui_url + 'incidents', allow_redirects=False)
    assert re.status_code == 200
    assert re.headers['content-type'] == 'text/html'
    assert ' appData.user = "%s";' % sample_user in re.text

    re = session.get(ui_url + 'logout', allow_redirects=False)
    assert re.status_code == 302
    assert re.headers['Location'] == '/login'
    assert 'iris-auth' not in session.cookies


def test_ui_assets():
    re = requests.get(ui_url + 'static/images/iris.png', allow_redirects=False)
    assert re.status_code == 200
    assert re.headers['content-type'] == 'image/png'

    re = requests.get(ui_url + 'static/bundles/iris.css', allow_redirects=False)
    assert re.status_code == 200
    assert re.headers['content-type'] == 'text/css'

    re = requests.get(ui_url + 'static/bundles/iris.js', allow_redirects=False)
    assert re.status_code == 200
    assert re.headers['content-type'] == 'text/javascript'

    re = requests.get(ui_url + 'static/fonts/glyphicons-halflings-regular.woff', allow_redirects=False)
    assert re.status_code == 200
    assert re.headers['content-type'] == 'application/font-woff'


def test_timezones_list():
    re = requests.get(base_url + 'timezones', allow_redirects=False)
    assert re.status_code == 200
    assert isinstance(re.json(), list)


def test_valid_target(sample_user, sample_mailing_list_1):
    # Test invalid user
    re = requests.get(base_url + 'targets/' + invalid_user + '/exists',
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert not re.json()['exists']

    # Test valid user
    re = requests.get(base_url + 'targets/' + sample_user + '/exists',
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert re.json()['exists']

    # Test valid mailing-list
    re = requests.get(base_url + 'targets/' + sample_mailing_list_1 + '/exists',
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert re.json()['exists']

    # Test invalid mailing-list
    re = requests.get(base_url + 'targets/' + invalid_mailing_list + '/exists',
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert not re.json()['exists']


def test_list_membership(sample_user, sample_mailing_list_0,
                         sample_mailing_list_1):
    # sample_user(demo) is a part of sample_mailing_list_1(demo)
    re = requests.get(base_url + 'users/' + sample_user + '/in_lists',
                      params={'list': [sample_mailing_list_1]},
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert re.json()['is_member']

    # sample_user(demo) is NOT a part of sample_mailing_list_0(abc)
    re = requests.get(base_url + 'users/' + sample_user + '/in_lists',
                      params={'list': [sample_mailing_list_0]},
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert not re.json()['is_member']

    # check multiple lists
    re = requests.get(base_url + 'users/' + sample_user + '/in_lists',
                      params={'list': [sample_mailing_list_0,
                                       sample_mailing_list_1]},
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert re.json()['is_member']

    # check invalid multiple lists
    re = requests.get(base_url + 'users/' + sample_user + '/in_lists',
                      params={'list': [invalid_mailing_list]},
                      headers=username_header(sample_user))
    assert re.status_code == 200
    assert not re.json()['is_member']


def test_user_update_timezone(sample_user):
    re = requests.get(base_url + 'timezones', allow_redirects=False)
    timezones = list(set(re.json()))

    if len(timezones) < 2:
        pytest.skip('Skipping timezone test as we have no timezones configured')

    session = requests.Session()
    session.headers = username_header(sample_user)

    # Change it to the first one and see if it sticks
    re = session.put(base_url + 'users/settings/' + sample_user,
                     json={'timezone': timezones[0]})
    assert re.status_code == 204

    re = session.get(base_url + 'users/settings/' + sample_user)
    assert re.status_code == 200
    assert re.json()['timezone'] == timezones[0]

    # Then change it to another one and see if that one sticks
    re = session.put(base_url + 'users/settings/' + sample_user,
                     json={'timezone': timezones[1]})
    assert re.status_code == 204

    re = session.get(base_url + 'users/settings/' + sample_user)
    assert re.status_code == 200
    assert re.json()['timezone'] == timezones[1]


def test_user_update_sms_override(sample_user):

    session = requests.Session()
    session.headers = username_header(sample_user)

    # Change it to enabled and see if it sticks
    re = session.post(base_url + 'users/overrides/' + sample_user,
                      json={'template_overrides': {'sms': 'enabled'}})
    assert re.status_code == 204

    re = session.get(base_url + 'users/' + sample_user)
    assert re.status_code == 200
    assert 'sms' in re.json()['template_overrides']

    # Change it to disabled and see if it sticks
    re = session.post(base_url + 'users/overrides/' + sample_user,
                      json={'template_overrides': {'sms': 'disabled'}})
    assert re.status_code == 204

    re = session.get(base_url + 'users/' + sample_user)
    assert re.status_code == 200
    assert 'sms' not in re.json()['template_overrides']

    # test bad request
    re = session.post(base_url + 'users/overrides/' + sample_user,
                      json={'template_overrides': {'invalid_mode': 'disabled'}})
    assert re.status_code == 400


def test_comment(sample_user, sample_team, sample_application_name, sample_template_name):
    data = {
        "creator": sample_user,
        "name": sample_user + "-test-comment-post",
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
                    "template": sample_template_name,
                    "optional": 0
                },
                {
                    "role": "oncall-primary",
                    "target": sample_team,
                    "priority": "high",
                    "wait": 300,
                    "repeat": 1,
                    "template": sample_template_name,
                    "optional": 0
                },
            ],
        ],
        "isValid": True
    }
    re = requests.post(base_url + 'plans', json=data, headers=username_header(sample_user))
    assert re.status_code == 201

    re = requests.post(base_url + 'incidents', json={
        'plan': sample_user + '-test-comment-post',
        'context': {},
    }, headers={'Authorization': 'hmac %s:abc' % sample_application_name})
    incident_id = int(re.content)
    assert re.status_code == 201
    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200

    # Post a few comments for the incident
    re = requests.post(base_url + 'incidents/%s/comments' % incident_id, headers=username_header(sample_user), json={
        'author': sample_user,
        'content': 'Hello world'
    })
    assert re.status_code == 201
    re = requests.post(base_url + 'incidents/%s/comments' % incident_id, headers=username_header(sample_user), json={
        'author': sample_user,
        'content': 'Goodbye world'
    })
    assert re.status_code == 201
    # Get incident info and verify comments
    re = requests.get(base_url + 'incidents/%s' % incident_id)
    assert re.status_code == 200
    comments = re.json()['comments']
    assert comments[0]['content'] == 'Hello world'
    assert comments[0]['author'] == sample_user
    assert comments[1]['content'] == 'Goodbye world'
    assert comments[1]['author'] == sample_user


def clean_categories(app, admin):
    # Helper to clean up categories before creating them
    re = requests.post(base_url + 'categories/%s' % app, json=[], headers=username_header(admin))
    assert re.status_code == 200


def test_category(sample_application_name, sample_admin_user, sample_user):
    category_name = 'test_category'
    clean_categories(sample_application_name, sample_admin_user)
    # Test creating category
    re = requests.post(
        base_url + 'categories/%s' % sample_application_name,
        json=[{
            'name': category_name,
            'description': 'barfoo',
            'mode': 'slack'
        }],
        headers=username_header(sample_admin_user))
    assert re.status_code == 200
    # Make sure the category exists and test GET
    re = requests.get(base_url + 'categories/' + sample_application_name)
    assert re.status_code == 200
    categories = re.json()
    assert any(c['name'] == category_name for c in categories)

    # Check that app ownership is required for category creation
    re = requests.post(
        base_url + 'categories/%s' % sample_application_name,
        json=[{
            'name': category_name,
            'description': 'barfoo',
            'mode': 'slack'
        }])
    assert re.status_code == 401

    # Test name filters with GET
    re = requests.get(base_url + 'categories/%s?name__startswith=%s' % (sample_application_name, category_name))
    assert re.status_code == 200
    categories = re.json()
    assert any(c['name'] == category_name for c in categories)

    # Test GET with application specified
    re = requests.get(base_url + 'categories/%s' % sample_application_name)
    assert re.status_code == 200
    categories = re.json()
    assert any(c['name'] == category_name for c in categories)

    # Test edit category
    re = requests.post(
        base_url + 'categories/%s' % sample_application_name,
        json=[{
            'name': category_name,
            'description': 'barfoo',
            'mode': 'slack'
        }],
        headers=username_header(sample_admin_user))
    assert re.status_code == 200
    re = requests.get(base_url + 'categories/%s' % sample_application_name)
    data = re.json()[0]
    assert data['description'] == 'barfoo'
    assert data['mode'] == 'slack'

    # Test delete
    re = requests.post(
        base_url + 'categories/%s' % sample_application_name,
        json=[],
        headers=username_header(sample_admin_user))
    assert re.status_code == 200
    re = requests.get(base_url + 'categories/%s' % sample_application_name)
    assert len(re.json()) == 0


def test_category_override(sample_application_name, sample_application_name2, sample_user, sample_user2, sample_admin_user):
    category_name = 'test_category'
    category_name_2 = 'test_category_2'
    clean_categories(sample_application_name, sample_admin_user)

    category_data = [
        {
            'name': category_name,
            'description': 'foobar',
            'mode': 'email'
        },
        {
            'name': category_name_2,
            'description': 'foobar',
            'mode': 'email'
        }
    ]

    # Set up categories
    re = requests.post(
        base_url + 'categories/' + sample_application_name,
        json=category_data,
        headers=username_header(sample_admin_user))
    assert re.status_code == 200

    # Test create overrides
    re = requests.post(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user),
        json={
            category_name: 'slack'
        })
    assert re.status_code == 201

    # Test GET and make sure POST worked properly
    re = requests.get(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user))
    assert re.status_code == 200
    data = re.json()
    assert len(data) == 1
    assert data[0]['category'] == category_name
    assert data[0]['application'] == sample_application_name
    assert data[0]['mode'] == 'slack'

    # Add another override
    re = requests.post(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user),
        json={
            category_name_2: 'slack'
        })
    assert re.status_code == 201
    # Makes sure we get both
    re = requests.get(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user))
    assert re.status_code == 200
    data = re.json()
    assert len(data) == 2

    # Remove an override via POST
    re = requests.post(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user),
        json={
            category_name_2: None
        })
    assert re.status_code == 201
    re = requests.get(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user))
    assert re.status_code == 200
    data = re.json()
    assert len(data) == 1

    # Remove all overrides via DELETE
    re = requests.delete(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user))
    assert re.status_code == 204
    re = requests.get(
        base_url + 'users/%s/categories/%s' % (sample_user, sample_application_name),
        headers=username_header(sample_user))
    assert re.status_code == 200
    data = re.json()
    assert len(data) == 0

    # Clean up categories
    re = requests.post(
        base_url + 'categories/%s' % sample_application_name,
        json=[],
        headers=username_header(sample_admin_user))
    assert re.status_code == 200


def test_post_category_notification(sample_application_name, sample_user, sample_admin_user):
    # The iris-api in this case will send a request to iris-sender's
    # rpc endpoint. Don't bother if sender isn't working.
    try:
        sock = socket.socket()
        sock.connect(sender_address)
        sock.close()
    except socket.error:
        pytest.skip('Skipping this test as sender is not running/reachable.')

    category_name = 'test_category'
    clean_categories(sample_application_name, sample_admin_user)
    # Set up category
    re = requests.post(
        base_url + 'categories/%s' % sample_application_name,
        json=[{
            'name': category_name,
            'description': 'barfoo',
            'mode': 'slack'
        }],
        headers=username_header(sample_admin_user))
    assert re.status_code == 200

    re = requests.post(base_url + 'notifications', json={
        'role': 'user',
        'target': sample_user,
        'subject': 'test',
        'category': category_name,
        'body': '',
    }, headers={'authorization': 'hmac %s:boop' % sample_application_name})
    assert re.status_code == 200
    assert re.text == '[]'
    clean_categories(sample_application_name, sample_admin_user)


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
            cursor.execute("INSERT INTO plan_notification(id, plan_id, step, template_id, target_id, role_id, priority_id, `optional`)"
                           "VALUES (1, 2, 1, 1, 8, 8, 8, 0)")
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
        result = runner.invoke(iris_ctl.template,
                               ['delete', 'foobar', '--config=../configs/config.dev.yaml'],
                               input='y\n')
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
            cursor.execute("INSERT INTO plan_notification(id, plan_id, step, template_id, target_id, role_id, priority_id, `optional`)"
                           "VALUES (1, 29, 1, 1, 8, 8, 8, 0)")
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
