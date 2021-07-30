# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.


def test_twilio_message_generate(mocker):
    from iris.vendors.iris_twilio import iris_twilio
    twilio = iris_twilio({})
    assert twilio.generate_message_text({}) == ''
    assert twilio.generate_message_text({'subject': '', 'body': ''}) == ''
    assert twilio.generate_message_text({'subject': 'Foo', 'body': 'Bar'}) == 'Foo. Bar'
    assert twilio.generate_message_text({'body': 'FooBar'}) == 'FooBar'
    assert twilio.generate_message_text({'subject': 'FooBar'}) == 'FooBar'


def test_twilio_notification_call_generate(mocker):
    mocker.patch('iris.vendors.iris_twilio.find_plugin')
    from iris.vendors.iris_twilio import iris_twilio
    relay_base_url = 'http://foo/relay'
    fake_from_num = '123-123-1234'
    fake_to_num = '123-123-1235'

    twilio = iris_twilio({
        'twilio_number': fake_from_num,
        'relay_base_url': relay_base_url
    })
    mock_twilio_client = mocker.MagicMock()
    mocker.patch.object(twilio, 'get_twilio_client').return_value = mock_twilio_client
    twilio.send_call({
        'destination': fake_to_num,
        'application': 'iris-sender',
        'subject': 'Hello',
        'body': 'World',
    })
    mock_twilio_client.calls.create.assert_called_once_with(
        to=fake_to_num,
        from_=fake_from_num,
        if_machine='Continue',
        url=relay_base_url + (
            '/api/v0/twilio/calls/say?content=Hello.+World&'
            'loop=3&source=iris-sender'),
        status_callback=relay_base_url + '/api/v0/twilio/status'
    )


def test_twilio_notification_call_generate_override(mocker):
    mocker.patch('iris.vendors.iris_twilio.find_plugin')
    from iris.vendors.iris_twilio import iris_twilio
    relay_base_url = 'http://foo/relay'
    fake_from_num = '123-123-1234'
    fake_to_num = '123-123-1235'
    override_num = '777-777-7777'

    twilio = iris_twilio({
        'twilio_number': fake_from_num,
        'relay_base_url': relay_base_url,
        'application_override_mapping': {'iris-sender': override_num}
    })
    mock_twilio_client = mocker.MagicMock()
    mocker.patch.object(twilio, 'get_twilio_client').return_value = mock_twilio_client
    twilio.send_call({
        'destination': fake_to_num,
        'application': 'iris-sender',
        'subject': 'Hello',
        'body': 'World',
    })
    mock_twilio_client.calls.create.assert_called_once_with(
        to=fake_to_num,
        from_=override_num,
        if_machine='Continue',
        url=relay_base_url + (
            '/api/v0/twilio/calls/say?content=Hello.+World&'
            'loop=3&source=iris-sender'),
        status_callback=relay_base_url + '/api/v0/twilio/status'
    )


def test_twilio_incident_call_generate(mocker):
    mock_plugin = mocker.MagicMock()
    mock_plugin.get_phone_menu_text.return_value = 'Press 1 to pay'
    mocker.patch('iris.vendors.iris_twilio.find_plugin').return_value = mock_plugin
    relay_base_url = 'http://foo/relay'
    fake_from_num = '123-123-1234'
    fake_to_num = '123-123-1235'

    from iris.vendors.iris_twilio import iris_twilio
    twilio = iris_twilio({
        'twilio_number': fake_from_num,
        'relay_base_url': relay_base_url
    })
    mock_twilio_client = mocker.MagicMock()
    mocker.patch.object(twilio, 'get_twilio_client').return_value = mock_twilio_client
    mocker.patch.object(twilio, 'initialize_twilio_message_status')

    twilio.send_call({
        'message_id': 1,
        'destination': fake_to_num,
        'application': 'iris-sender',
        'subject': 'Hello',
        'body': 'World',
    })
    mock_twilio_client.calls.create.assert_called_once_with(
        to=fake_to_num,
        from_=fake_from_num,
        if_machine='Continue',
        url=relay_base_url + (
            '/api/v0/twilio/calls/gather?content=Hello.+World&'
            'loop=3&source=iris-sender&'
            'message_id=1&instruction=Press+1+to+pay'),
        status_callback=relay_base_url + '/api/v0/twilio/status'
    )
