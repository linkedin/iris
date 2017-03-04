# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.


def test_twilio_message_generate(mocker):
    mocker.patch('twilio.rest.resources.Connection')
    from iris_api.vendors.iris_twilio import iris_twilio
    twilio = iris_twilio({})
    assert twilio.generate_message_text({}) == ''
    assert twilio.generate_message_text({'subject': '', 'body': ''}) == ''
    assert twilio.generate_message_text({'subject': 'Foo', 'body': 'Bar'}) == 'Foo. Bar'
    assert twilio.generate_message_text({'body': 'FooBar'}) == 'FooBar'
    assert twilio.generate_message_text({'subject': 'FooBar'}) == 'FooBar'
