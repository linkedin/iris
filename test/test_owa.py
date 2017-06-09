from iris.bin.owasync import is_pointless_message


def test_is_pointless_message():
    bad_message_headers = [{
        'name': 'X-Autoreply',
        'value': 'yes'
    }]

    bad_message2_headers = [
        {
            'name': 'Auto-Submitted',
            'value': 'auto-replied'
        },
        {
            'name': 'Precedence',
            'value': 'bulk'
        }
    ]

    good_message_headers = [{
        'name': 'From',
        'value': 'Foo Bar <foo@bar.com>'
    }]

    assert is_pointless_message(bad_message_headers)
    assert is_pointless_message(bad_message2_headers)
    assert not is_pointless_message(good_message_headers)
