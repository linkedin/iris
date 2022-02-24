import logging
import importlib

logger = logging.getLogger(__name__)


class CustomIncidentHandlerDispatcher:
    """ Dispatch requests to multiple incident handlers """

    def __init__(self, config):
        """ Load all handlers from config """
        self.config = config
        self.handlers = []
        module_path = config.get('custom_incident_handler_module')
        if module_path:
            self._load_module(module_path)

        module_paths = config.get('custom_incident_handler_modules')
        if module_paths:
            for module_path in module_paths:
                self._load_module(module_path)

    def _load_module(self, module_path):
        """ Load a handler based on its module path from config """
        module = importlib.import_module(module_path)
        instance = getattr(module, 'IncidentHandler')(self.config)
        self.handlers.append(instance)

    def process_create(self, incident):
        """ Call all handlers upon incident creation """
        for handler in self.handlers:
            handler.process_create(incident)

    def process_claim(self, incident):
        """ Call all handlers upon incident claim """
        for handler in self.handlers:
            handler.process_claim(incident)

    def process_resolve(self, incident):
        """ Call all handlers upon incident resolve """
        for handler in self.handlers:
            handler.process_resolve(incident)


class IncidentHandler:
    """ Dummy custom incident handler """
    def __init__(self, config):
        pass

    def process_create(self, incident):
        logger.info('Dummy custom handler code for creation executed %s', incident)
        return

    def process_claim(self, incident):
        logger.info('Dummy custom handler code for claim executed %s', incident)
        return

    def process_resolve(self, incident):
        logger.info('Dummy custom handler code for resolve executed %s', incident)
        return
