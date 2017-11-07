from iris.vendors import IrisVendorManager


def test_send_through_dummy():
    vendor_manager = IrisVendorManager([{'type': 'iris_dummy'}], ['dummy_app'])
    assert vendor_manager.send_message({'mode': 'call'}) == 1
    assert vendor_manager.send_message({'application': 'dummy app', 'mode': 'call'}) == 2
