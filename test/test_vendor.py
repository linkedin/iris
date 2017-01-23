from iris_api.vendors import init_vendors, send_message


def test_send_through_dummy():
    init_vendors([{'type': 'iris_dummy'}], ['dummy_app'])
    assert send_message({'mode': 'call'}) == 1
    assert send_message({'application': 'dummy app', 'mode': 'call'}) == 2
