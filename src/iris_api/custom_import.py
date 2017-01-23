from importlib import import_module


def import_custom_module(default_root, module):
    if '.' in module:
        module_path = module
        module = module.split('.')[-1]
    else:
        module_path = default_root + '.' + module
    return getattr(import_module(module_path), module)
