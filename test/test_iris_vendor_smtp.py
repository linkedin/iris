#!/usr/bin/env python
# -*- coding:utf-8 -*-


def test_smtp_vendor_init():
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'foo'
    }
    smtp_vendor = iris_smtp(smtp_config)
    assert smtp_vendor.smtp_timeout == 10
    assert smtp_vendor.mx_sorted == [(0, 'foo')]

    smtp_config = {
        'timeout': 20,
        'smtp_server': 'foo'
    }
    smtp_vendor = iris_smtp(smtp_config)
    assert smtp_vendor.smtp_timeout == 20


def test_smtp_send_email(mocker):
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'foo',
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    mocked_SMPT = mocker.patch('iris.vendors.iris_smtp.SMTP')
    smtp_vendor.send_email({
        'destination': 'foo@bar',
        'subject': 'hello',
        'body': 'world',
    })
    mocked_SMPT.assert_called_once_with(timeout=10)

    class CheckEmailString(str):
        def __eq__(self, other):
            return 'hello' in other and 'world' in other

    mocked_SMPT.return_value.sendmail.assert_called_once_with(
        ['iris@bar'],
        ['foo@bar'],
        CheckEmailString())
    smtp_vendor.cleanup()
    mocked_SMPT.return_value.quit.assert_called_once_with()


def test_smtp_unicode(mocker):
    from iris.vendors.iris_smtp import iris_smtp
    smtp_config = {
        'smtp_server': 'foo',
        'from': 'iris@bar',
    }
    smtp_vendor = iris_smtp(smtp_config)
    mocker.patch('iris.vendors.iris_smtp.SMTP')
    smtp_vendor.send_email({
        'destination': 'foo@bar',
        'subject': 'hello',
        'body': '\u201c',
    })
