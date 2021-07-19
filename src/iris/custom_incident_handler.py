import logging

logger = logging.getLogger(__name__)


class IncidentHandler:
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
