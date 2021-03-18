import logging

logger = logging.getLogger(__name__)


class IncidentHandler:
    def __init__(self, config):
        pass

    def process(self, incident):
        logger.debug('Dummy custom handler code executed')
        return
