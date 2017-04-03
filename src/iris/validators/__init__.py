# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from iris.custom_import import import_custom_module

_registered_validators = []


def init_validators(validators):
    for module in validators:
        _registered_validators.append(import_custom_module('iris.validators', module)())


class IrisValidationException(Exception):
    pass


def run_validation(item, *args, **kwargs):
    for validator in _registered_validators:
        try:
            getattr(validator, 'validate_' + item)(*args, **kwargs)
        except RuntimeError as e:
            raise IrisValidationException(e)
